from stockfetcher.logging_setup import setup_logging
import sys
import os
from time import sleep
import pandas as pd
import numpy as np
import shopify
from stockfetcher.orbea_stock import OrbeaStock
from stockfetcher.config import AppConfig, EposConfig
from app_secrets import ftp_secrets, shopify_secret, notification_secret
from stockfetcher.notification import Notification
import click
from stockfetcher.epos import Epos


@click.command()
@click.option(
    "--notify-error",
    is_flag=True,
    help="Send a notification alert when the app fails",
)
@click.option(
    "--notify-success",
    is_flag=True,
    help="Send a notification when the app succeeds",
)
@click.option(
    "--filter-single-model",
    required=False,
    help="Only load a single model for quick testing",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Don't touch Shopify but print statements",
)
def main(
    notify_error: bool, notify_success: bool, filter_single_model: str, dry_run: bool
):
    # @TODO use @catch something for try except
    try:
        logger = setup_logging()

        logger.info(f"Starting app")

        app_config = AppConfig()
        epos_config = EposConfig(filter_single_model=filter_single_model)

        # Load epos
        df = Epos(epos_config=epos_config).df

        # Download and load Orbea stock
        df_orbea_stock = OrbeaStock.download(secrets=ftp_secrets)

        # Extend epos with df_orbea_stock
        df = df.merge(df_orbea_stock, how="left", on=["EAN"])
        df["Available"].replace(np.nan, 0, inplace=True)

        unique_model_ids = df["Model"].unique()

        logger.info(f"Processing {len(unique_model_ids)} products")
        errors = 0
        with shopify.Session.temp(
            shopify_secret.shop_url,
            app_config.shopify_api_version,
            shopify_secret.api_secret,
        ):
            for i, unique_model_id in enumerate(unique_model_ids):
                df_variants = df[df["Model"] == unique_model_id]

                # Get attributes from 1st record
                first_record = df_variants.iloc[0]

                title = f"Orbea {first_record['Model']} {first_record['Year']}"

                logger.info(f"Product {i+1} of {len(unique_model_ids)} - {title}")

                find_product = shopify.Product.find(title=title)

                # Overwrite product by what's in Shopify when it exists. Exit when multiple products are found
                if find_product:
                    if len(find_product) == 1:
                        product = find_product[0]
                    else:
                        raise Exception(f"Multiple products found for {title}")
                else:
                    logger.info(f"Skipping {title}. Doesn't exist in Shopify")
                    # Sleep to avoid rate limiting
                    sleep(0.5)
                    continue

                for variant in product.variants:
                    try:
                        df_variant = df_variants[
                            (df_variants["Size"] == variant.attributes["option1"])
                            & (
                                df_variants["Summarised Colour (EN)"]
                                == variant.attributes["option2"]
                            )
                        ].iloc[0]
                    except:
                        errors += 1
                        logger.error(f"Mismatching color for {title}")
                        logger.error(f"Shopify color: {variant.option2}")

                        df_stock_colors = df_variants["Summarised Colour (EN)"].unique()
                        stock_colors_str = ", ".join(map(str, df_stock_colors))
                        logger.error(f"Stock colors: {stock_colors_str}")

                    if df_variant["Available"] > 0:
                        inventory_policy = "continue"
                    else:
                        inventory_policy = "deny"

                    variant.attributes["inventory_policy"] = inventory_policy

                try:
                    if dry_run:
                        logger.info("Dry run: would've saved product")
                    else:
                        product.save()
                except Exception as e:
                    logger.warning("Error saving product, retrying after 1s")
                    logger.warning(e)
                    sleep(0.5)
                    if dry_run:
                        logger.info("Dry run: would've saved product")
                    else:
                        product.save()

                # Sleep to avoid rate limiting
                if dry_run:
                    logger.info("Dry run: would've slept")
                else:
                    sleep(0.5)

        if errors > 0:
            logger.error(f"{errors} errors occurred. Please check log above")
            sys.exit(1)
        else:
            logger.info("Finished successfully")

        if notify_success:
            Notification.send(secret=notification_secret, status="success")
    except Exception as e:
        if notify_error:
            Notification.send(secret=notification_secret, status="error")
        raise


if __name__ == "__main__":
    main()
