#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 16 17:43:40 2026

@author: loganbattaglia
"""

# Import needed modules

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import os

# Create folder for visualizations if it doesn't exist

os.makedirs("../Visualizations", exist_ok=True)

# Set default plot params

plt.rcParams["figure.dpi"] = 300

# Read permits dataset in

permits = pd.read_csv("../Data/Permit Data/chicago_building_permits.csv")

# Explore permit types 

permits["work_type"].value_counts(dropna=False)
permits["permit_type"].value_counts(dropna=False)

# Add columns for issue year, month, day

permits["issue_year"]  = permits["issue_date"].str[:4]
permits["issue_month"]  = permits["issue_date"].str[5:7]
permits["issue_day"]  = permits["issue_date"].str[8:10]

permits["issue_year"].value_counts(dropna=False)

permits.to_csv("../Data/Permit Data/chicago_building_permits.csv")

# Separate solar projects 

solar_permits = permits[permits["work_type"] == "Small-Scale Solar PV System"]
solar_permits["issue_year"].value_counts(dropna=False)

# Data is only for 2023-2026, so want to try something else to search for solar projects...
# Identify work descriptions that contain the word "solar" or work types that are Small-Scale Solar PV System

permits["is_solar"] = (
    permits["work_description"].str.contains("solar", case=False, na=False) |
    permits["work_type"].str.contains("solar", case=False, na=False)        
).astype(int)
permits["is_solar"].value_counts()

# Create separate dataframe with these permits 

is_solar_permits = permits[permits["is_solar"] == 1]
is_solar_permits["issue_year"].value_counts()

# First get value counts then sort by year (for stacked dataframe)

is_solar_year_counts = is_solar_permits["issue_year"].value_counts().sort_index()


# Search for permits with flood in description

# First make sure that key words are present in dataset

permits["work_description"].str.contains("flood", case=False, na=False).value_counts()
permits["work_description"].str.contains("rain", case=False, na=False).value_counts()
permits["work_description"].str.contains("stormwater", case=False, na=False).value_counts()
permits["work_description"].str.contains("storm water", case=False, na=False).value_counts()
permits["work_type"].str.contains("storm water", case=False, na=False).value_counts()

# Use key words to filter out flood mitigation related permits 

permits["is_flood"] = (
    permits["work_description"].str.contains("flood", case=False, na=False) |
    permits["work_description"].str.contains("rain", case=False, na=False) |
    permits["work_description"].str.contains("stormwater", case=False, na=False) |
    permits["work_description"].str.contains("storm water", case=False, na=False) |
    permits["work_type"].str.contains("storm water", case=False, na=False)
).astype(int)
permits["is_flood"].value_counts()

# Create separate dataframe with these permits

is_flood_permits = permits[permits["is_flood"] == 1]
is_flood_permits["issue_year"].value_counts()

# First get value counts then sort by year (for stacked dataframe)

is_flood_year_counts = is_flood_permits["issue_year"].value_counts().sort_index()


# Check for green infrastructure key words

permits["work_description"].str.contains("green roof", case=False, na=False).value_counts()
permits["work_description"].str.contains("plant", case=False, na=False).value_counts()
permits["work_description"].str.contains("planting", case=False, na=False).value_counts()
permits["work_description"].str.contains("tree", case=False, na=False).value_counts()

# Use key words to get green infrastructure

permits["is_green"] = (
    (
        permits["work_description"].str.contains("plant|planting|plants", case=False, na=False) &
        permits["work_description"].str.contains(r"\btree|trees\b", case=False, na=False)
    ) |
    permits["work_description"].str.contains("green roof", case=False, na=False) |
    permits["work_description"].str.contains("plant|planting|plants", case=False, na=False)
).astype(int)

permits["is_green"].value_counts()

# Create separate dataframe with these permits

is_green_permits = permits[permits["is_green"] == 1]
is_green_permits["issue_year"].value_counts()

# First get value counts then sort by year (for stacked dataframe)

is_green_year_counts = is_green_permits["issue_year"].value_counts().sort_index()


# Write function to plot individual bar graphs 

def plot_permit_trend(permit_flag, permits_df):
    config = {
        'is_solar': {
            'color':    'orange',
            'label':    'Solar',
            'title':    'Solar Permits by Year in Chicago (2006-2025)',
            'filename': 'solar_permits_by_year.png',
        },
        'is_flood': {
            'color':    'blue',
            'label':    'Flood Mitigation',
            'title':    'Flood Mitigation Permits by Year in Chicago (2006-2025)',
            'filename': 'flood_permits_by_year.png',
        },
        'is_green': {
            'color':    'green',
            'label':    'Green Infrastructure',
            'title':    'Green Infrastructure Permits by Year in Chicago (2006-2025)',
            'filename': 'green_permits_by_year.png',
        },
    }

    cfg = config[permit_flag]
    year_counts = (
        permits_df[permits_df[permit_flag] == 1]["issue_year"]
        .astype(int)
        .value_counts()
        .sort_index()
    )
    fig, ax = plt.subplots(figsize=(12, 5), dpi=150)

    year_counts.plot(
        kind='bar',
        color=cfg['color'],
        width=0.9,
        ax=ax,
        label=cfg['label']
    )
    x_numeric   = np.arange(len(year_counts))
    rolling_avg = year_counts.rolling(window=5, min_periods=1, center=False).mean()

    ax.plot(
        x_numeric,
        rolling_avg,
        color='black',
        linewidth=2,
        linestyle='--',
        label='5-Year Rolling Average'
    )
    for i, (year, count) in enumerate(year_counts.items()):
        ax.annotate(
            f"{int(count):,}",
            xy=(i, count),
            xytext=(0, 4),
            textcoords='offset points',
            ha='center',
            fontsize=7
        )
        
    if permit_flag == 'is_solar':
        years = list(year_counts.index)

        if 2016 in years:
            x_feja = years.index(2016) - 0.5
            ax.axvline(x=x_feja, color='black', linewidth=1.5, linestyle='--')
            ax.text(
                x_feja - 0.1,
                year_counts.max() * 0.98,
                'Future Energy\nJobs Act passed',
                ha='right', va='top',
                fontsize=8, color='black',
                style='italic'
            )

        if 2019 in years:
            x_isfa = years.index(2019) - 0.5
            ax.axvline(x=x_isfa, color='black', linewidth=1.5, linestyle='--')
            ax.text(
                x_isfa - 0.1,
                year_counts.max() * 0.98,
                'Illinois Solar for\nAll implemented',
                ha='right', va='top',
                fontsize=8, color='black',
                style='italic'
            )
    ax.set_ylim(0, year_counts.max() * 1.15) 
    ax.set_ylim(0, year_counts.max() * 1.05)
    ax.set_title(cfg['title'], fontsize=13, pad=12)
    ax.set_xlabel('Year', fontsize=10)
    ax.set_ylabel('Number of Permits Issued', fontsize=10)
    ax.tick_params(axis='x', rotation=45)
    ax.legend(fontsize=9)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))

    plt.tight_layout()
    plt.savefig(f"../Visualizations/{cfg['filename']}", dpi=150, bbox_inches='tight')
    plt.show()
    print(f"Saved: {cfg['filename']}")
       
# Call function for three datasets

plot_permit_trend('is_solar', permits)
plot_permit_trend('is_flood', permits)
plot_permit_trend('is_green', permits)

# Combine into a single dataframe, filling missing years with 0
stacked = pd.DataFrame({
    "Flood Mitigation":     is_flood_year_counts,
    "Green Infrastructure": is_green_year_counts,
    "Solar":                is_solar_year_counts,
}).fillna(0).astype(int)

stacked = stacked.sort_index()
stacked.index = stacked.index.astype(int)
stacked['total'] = stacked.sum(axis=1)

# Plot stacked bar chart
fig, ax = plt.subplots(figsize=(10, 7), dpi=150)
stacked.drop(columns='total').plot(
    kind='bar',
    stacked=True,
    width=0.9,
    color=['blue', 'green', 'orange'],
    ax=ax
)

x_numeric = np.arange(len(stacked))
rolling_avg = stacked['total'].rolling(window=5, min_periods=1, center=False).mean()

ax.plot(
    x_numeric,
    rolling_avg,
    color='black',
    linewidth=2,
    linestyle='--',
    label='5-Year Rolling Average'
)
for i, (year, count) in enumerate(stacked['total'].items()):
    ax.annotate(
        f"{int(count):,}",
        xy=(i, count),
        xytext=(0, 4),
        textcoords='offset points',
        ha='center',
        fontsize=7
    )
years = list(stacked.index)

if 2016 in years:
    x_feja = years.index(2016) - 0.5
    ax.axvline(x=x_feja, color='black', linewidth=1.5, linestyle='--')
    ax.text(
        x_feja - 0.1,
        stacked['total'].max() * 0.98,
        'Future Energy\nJobs Act passed',
        ha='right', va='top',
        fontsize=8, color='black',
        style='italic'
    )

if 2019 in years:
    x_isfa = years.index(2019) - 0.5
    ax.axvline(x=x_isfa, color='black', linewidth=1.5, linestyle='--')
    ax.text(
        x_isfa - 0.1,
        stacked['total'].max() * 0.98,
        'Illinois Solar for\nAll implemented',
        ha='right', va='top',
        fontsize=8, color='black',
        style='italic'
    )
ax.set_title('Climate Resilient Infrastructure Permits by Year in Chicago (2006-2025)', fontsize=13, pad=12)
ax.set_xlabel('Year', fontsize=10)
ax.set_ylabel('Number of Permits Issued', fontsize=10)
ax.tick_params(axis='x', rotation=45)
ax.legend(title='Permit Type', fontsize=9, title_fontsize=9)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))

plt.tight_layout()
plt.savefig("../Visualizations/climate_permits_stacked_by_year.png", dpi=150, bbox_inches='tight')
plt.show()

# Save permit data as CSVs

is_solar_permits.to_csv("../Data/Permit Data/solar_permits.csv", index=False)
is_flood_permits.to_csv("../Data/Permit Data/flood_permits.csv", index=False)
is_green_permits.to_csv("../Data/Permit Data/green_permits.csv", index=False)

# Save permit data as geopandas

utm18n = 26918

def load_permit_geodataframe(df):
    df = df.dropna(subset=["xcoordinate", "ycoordinate"])
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["xcoordinate"], df["ycoordinate"]),
        crs="EPSG:3435"
    ).to_crs(epsg=utm18n)
    return gdf

solar_geo = load_permit_geodataframe(is_solar_permits)
flood_geo = load_permit_geodataframe(is_flood_permits)
green_geo = load_permit_geodataframe(is_green_permits)

gpkg_path = "../Data/Geodata/permits.gpkg"

solar_geo.to_file(gpkg_path, layer="solar", driver="GPKG")
flood_geo.to_file(gpkg_path, layer="flood", driver="GPKG")
green_geo.to_file(gpkg_path, layer="green", driver="GPKG")