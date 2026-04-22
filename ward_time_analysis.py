#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 10:20:12 2026

@author: loganbattaglia
"""

# Import needed packages 

import pandas as pd
import geopandas as gpd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Import needed files

# Building permits CSV (replace null values, filter out incomplete 2026)

permits = pd.read_csv("chicago_building_permits.csv", dtype={"id": str}, low_memory=False)
permits = permits.replace(-666666666, np.nan)
permits = permits[permits['issue_year'] < 2026]

# Census demographic data

demos = pd.read_csv("chicago_census_data.csv", dtype={"GEOID": str})
demos = demos.replace(-666666666, np.nan)

# Geopackage layers

boundary = gpd.read_file("chicago.gpkg", layer="city_boundary")
geo_clip = gpd.read_file("chicago.gpkg", layer="census_tracts")
tract_centroids = gpd.read_file("chicago.gpkg", layer="permit_counts_by_tract")

# Wards shapefile

wards = gpd.read_file("chicago_ward_boundaries_2023.zip")

# Convert permits to geodataframe

utm18n = 26918
permits_geo = gpd.GeoDataFrame(
    permits,
    geometry=gpd.points_from_xy(permits['xcoordinate'], permits['ycoordinate']),
    crs='EPSG:3435'
).to_crs(epsg=utm18n)

# Project wards shapefile

wards = wards.to_crs(epsg=utm18n)

# Spatial join permits to tracts to get GEOID on each permit

permits_with_ward = gpd.sjoin(
    permits_geo[['id', 'issue_year', 'geometry']],
    wards[['ward', 'geometry']],
    how='inner',
    predicate='within'
)

print(f"Permits matched to wards: {len(permits_with_ward):,}")

# Count permits by GEOID and year

permits_by_ward_year = (
    permits_with_ward
    .groupby(['ward', 'issue_year'])
    .size()
    .reset_index(name='permit_count')
)

# Pivot to wide format: one row per tract, one column per year

permits_wide = permits_by_ward_year.pivot_table(
    index='ward',
    columns='issue_year',
    values='permit_count',
    fill_value=0
)

# Flatten column names to strings like 'permits_2004'

permits_wide.columns = [f'permits_{int(y)}' for y in permits_wide.columns]
permits_wide = permits_wide.reset_index()

print(f"Wide format: {len(permits_wide)} wards x {len(permits_wide.columns)} columns")
print(permits_wide.head())

# Merge onto wards

wards = wards.merge(permits_wide, on='ward', how='left') 

# Fill any wards with no permits at all with 0

year_cols = [c for c in wards.columns if c.startswith('permits_')]
wards[year_cols] = wards[year_cols].fillna(0).astype(int)

# Add total permit count across all years

wards['permits_total'] = wards[year_cols].sum(axis=1)

# Prepare data for heatmap visualization

heatmap_ward = permits_by_ward_year.pivot_table(
    index='ward',
    columns='issue_year',
    values='permit_count',
    fill_value=0
)

# Plot heatmap with normalized peaks

fig, ax = plt.subplots(figsize=(20, 12), dpi=150)
heatmap_ward = heatmap_ward.sort_index(ascending=True)
heatmap_ward = heatmap_ward.fillna(0).astype(int)
heatmap_norm = heatmap_ward.div(heatmap_ward.max(axis=1), axis=0).fillna(0)

sns.heatmap(
    heatmap_norm,                                             
    cmap='plasma',
    linewidths=0.3,
    linecolor='white',
    ax=ax,
    cbar_kws={'label': 'Permits (normalized to ward max)', 'shrink': 0.5}, 
    xticklabels=True,
    yticklabels=True,
    annot=True,
    fmt='.2f',                                               
    annot_kws={'size': 5},
    vmin=0,                                                    
    vmax=1,                                                   
)

ax.set_title('Building Permits by Ward and Year\n(Normalized to Each Ward\'s Peak Year)', 
             fontsize=14, pad=12)
ax.set_xlabel('Year', fontsize=10)
ax.set_ylabel('Ward', fontsize=10)
ax.tick_params(axis='x', rotation=45)
ax.tick_params(axis='y', labelsize=8)

plt.tight_layout()
plt.savefig('Visualizations/heatmap_wards_normalized.png', dpi=150, bbox_inches='tight') 
plt.show()

# Try non-normalized version of plot 

fig, ax = plt.subplots(figsize=(20, 12), dpi=150)
heatmap_ward = permits_by_ward_year.pivot_table(
    index='ward',
    columns='issue_year',
    values='permit_count',
    fill_value=0
)
heatmap_ward = heatmap_ward.sort_index(ascending=True)

heatmap_ward = heatmap_ward.fillna(0).astype(int)
heatmap_ward = heatmap_ward.sort_index(ascending=True)  

sns.heatmap(
    heatmap_ward,
    cmap='plasma',                                      
    linewidths=0.3,
    linecolor='white',
    ax=ax,
    cbar_kws={'label': 'Permit Count', 'shrink': 0.5},   
    xticklabels=True,
    yticklabels=True,
    annot=True,                                        
    fmt='d',                                          
    annot_kws={'size': 5},
)

ax.set_title('Building Permits by Ward and Year', fontsize=14, pad=12)  
ax.set_xlabel('Year', fontsize=10)
ax.set_ylabel('Ward', fontsize=10)
ax.tick_params(axis='x', rotation=45)
ax.tick_params(axis='y', labelsize=8)

plt.tight_layout()
plt.savefig('Visualizations/heatmap_wards_raw.png', dpi=150, bbox_inches='tight')   
plt.show()

# Create line chart of permit counts by year

permits_by_year = permits_by_ward_year.groupby('issue_year')['permit_count'].sum().reset_index()

fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
ax.bar(
    permits_by_year['issue_year'],
    permits_by_year['permit_count'],
    color='gray',
    width=0.9,
    label='Total Permits'
)

for _, row in permits_by_year.iterrows():
    ax.annotate(
        f"{int(row['permit_count']):,}",
        xy=(row['issue_year'], row['permit_count']),
        xytext=(0, 8),
        textcoords='offset points',
        ha='center',
        fontsize=7
    )

ax.set_title('Total Building Permits by Year', fontsize=13, pad=12)
ax.set_xlabel('Year', fontsize=10)
ax.set_ylabel('Total Permits', fontsize=10)
ax.set_xticks(permits_by_year['issue_year'])
ax.tick_params(axis='x', rotation=45)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))
ax.grid(axis='y', linestyle='--', alpha=0.5)
ax.set_ylim(0, 55000) 

plt.tight_layout()
plt.savefig('Visualizations/timeseries_total_permits.png', dpi=150, bbox_inches='tight')
plt.show()


