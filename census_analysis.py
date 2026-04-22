#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 20:18:57 2026

@author: loganbattaglia
"""

# Visualize census demographic data

import pandas as pd
import geopandas as gpd
import numpy as np

# Read shapefile into variable, filter to NY counties

geodata = gpd.read_file("cb_2024_17_tract_500k.zip")
geodata = geodata.query('COUNTYFP == "031"')

# Read census data into file

demos = pd.read_csv("chicago_census_data.csv", dtype={"GEOID": str})

# Replace Census sentinel value with NaN
demos = demos.replace(-666666666, np.nan)

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

print(f"Before clip: {len(geodata)} tracts")
geo_clip = geodata.clip(boundary, keep_geom_type=True)
print(f"After clip:  {len(geo_clip)} tracts")

# Read building permits, convert to geodataframe using lat/lon

permits = pd.read_csv("chicago_building_permits.csv", dtype={"id": str})
permits = permits.dropna(subset=["xcoordinate", "ycoordinate"])
permits_geo = gpd.GeoDataFrame(
    permits,
    geometry=gpd.points_from_xy(permits["xcoordinate"], permits["ycoordinate"]),
    crs="EPSG:3435"
).to_crs(epsg=utm18n)

# Confirm they now overlap

print("Permit bounds: ", permits_geo.total_bounds)
print("Tract bounds:  ", geo_clip.total_bounds)

# Spatial join permits to clipped tracts, count per tract

permits_joined = gpd.sjoin(permits_geo, geo_clip[['GEOID', 'geometry']],
                            how='inner', predicate='within')
permit_counts  = permits_joined.groupby('GEOID').size().reset_index(name='permit_count')

# Merge permit counts back onto clipped tracts

geo_clip = geo_clip.merge(permit_counts, on='GEOID', how='left')
geo_clip['permit_count'] = geo_clip['permit_count'].fillna(0).astype(int)
geo_clip['permit_rate'] = (geo_clip['permit_count'] / geo_clip['total_population']) * 1000

# Clean up columns before export
# Geopackage does not support list or geometry columns other than the main one
# Drop centroid and any plotting-only columns before saving

cols_to_drop = ['centroid', 'symbol_size', 'income_class']
geo_clip = geo_clip.drop(columns=[c for c in cols_to_drop if c in geo_clip.columns])

# Export all three layers to a single geopackage

gpkg_path = "chicago.gpkg"
boundary.to_file(gpkg_path, layer="city_boundary", driver="GPKG")
geo_clip.to_file(gpkg_path, layer="census_tracts", driver="GPKG")
tract_centroids = geo_clip[['GEOID', 'permit_count']].copy()
tract_centroids['geometry'] = geo_clip.geometry.centroid
tract_centroids = gpd.GeoDataFrame(tract_centroids, geometry='geometry', crs=utm18n)
tract_centroids.to_file(gpkg_path, layer="permit_counts_by_tract", driver="GPKG")
