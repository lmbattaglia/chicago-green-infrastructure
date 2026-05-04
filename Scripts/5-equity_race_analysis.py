#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 18:34:45 2026

@author: loganbattaglia
"""

# Import needed modules, check that Visualizations directory exists

import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
os.makedirs("../Visualizations", exist_ok=True)

# Read needed files 

# Census demographic data

demos = pd.read_csv("../Data/Census Data/chicago_census_data.csv", dtype={"GEOID": str})
demos = demos.replace(-666666666, np.nan)

# Geopackage layers

boundary    = gpd.read_file("../Data/Geodata/chicago.gpkg", layer="city_boundary")
geo_clip    = gpd.read_file("../Data/Geodata/chicago.gpkg", layer="census_tracts")

# Building permits

permits = pd.read_csv("../Data/Permit Data/chicago_building_permits.csv", dtype={"id": str}, low_memory=False)
permits = permits.replace(-666666666, np.nan)
permits = permits[permits['issue_year'] < 2026]

# Read building permits, convert to geodataframe using lat/lon

utm18n = 26918
permits = pd.read_csv("../Data/Permit Data/chicago_building_permits.csv", dtype={"id": str})
permits = permits.dropna(subset=["xcoordinate", "ycoordinate"])
permits_geo = gpd.GeoDataFrame(
    permits,
    geometry=gpd.points_from_xy(permits["xcoordinate"], permits["ycoordinate"]),
    crs="EPSG:3435"
).to_crs(epsg=utm18n)

# Spatial join permits to census tracts to get GEOID on each permit

permits_with_tract = gpd.sjoin(
    permits_geo[['id', 'issue_year', 'geometry']],
    geo_clip[['GEOID', 'geometry']],
    how='inner',
    predicate='within'
)
print(f"Permits matched to census tracts: {len(permits_with_tract):,}")

# Count total permits by year directly

permits_by_year = (
    permits_with_tract
    .groupby('issue_year')
    .size()
    .reset_index(name='permit_count')
)

# Create bar chart of permit counts by year

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
ax.set_ylim(0, 55000)
plt.tight_layout()
plt.savefig('../Visualizations/timeseries_total_permits.png', dpi=150, bbox_inches='tight')
plt.show()

# Bin tracts by income quartile

geo_clip = geo_clip.dropna(subset=['median_household_income'])

geo_clip['income_quartile'] = pd.qcut(
    geo_clip['median_household_income'],
    q=4,
    labels=['Q1\n(Lowest Income)', 'Q2', 'Q3', 'Q4\n(Highest Income)']
)

# Create bar chart for permit rate by income quartile 

quartile_permits = geo_clip.groupby('income_quartile', observed=True)['permit_rate'].mean().reset_index()

fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
bars = ax.bar(
    quartile_permits['income_quartile'],
    quartile_permits['permit_rate'],
    color=['#2C3E7A', '#5B7FBF', '#F4A460', '#D4622A'],
    width=0.6,
    edgecolor='white'
)

for bar in bars:
    ax.annotate(
        f"{bar.get_height():.1f}",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 4),
        textcoords='offset points',
        ha='center', fontsize=9
    )

ax.set_title('Average Building Permit Rate by Income Quartile\n(Permits per 1,000 Residents)', fontsize=12, pad=12)
ax.set_xlabel('Income Quartile', fontsize=10)
ax.set_ylabel('Permits per 1,000 Residents', fontsize=10)
ax.set_ylim(0, quartile_permits['permit_rate'].max() * 1.2)

plt.tight_layout()
plt.savefig('../Visualizations/permit_rate_by_income_quartile.png', dpi=150, bbox_inches='tight')
plt.show()

# Create bar chart: permit rate by racial majority tract

# Classify each tract by its plurality racial group

race_cols = {
    'pct_white':    'Majority White',
    'pct_black':    'Majority Black',
    'pct_hispanic': 'Majority Hispanic',
    'pct_asian':    'Majority Asian',
}

# Compute pct columns if not already present

geo_clip['pct_white']    = geo_clip['pop_white_alone']    / geo_clip['total_population']
geo_clip['pct_black']    = geo_clip['pop_black_alone']    / geo_clip['total_population']
geo_clip['pct_hispanic'] = geo_clip['pop_hispanic_latino']/ geo_clip['total_population']
geo_clip['pct_asian']    = geo_clip['pop_asian_alone']    / geo_clip['total_population']

def classify_race(row):
    shares = {
        'Majority White':    row.get('pct_white', 0),
        'Majority Black':    row.get('pct_black', 0),
        'Majority Hispanic': row.get('pct_hispanic', 0),
        'Majority Asian':    row.get('pct_asian', 0),
    }
    max_group = max(shares, key=shares.get)
    if shares[max_group] >= 0.5:
        return max_group
    return 'Mixed / No Majority'

geo_clip['racial_majority'] = geo_clip.apply(classify_race, axis=1)

race_permits = (
    geo_clip.groupby('racial_majority')['permit_rate']
    .mean()
    .reset_index()
    .sort_values('permit_rate', ascending=False)
)

fig, ax = plt.subplots(figsize=(9, 5), dpi=150)
colors = {
    'Majority White':    '#2C3E7A',
    'Majority Black':    '#5B7FBF',
    'Majority Hispanic': '#F4A460',
    'Majority Asian':    '#D4622A',
    'Mixed / No Majority': '#909090'
}
bar_colors = [colors.get(r, '#999999') for r in race_permits['racial_majority']]

bars = ax.bar(
    race_permits['racial_majority'],
    race_permits['permit_rate'],
    color=bar_colors,
    width=0.6,
    edgecolor='white'
)

for bar in bars:
    ax.annotate(
        f"{bar.get_height():.1f}",
        xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
        xytext=(0, 4),
        textcoords='offset points',
        ha='center', fontsize=9
    )

ax.set_title('Average Building Permit Rate by Racial Majority of Census Tract\n(Permits per 1,000 Residents)',
             fontsize=12, pad=12)
ax.set_xlabel('Tract Racial Composition', fontsize=10)
ax.set_ylabel('Permits per 1,000 Residents', fontsize=10)
ax.set_ylim(0, race_permits['permit_rate'].max() * 1.2)
ax.tick_params(axis='x', labelsize=9)

plt.tight_layout()
plt.savefig('../Visualizations/permit_rate_by_race.png', dpi=150, bbox_inches='tight')
plt.show()

# Create scatter plot: median income vs permit rate

outlier_threshold = 0.99

fig, ax = plt.subplots(figsize=(9, 6), dpi=150)

scatter_data = geo_clip.dropna(subset=['median_household_income', 'permit_rate'])

ax.scatter(
    scatter_data['median_household_income'],
    scatter_data['permit_rate'],
    alpha=0.5,
    s=20,
    color='steelblue',
    edgecolor='none'
)

z = np.polyfit(scatter_data['median_household_income'], scatter_data['permit_rate'], 1)
p = np.poly1d(z)
x_line = np.linspace(scatter_data['median_household_income'].min(),
                     scatter_data['median_household_income'].max(), 300)
ax.plot(x_line, p(x_line), color='red', linewidth=2, linestyle='--', label='Trend')

threshold1 = scatter_data['permit_rate'].quantile(outlier_threshold)
outliers1  = scatter_data[scatter_data['permit_rate'] > threshold1]

ax.scatter(
    outliers1['median_household_income'],
    outliers1['permit_rate'],
    color='red', s=30, zorder=5, edgecolor='darkred', linewidth=0.5
)

for _, row in outliers1.iterrows():
    ax.annotate(
        row['NAMELSAD'],
        xy=(row['median_household_income'], row['permit_rate']),
        xytext=(5, 3),
        textcoords='offset points',
        fontsize=6,
        color='darkred'
    )
ax.set_title('Median Household Income vs. Permit Rate by Census Tract', fontsize=12, pad=12)
ax.set_xlabel('Median Household Income ($)', fontsize=10)
ax.set_ylabel('Permits per 1,000 Residents', fontsize=10)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${int(x):,}'))
ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig('../Visualizations/scatter_income_vs_permit_rate.png', dpi=150, bbox_inches='tight')
plt.show()

# Create scatterplot of poverty rate vs permit rate

fig, ax = plt.subplots(figsize=(9, 6), dpi=150)

scatter_data2 = geo_clip.dropna(subset=['poverty_rate', 'permit_rate'])

ax.scatter(
    scatter_data2['poverty_rate'] * 100,
    scatter_data2['permit_rate'],
    alpha=0.5,
    s=20,
    color='darkorange',
    edgecolor='none'
)

z2 = np.polyfit(scatter_data2['poverty_rate'], scatter_data2['permit_rate'], 1)
p2 = np.poly1d(z2)
x_line2 = np.linspace(scatter_data2['poverty_rate'].min(),
                      scatter_data2['poverty_rate'].max(), 300)
ax.plot(x_line2 * 100, p2(x_line2), color='red', linewidth=2, linestyle='--', label='Trend')

threshold2 = scatter_data2['permit_rate'].quantile(outlier_threshold)
outliers2  = scatter_data2[scatter_data2['permit_rate'] > threshold2]

ax.scatter(
    outliers2['poverty_rate'] * 100,
    outliers2['permit_rate'],
    color='red', s=30, zorder=5, edgecolor='darkred', linewidth=0.5
)

for _, row in outliers2.iterrows():
    ax.annotate(
        row['NAMELSAD'],
        xy=(row['poverty_rate'] * 100, row['permit_rate']),
        xytext=(5, 3),
        textcoords='offset points',
        fontsize=6,
        color='darkred'
    )
ax.set_title('Poverty Rate vs. Permit Rate by Census Tract', fontsize=12, pad=12)
ax.set_xlabel('Poverty Rate (%)', fontsize=10)
ax.set_ylabel('Permits per 1,000 Residents', fontsize=10)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))
ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig('../Visualizations/scatter_poverty_vs_permit_rate.png', dpi=150, bbox_inches='tight')
plt.show()

# ------------- No Outliers ---------------

# Define outlier threshold

outlier_remove          = 0.99  

# Create scatterplot of median income vs permit rate (no outliers)

fig, ax = plt.subplots(figsize=(9, 6), dpi=150)

scatter_data = geo_clip.dropna(subset=['median_household_income', 'permit_rate'])

lower1 = scatter_data['permit_rate'].quantile(1 - outlier_remove)
upper1 = scatter_data['permit_rate'].quantile(outlier_remove)
scatter_data_clean = scatter_data[
    (scatter_data['permit_rate'] >= lower1) &
    (scatter_data['permit_rate'] <= upper1)
]

ax.scatter(
    scatter_data_clean['median_household_income'],
    scatter_data_clean['permit_rate'],
    alpha=0.5,
    s=20,
    color='steelblue',
    edgecolor='none'
)

z = np.polyfit(scatter_data_clean['median_household_income'], scatter_data_clean['permit_rate'], 1)
p = np.poly1d(z)
x_line = np.linspace(scatter_data_clean['median_household_income'].min(),
                     scatter_data_clean['median_household_income'].max(), 300)
ax.plot(x_line, p(x_line), color='red', linewidth=2, linestyle='--', label='Trend')

ax.set_title('Median Household Income vs. Permit Rate by Census Tract\n(Outliers Above/Below 99th Percentile Removed)',
             fontsize=12, pad=12)
ax.set_xlabel('Median Household Income ($)', fontsize=10)
ax.set_ylabel('Permits per 1,000 Residents', fontsize=10)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${int(x):,}'))
ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig('../Visualizations/scatter_income_vs_permit_rate_no_outliers.png',   
            dpi=150, bbox_inches='tight')
plt.show()

# Create scatterplot of poverty rate vs permit rate (no outliers)

fig, ax = plt.subplots(figsize=(9, 6), dpi=150)

scatter_data2 = geo_clip.dropna(subset=['poverty_rate', 'permit_rate'])

lower2 = scatter_data2['permit_rate'].quantile(1 - outlier_remove)
upper2 = scatter_data2['permit_rate'].quantile(outlier_remove)
scatter_data2_clean = scatter_data2[
    (scatter_data2['permit_rate'] >= lower2) &
    (scatter_data2['permit_rate'] <= upper2)
]

ax.scatter(
    scatter_data2_clean['poverty_rate'] * 100,
    scatter_data2_clean['permit_rate'],
    alpha=0.5,
    s=20,
    color='darkorange',
    edgecolor='none'
)

z2 = np.polyfit(scatter_data2_clean['poverty_rate'], scatter_data2_clean['permit_rate'], 1)
p2 = np.poly1d(z2)
x_line2 = np.linspace(scatter_data2_clean['poverty_rate'].min(),
                      scatter_data2_clean['poverty_rate'].max(), 300)
ax.plot(x_line2 * 100, p2(x_line2), color='red', linewidth=2, linestyle='--', label='Trend')

ax.set_title('Poverty Rate vs. Permit Rate by Census Tract\n(Outliers Above/Below 99th Percentile Removed)',
             fontsize=12, pad=12)
ax.set_xlabel('Poverty Rate (%)', fontsize=10)
ax.set_ylabel('Permits per 1,000 Residents', fontsize=10)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))
ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig('../Visualizations/scatter_poverty_vs_permit_rate_no_outliers.png',  
            dpi=150, bbox_inches='tight')
plt.show()

# Create function for permit types bar chart by income quintile

def plot_permits_by_income_quartile(gdf, permit_type, geo_clip):
    config = {
        'solar': {
            'colors':   ['#FFE0B2', '#FFB74D', '#F57C00', '#E65100'], 
            'label':    'Solar',
            'filename': 'solar_permits_by_year_income_quartile.png',
        },
        'flood': {
            'colors':   ['#BBDEFB', '#64B5F6', '#1976D2', '#0D47A1'],  
            'label':    'Flood Mitigation',
            'filename': 'flood_permits_by_year_income_quartile.png',
        },
        'green': {
            'colors':   ['#C8E6C9', '#66BB6A', '#2E7D32', '#1B5E20'], 
            'label':    'Green Infrastructure',
            'filename': 'green_permits_by_year_income_quartile.png',
        },
    }

    cfg = config[permit_type]

    if gdf.crs != geo_clip.crs:
        gdf = gdf.to_crs(geo_clip.crs)

    # Spatial join to census tracts
    
    joined = gpd.sjoin(
        gdf[['id', 'issue_year', 'geometry']],
        geo_clip[['GEOID', 'median_household_income', 'geometry']],
        how='inner',
        predicate='within'
    )

    # Bin into income quartiles 
    
    joined = joined.dropna(subset=['median_household_income'])
    joined['income_quartile'] = pd.qcut(
        joined['median_household_income'],
        q=4,
        labels=['Q1 (Lowest)', 'Q2', 'Q3', 'Q4 (Highest)'] 
    )

    # Pivot for stacking 
    
    stacked = (
        joined
        .groupby(['issue_year', 'income_quartile'], observed=True)
        .size()
        .reset_index(name='permit_count')
        .pivot_table(index='issue_year', columns='income_quartile',
                     values='permit_count', fill_value=0)
    )

    # Create plot 
    fig, ax = plt.subplots(figsize=(12, 6), dpi=150)

    stacked.plot(
        kind='bar',
        stacked=True,
        color=cfg['colors'],         
        width=0.9,
        ax=ax
    )

    # Total count labels above each bar
    
    for i, (year, row) in enumerate(stacked.iterrows()):
        total = row.sum()
        ax.annotate(
            f"{int(total):,}",
            xy=(i, total),
            xytext=(0, 3),
            textcoords='offset points',
            ha='center',
            fontsize=7
        )

    ax.set_ylim(0, stacked.sum(axis=1).max() * 1.15)
    ax.set_title(f'{cfg["label"]} Permits by Year and Income Quartile\nin Chicago (2006-2025)',
                 fontsize=12, pad=12)
    ax.set_xlabel('Year', fontsize=10)
    ax.set_ylabel(f'Number of {cfg["label"]} Permits Issued', fontsize=10)
    ax.tick_params(axis='x', rotation=45)
    ax.legend(title='Income Quartile', fontsize=9, title_fontsize=9)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{int(x):,}'))

    plt.tight_layout()
    plt.savefig(f'../Visualizations/{cfg["filename"]}', dpi=150, bbox_inches='tight')
    plt.show()
    print(f"Saved: {cfg['filename']}")
    
# Read gpkg layers and call function 

solar_geo = gpd.read_file("../Data/Geodata/permits.gpkg", layer="solar")
flood_geo = gpd.read_file("../Data/Geodata/permits.gpkg", layer="flood")
green_geo = gpd.read_file("../Data/Geodata/permits.gpkg", layer="green")

plot_permits_by_income_quartile(solar_geo, 'solar', geo_clip)
plot_permits_by_income_quartile(flood_geo, 'flood', geo_clip)
plot_permits_by_income_quartile(green_geo, 'green', geo_clip)