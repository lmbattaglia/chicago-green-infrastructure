#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 21:58:03 2026

@author: loganbattaglia
"""

# Get demographic data from Census API 

# Import needed modules 

import pandas as pd
import requests

# Define variables to pull
# Full variable list: https://api.census.gov/data/2024/acs/acs5/variables.html

variables = {
    'B19013_001E': 'median_household_income',
    'B25077_001E': 'median_property_value',
    'B17001_002E': 'population_below_poverty',
    'B01003_001E': 'total_population',
    'B17001_001E': 'poverty_universe',
    'B19301_001E': 'per_capita_income',
    'B25064_001E': 'median_gross_rent',
    'B23025_005E': 'unemployed',
    'B23025_002E': 'labor_force',
    'B15003_022E': 'bachelors_degree',
    'B15003_001E': 'education_universe',
}

var_string = 'NAME,' + ','.join(variables.keys())

# Read API key into a variable

with open('apikey.txt') as fh:
    apikey = fh.readline().strip()
    
# Set api variable to ACS 2024 5 Year API

api = 'https://api.census.gov/data/2024/acs/acs5'

# Indicate that census tracts in Cook County, IL

for_clause = 'tract:*'
in_clause = 'state:17 county:031'

# Set payload and response values, collect response

payload = {'get':var_string,'for':for_clause,'in':in_clause,'key':apikey}
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
cook_demo = pd.DataFrame(columns=colnames,data=datarows)

# Rename variables to nicer names

cook_demo = cook_demo.rename(columns=variables)

# Build GEOID for joining to other datasets

cook_demo["GEOID"] = cook_demo["state"] + cook_demo["county"] + cook_demo["tract"]

# Convert numeric columns from strings to numbers 
numeric_cols = list(variables.values())
cook_demo[numeric_cols] = cook_demo[numeric_cols].apply(pd.to_numeric, errors='coerce')

# ── Derive useful rate columns ────────────────────────────────────────────────
cook_demo["poverty_rate"] = cook_demo["population_below_poverty"] / cook_demo["poverty_universe"]
cook_demo["unemployment_rate"] = cook_demo["unemployed"] / cook_demo["labor_force"]
cook_demo["pct_bachelors"] = cook_demo["bachelors_degree"] / cook_demo["education_universe"]

# Set index of df to be names, write out to CSV file

cook_demo.setindex = cook_demo["NAME"]
cook_demo.to_csv('chicago_census_data.csv',index=False)





