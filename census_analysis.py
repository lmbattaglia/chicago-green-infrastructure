#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 20:18:57 2026

@author: loganbattaglia
"""

# Visualize census demographic data

import pandas as pd
import geopandas as gpd

# Read shapefile into variable, filter to NY counties

geodata = gpd.read_file("cb_2024_17_tract_500k.zip")
geodata = geodata.query('COUNTYFP == "031"')

# Read census data into file

demos = pd.read_csv("chicago_census_data.csv", dtype={"GEOID": str})

# Merge geodata on census data

geodata = geodata.merge(demos, on="GEOID", how="left", indicator=True)

# Print value counts and drop column

print( geodata['_merge'].value_counts() )
geodata.drop(columns='_merge',inplace=True)

# Write geodata to geopackage file

geodata.to_file("tracts.gpkg",layer="")

# Read chicago city boundary into shapefile

boundary = gpd.read_file("chicago_city_boundary.zip")

# Set up projection number

utm18n = 26918

# Reproject shapefiles to utm 18n

boundary = boundary.to_crs(epsg=utm18n)
geodata = geodata.to_crs(epsg=utm18n)

# Clip census data to City of Chicago

geo_clip = geodata.clip(boundary,keep_geom_type=True)
