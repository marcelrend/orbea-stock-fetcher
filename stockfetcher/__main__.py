import logging
import sys
import os
from time import sleep
import pandas as pd
import numpy as np
import shopify
from stockfetcher.orbea_stock import OrbeaStock
from app_secrets import ftp_secrets, shopify_secret, notification_secret
from stockfetcher.notification import Notification


def main():
    # Default logger for imported modules
    logging.basicConfig(
        level=logging.WARN,
        format="%(asctime)s:%(levelname)s:%(message)s",
        datefmt="%Y-%m-%d %I:%M:%S%p",
    )
    # Info logger for this module
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    shopify_api_version = "2022-10"

    dry_run = False

    families = [
        "Alma",
        "Avant",
        "Kemen",
        "Kemen Suv" "Laufey",
        "Occam",
        "Occam LT",
        "Occam SL",
        "Oiz",
        "Orca",
        "Orca Aero",
        "Ordu",
        "Rallon",
        "Rise",
        "Terra",
        "Urrun",
        "Wild",
    ]

    # Optional: only load a single model
    filter_model = ""

    # Exclude models, e.g if they are double
    skip_models = [
        {"model": "ORDU M30iLTD", "year": "2023"},
        {"model": "WILD M-TEAM", "year": "2024"},
        {"model": "WILD M-LTD", "year": "2024"},
        {"model": "TERRA M20iTEAM", "year": "2024"},
    ]

    # Load Epos
    epos_file = "epos_small_v2_23_24.xlsx"
    df = pd.read_excel(io=epos_file, index_col=0, dtype=str)

    df = df[df["Family"].isin(families)]

    # Optional: only load a single model
    if filter_model:
        df = df[df["Model"] == filter_model]

    # if skip_models is defined, remove those models if the model and year match
    if skip_models:
        for skip_model in skip_models:
            df = df[
                ~(
                    (df["Model"] == skip_model["model"])
                    & (df["Year"] == skip_model["year"])
                )
            ]

    # Remove >mph and OMRs (frame)
    for v in ["20mph", "28mph", " OMR", " OMX", "SPIRIT", "2POS FK"]:
        df = df[~df["Model"].str.contains(v)]

    # Convert double whitespace to single whitespace
    df["Summarised Colour (EN)"] = df["Summarised Colour (EN)"].str.replace(r"\s+", " ")

    # Download and load Orbea stock
    df_orbea_stock = OrbeaStock.download(secrets=ftp_secrets)

    # Extend epos with df_orbea_stock
    df = df.merge(df_orbea_stock, how="left", on=["EAN"])

    df["Available"].replace(np.nan, 0, inplace=True)

    unique_model_ids = df["Model"].unique()

    logger.info(f"Running app, processing {len(unique_model_ids)} products")

    errors = 0
    with shopify.Session.temp(
        shopify_secret.shop_url,
        shopify_api_version,
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


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        Notification.send(secret=notification_secret)
        raise
