#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 18:20:06 2026

@author: loganbattaglia
"""

# Get building permit data from Chicago API 

# Using links https://data.cityofchicago.org/resource/ydr8-5enu.csv
# Code from this resource: https://dev.socrata.com/foundry/data.cityofchicago.org/ydr8-5enu

# Import needed modules 

import pandas as pd
from sodapy import Socrata
import requests
import time

# Identify desired variables

variables = [
    "id",
    "permit_",
    "permit_type",
    "application_start_date",
    "issue_date",
    "street_number",
    "street_name",
    "work_type",
    "work_description",
    "subtotal_waived",
    "total_fee",
    "census_tract",
    "ward",
    "xcoordinate",
    "ycoordinate"
    ]

# Identify dataset id 

dataset_id = "ydr8-5enu"

# Read app token (from City of Chicago website) with username and password into file

    
with open('apptoken.txt') as fh:
    apptoken = fh.readline().strip()
    
with open('username.txt') as fh:
    username = fh.readline().strip()  

with open('password.txt') as fh:
    password = fh.readline().strip()

# Use city resource example authenticated client (needed for non-public datasets) to pull this dataset

client = Socrata("data.cityofchicago.org",
                  apptoken,
                  username=username,
                  password=password,
                  timeout=120)

# Specify batch size of 50,000 and use offset to pull multiple batches

batch_size = 50000
all_records = []
offset = 0

# Indicate that download is beginning

print("Starting download...")

# Define data collection function with correct dataset endpoint

while True:
    batch = client.get(
        dataset_id,
        select=",".join(variables),
        limit=batch_size,
        offset=offset,
        order="id"
    )

    batch_size = len(batch)
    all_records.extend(batch)
    print(f"  Fetched {len(all_records):,} records so far (batch: {batch_size})")

# Specify endpoint in data collection when batch size = 0

    if batch_size == 0:
        break  

# Give time for the API to rest between pulls 

    offset += batch_size
    time.sleep(0.5)

# Save as dataframe

df = pd.DataFrame.from_records(all_records)

# Drop nulls in work_description category 

df = df.dropna(subset=['work_description'])

df.to_csv("chicago_building_permits.csv", index=False)
print(f"\nDone! {len(df):,} total rows, {len(df.columns)} columns saved to chicago_building_permits.csv")
print(f"Columns: {list(df.columns)}")

# Get metadata for columns 

meta_url   = f"https://data.cityofchicago.org/api/views/{dataset_id}.json"

print("Fetching column metadata...")
meta      = requests.get(meta_url).json()
all_cols  = meta.get("columns", [])

# Build a lookup: fieldName → description

col_meta  = {
    c["fieldName"]: {
        "name":         c.get("name", ""),
        "dataTypeName": c.get("dataTypeName", ""),
        "description":  c.get("description", ""),
    }
    for c in all_cols
}

# Print column metadata

print(f"\n{'Field Name':<30} {'Type':<15} {'Label':<35} Description")
print("─" * 120)
for field in variables:
    info = col_meta.get(field, {})
    print(f"{field:<30} {info.get('dataTypeName',''):<15} {info.get('name',''):<35} {info.get('description','')}")
    
# Put column metadata into dataframe 

meta_rows = [
    {
        "fieldName":    field,
        "label":        col_meta.get(field, {}).get("name", ""),
        "dataTypeName": col_meta.get(field, {}).get("dataTypeName", ""),
        "description":  col_meta.get(field, {}).get("description", ""),
    }
    for field in variables
    if field in col_meta
]

pd.DataFrame(meta_rows).to_csv("chicago_building_permits_metadata.csv", index=False)





