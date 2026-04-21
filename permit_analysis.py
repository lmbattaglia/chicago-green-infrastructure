#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 17:43:40 2026

@author: loganbattaglia
"""

# Import needed modules

import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams["figure.dpi"] = 300

# Read permits dataset in

permits = pd.read_csv("chicago_building_permits.csv")

# Explore permit types 

permits["work_type"].value_counts(dropna=False)
permits["permit_type"].value_counts(dropna=False)

# Add columns for issue year, month, day

permits["issue_year"]  = permits["issue_date"].str[:4]
permits["issue_month"]  = permits["issue_date"].str[5:7]
permits["issue_day"]  = permits["issue_date"].str[8:10]

permits["issue_year"].value_counts(dropna=False)

# Separate solar projects 

solar_permits = permits[permits["work_type"] == "Small-Scale Solar PV System"]
solar_permits["issue_year"].value_counts(dropna=False)

# Data is only for 2023-2026, so want to try something else to search for solar projects...
# Identify work descriptions that contain the word "solar"

permits["is_solar"] = permits["work_description"].str.contains("solar", case=False, na=False).astype(int)
permits["is_solar"].value_counts()

# Create separate dataframe with these permits 

is_solar_permits = permits[permits["is_solar"] == 1]
is_solar_permits["issue_year"].value_counts()

# First get value counts then sort by year
is_solar_year_counts = is_solar_permits["issue_year"].value_counts().sort_index()

# Create graph
is_solar_year_counts.plot(kind='bar', figsize=(12, 5), color='green', width=0.9)
plt.title('Solar Permits by Year')
plt.xlabel('Year')
plt.ylabel('Number of Permits Issued')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("solar_permits_by_year.png")
