import os
import numpy as np
import io
from time import sleep
import pandas as pd
import shopify
from orbea_stock import OrbeaStock

script_dir = os.path.dirname(os.path.realpath(__file__))
shopify_api_version = "2022-10"
epos_file = f"{script_dir}/epos.xlsx"

# Products to load
families = [
    "Alma",
]

# Optional: only load a single model 
filter_model = "ALMA H30"

# Check if all required environments variables are set
required_envs = [
    "ORBEA_EMAIL",
    "ORBEA_PASSWORD",
    "SHOPIFY_API_SECRET",
    "SHOPIFY_SHOP_URL"
]

for required_env in required_envs:
    if required_env not in os.environ:
        raise Exception(f"Environment variable {required_env} is not set")

# Load Epos
df = pd.read_excel(io=epos_file, index_col=0, dtype=str)
df = df[df["Family"].isin(families)]

# Optional: only load a single model
if filter_model:
    df = df[df["Model"] == filter_model]

# Download and load Orbea stock
orbea_stock = OrbeaStock(os.getenv("ORBEA_EMAIL"), os.getenv("ORBEA_PASSWORD"))
orbea_stock.login()
stock_download = orbea_stock.download()
df_orbea_stock = pd.read_csv(filepath_or_buffer=io.StringIO(stock_download.decode('utf-8')), dtype=str, sep=";")
df_orbea_stock.drop(columns=["Description", "Color", "Wheel Size"], axis=1, inplace=True)
df_orbea_stock.rename(columns={"Item": "TTCC"}, inplace=True)
df_orbea_stock.rename(columns={"Color Code": "Colour Code"}, inplace=True)

# Extend epos with df_orbea_stock
df = df.merge(df_orbea_stock, how="left", on=["TTCC", "Size", "Colour Code"])
df.replace(np.nan, "", inplace=True)

# Create int from Units available
df["Units available"] = df["Units available"].str.replace("+", "")
df["Units available"] = df["Units available"].replace("", "0")
df["Units available"] = df["Units available"].astype(int)

unique_model_ids = df["Model ID"].unique()

with shopify.Session.temp(os.getenv("SHOPIFY_SHOP_URL"), shopify_api_version, os.getenv("SHOPIFY_API_SECRET")):
    for i, unique_model_id in enumerate(unique_model_ids):
        print(f"Product {i+1} of {len(unique_model_ids)}")
        df_variants = df[df["Model ID"] == unique_model_id]

        # Get attributes from 1st record, but skip color Myo because it never has an image
        first_record = df_variants[df_variants["Orbea Colour (EN)"] != "Myo"].iloc[0]

        title = f"Orbea {first_record['Model']} {first_record['M']}"

        # Skip products without image - they are not for sale yet
        if not first_record["Image_Url"]:
            print(f"Skipping {title}. No image")
            continue

        find_product = shopify.Product.find(title=title)

        # Overwrite product by what's in Shopify when it exists. Exit when multiple products are found
        if find_product:
            if len(find_product) == 1:
                product = find_product[0]
            else:
                raise Exception(f"Multiple products found for {title}")
        else:
            print(f"Skipping {title}. Doesn't exist in Shopify")
            continue

        for variant in product.variants:
            df_variant = df_variants[
                (df_variants["Size"] == variant.attributes['option1']) &
                (df_variants["Summarised Colour (EN)"] == variant.attributes['option2'])
            ].iloc[0]

            if df_variant["Units available"] > 0 or df_variant["Orbea Colour (EN)"] == "Myo":
                inventory_policy = "continue"
            else:
                inventory_policy = "deny"

            variant.attributes["inventory_policy"] = inventory_policy

        product.save()

        # Sleep to prevent rate limit
        sleep(1)
