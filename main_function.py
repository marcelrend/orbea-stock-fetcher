import logging
import sys
import os
import numpy as np
import io
from time import sleep
import pandas as pd
import shopify
from orbea_stock import OrbeaStock


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

    script_dir = os.path.dirname(os.path.realpath(__file__))
    shopify_api_version = "2022-10"

    families = [
        "Alma",
        "Avant",
        "Kemen",
        "Kemen Suv"
        "Laufey",
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

    # Check if all required environments variables are set
    required_envs = [
        "ORBEA_EMAIL",
        "ORBEA_PASSWORD",
        "SHOPIFY_API_SECRET",
        "SHOPIFY_SHOP_URL",
    ]

    for required_env in required_envs:
        if required_env not in os.environ:
            raise Exception(f"Environment variable {required_env} is not set")

    # Load Epos
    epos_file = f"{script_dir}/epos.xlsx"
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
    for v in ['20mph', '28mph', ' OMR', ' OMX', 'SPIRIT', '2POS FK']:
        df = df[~df['Model'].str.contains(v)]

    # Convert double whitespace to single whitespace
    df["Summarised Colour (EN)"] = df["Summarised Colour (EN)"].str.replace(r'\s+', ' ')

    # Download and load Orbea stock
    orbea_stock = OrbeaStock(os.getenv("ORBEA_EMAIL"), os.getenv("ORBEA_PASSWORD"))
    stock_download = orbea_stock.download()
    df_orbea_stock = pd.read_csv(
        filepath_or_buffer=io.StringIO(stock_download.decode("utf-8")),
        dtype=str,
        sep=";",
    )
    df_orbea_stock.drop(
        columns=["Description", "Color", "Wheel Size"], axis=1, inplace=True
    )
    df_orbea_stock.rename(columns={"Article": "TTCC"}, inplace=True)
    df_orbea_stock.rename(columns={"Color Code": "Colour Code"}, inplace=True)

    # Extend epos with df_orbea_stock
    df = df.merge(df_orbea_stock, how="left", on=["TTCC", "Size", "Colour Code"])
    df.replace(np.nan, "", inplace=True)

    # Create int from Units available
    df["Units available"] = df["Units available"].str.replace("+", "")
    df["Units available"] = df["Units available"].replace("", "0")
    df["Units available"] = df["Units available"].astype(int)

    unique_model_ids = df["Model ID"].unique()

    logger.info(f"Running app, processing {len(unique_model_ids)} products")

    errors = 0
    with shopify.Session.temp(
        os.getenv("SHOPIFY_SHOP_URL"),
        shopify_api_version,
        os.getenv("SHOPIFY_API_SECRET"),
    ):
        for i, unique_model_id in enumerate(unique_model_ids):
            df_variants = df[df["Model ID"] == unique_model_id]

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
                    stock_colors_str = ', '.join(map(str, df_stock_colors))
                    logger.error(f"Stock colors: {stock_colors_str}")


                if df_variant["Units available"] > 0:
                    inventory_policy = "continue"
                else:
                    inventory_policy = "deny"

                variant.attributes["inventory_policy"] = inventory_policy

            try:
                product.save()
            except Exception as e:
                logger.warning("Error saving product, retrying after 1s")
                logger.warning(e)
                sleep(1)
                product.save()

            # Sleep to avoid rate limiting
            sleep(0.5)

    if errors > 0:
        logger.error(f"{errors} errors occurred. Please check log above")
        sys.exit(1)
    else:
        logger.info("Finished successfully")


if __name__ == "__main__":
    main()
