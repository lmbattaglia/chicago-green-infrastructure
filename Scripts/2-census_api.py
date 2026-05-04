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
    'B19301_001E': 'per_capita_income',
    'B17001_002E': 'population_below_poverty',
    'B17001_001E': 'poverty_universe',
    'B25077_001E': 'median_property_value',
    'B25064_001E': 'median_gross_rent',
    'B23025_005E': 'unemployed',
    'B23025_002E': 'labor_force',
    'B01003_001E': 'total_population',
    'B02001_002E': 'pop_white_alone',
    'B02001_003E': 'pop_black_alone',
    'B02001_004E': 'pop_aian_alone',         
    'B02001_005E': 'pop_asian_alone',
    'B02001_006E': 'pop_nhpi_alone',       
    'B02001_007E': 'pop_other_alone',
    'B02001_008E': 'pop_two_or_more_races',
    'B03003_003E': 'pop_hispanic_latino',    
    'B15003_001E': 'education_universe',    
    'B15003_017E': 'edu_high_school_diploma',
    'B15003_018E': 'edu_ged',
    'B15003_019E': 'edu_some_college_lt1yr',
    'B15003_020E': 'edu_some_college_gt1yr',
    'B15003_021E': 'edu_associates',
    'B15003_022E': 'edu_bachelors',
    'B15003_023E': 'edu_masters',
    'B15003_024E': 'edu_professional',
    'B15003_025E': 'edu_doctorate',
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

# Build GEOID for joining to other datasets

cook_demo["GEOID"] = cook_demo["state"] + cook_demo["county"] + cook_demo["tract"]

# Rename variables to nicer names

cook_demo = cook_demo.rename(columns=variables)

# Convert numeric columns from strings to numbers 
numeric_cols = list(variables.values())
cook_demo[numeric_cols] = cook_demo[numeric_cols].apply(pd.to_numeric, errors='coerce')

# Derive useful rate columns

# Poverty and unemployment rates 

cook_demo["poverty_rate"] = cook_demo["population_below_poverty"] / cook_demo["poverty_universe"]
cook_demo["unemployment_rate"] = cook_demo["unemployed"] / cook_demo["labor_force"]

# Race shares

cook_demo['pct_white']    = cook_demo['pop_white_alone']    / cook_demo['total_population']
cook_demo['pct_black']    = cook_demo['pop_black_alone']    / cook_demo['total_population']
cook_demo['pct_asian']    = cook_demo['pop_asian_alone']    / cook_demo['total_population']
cook_demo['pct_hispanic'] = cook_demo['pop_hispanic_latino']/ cook_demo['total_population']

# Educational attainment (Percent of pop 25+ with a bachelor's or higher)

cook_demo['pct_bachelors_plus'] = (
    cook_demo['edu_bachelors'] +
    cook_demo['edu_masters']   +
    cook_demo['edu_professional'] +
    cook_demo['edu_doctorate']
) / cook_demo['education_universe']

# Percent with less than high school

cook_demo['pct_no_hs'] = 1 - (
    cook_demo[['edu_high_school_diploma','edu_ged','edu_some_college_lt1yr',
               'edu_some_college_gt1yr','edu_associates','edu_bachelors',
               'edu_masters','edu_professional','edu_doctorate']].sum(axis=1)
    / cook_demo['education_universe']
)

# Set index of df to be names, write out to CSV file

cook_demo.setindex = cook_demo["NAME"]
cook_demo.to_csv('Data/Census Data/chicago_census_data.csv',index=False)





