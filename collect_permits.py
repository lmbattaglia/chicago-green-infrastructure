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
import time

# Identify desired variables

variables = "id,permit_,permit_type,application_start_date,issue_date,street_number,street_name,work_type,work_description,subtotal_waived,total_fee,census_tract,ward,xcoordinate,ycoordinate"

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
        "ydr8-5enu",
        select=variables,
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
df.to_csv("chicago_building_permits.csv", index=False)
print(f"\nDone! {len(df):,} total rows, {len(df.columns)} columns saved to chicago_building_permits.csv")
print(f"Columns: {list(df.columns)}")







