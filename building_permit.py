#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 18:20:06 2026

@author: loganbattaglia
"""

# Get building permit data from Chicago API, 

# Using links https://data.cityofchicago.org/resource/ydr8-5enu.csv
# Code from this resource: https://dev.socrata.com/foundry/data.cityofchicago.org/ydr8-5enu

# Import needed modules 

import pandas as pd
from sodapy import Socrata

# Unauthenticated client only works with public data sets. Note 'None'
# in place of application token, and no username or password:
client = Socrata("data.cityofchicago.org", None)

# Example authenticated client (needed for non-public datasets):
# client = Socrata(data.cityofchicago.org,
#                  MyAppToken,
#                  username="user@example.com",
#                  password="AFakePassword")

# First 2000 results, returned as JSON from API / converted to Python list of
# dictionaries by sodapy.
results = client.get("ydr8-5enu", limit=2000)

# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)




# Try class method from Census data

import pandas as pd
import requests

# Open API key

with open('apikey_secret.txt') as fh:
    apikey = fh.readline().strip()
    
# Set api variable to City of Chicago API

api = 'https://data.cityofchicago.org/api/v3/views/ydr8-5enu/query.csv'

# Define needed variables

variables = 'id,permit_,permit_type,street_number,street_name,work_type,work_description,subtotal_waived,total_fee,census_tract,ward,xcoordinate,ycoordinate'


# Set payload and response values, collect response

payload = {'get':variables,'key':apikey}
response = requests.get(api,payload)

# Test if response code succeeded

if response.status_code != 200:
    print(response.status_code)
    print(response.text)
    assert False

# Parse response to return list of rows 

row_list= response.json()

# Set columns and rows, convert to pandas df

colnames = row_list[0]
datarows = row_list[1:]
attain = pd.DataFrame(columns=colnames,data=datarows)

# Set index of df to be names, write out to CSV file

attain.setindex = attain["NAME"]
attain.to_csv('census-data.csv')

# Final try with just requests 

import requests
from requests.auth import HTTPBasicAuth

# Import api keys

with open('apikey_secret.txt') as fh:
    apikey_secret = fh.readline().strip()
    
with open('apikey_id.txt') as fh:
    apikey_id = fh.readline().strip()
    
with open('apptoken.txt') as fh:
    apptoken = fh.readline().strip()

response = requests.get(
    "https://data.cityofchicago.org/api/v3/views/ydr8-5enu/query.csv",
    headers={"X-App-Token": apptoken},
    auth=HTTPBasicAuth(apikey_id, apikey_secret),
    params=variables
)

print("Sending request...")

response = requests.get(
    "https://data.cityofchicago.org/api/v3/views/ydr8-5enu/query.csv",
    headers={"X-App-Token": apptoken},
    auth=HTTPBasicAuth(apikey_id, apikey_secret),
    params=variables
)

print(f"Done! Status code: {response.status_code}")
print(f"Response size: {len(response.content):,} bytes")


# Claude version 2

import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
import io
import time

variables = "id,permit_,permit_type,street_number,street_name,work_type,work_description,subtotal_waived,total_fee,census_tract,ward,xcoordinate,ycoordinate"

all_dfs = []
offset = 0
batch_size = 50000

print("Starting download...")

while True:
    variables = {
        "$select": variables,
        "$limit": batch_size,
        "$offset": offset,
        "$order": "id"
    }

    print(f"  Fetching rows {offset:,} to {offset + batch_size:,}...")

    response = requests.get(
        "https://data.cityofchicago.org/api/v3/views/ydr8-5enu/query.csv",
        headers={"X-App-Token": apptoken},
        auth=HTTPBasicAuth(apikey_id, apikey_secret),
        params=variables,
        timeout=60
    )

    if response.status_code != 200:
        print(response.status_code)
        print(response.text)
        break

    batch_df = pd.read_csv(io.StringIO(response.text))

    if len(batch_df) == 0:
        break

    all_dfs.append(batch_df)
    print(f"  Got {len(batch_df):,} rows (total so far: {sum(len(d) for d in all_dfs):,})")

    if len(batch_df) < batch_size:
        break  # Last partial page — done

    offset += batch_size
    time.sleep(0.5)

df = pd.concat(all_dfs, ignore_index=True)
df.to_csv("chicago_building_permits.csv", index=False)
print(f"\nDone! {len(df):,} total rows saved to chicago_building_permits.csv")