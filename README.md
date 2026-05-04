# Climate Resilient Infrastructure in Chicago

## Introduction 

This project examines 2006-2025 building permit data in the City of Chicago to identify spatial and temporal trends in climate infrastructure development relative to climate infrastructure policies and neighborhood demographics. 

## Data

The City of Chicago maintains an online dataset with a record for every permit request filed, with information about the address of the property, the name of the person who filed the request, and the type of work that will be done at the property. The dataset ranges from 2006-2026, but for the purposes of this analysis, only 2006-2025 are included as 2026 has incomplete data.
The dataset used in this project can be found at the [City of Chicago's Data Portal](https://data.cityofchicago.org/Buildings/Building-Permits/ydr8-5enu/about_data).

Additionally, Census Bureau data was used for demographic purposes and geospatial visualization. American Community Survey 5-Year Estimates for Cook County (by census tract) with demographic data can be found [here](https://data.census.gov/table?g=050XX00US17031$1400000&y=2024), and cartographic shapefiles for geospatial visualization can be found [here](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html) on the Census Bureau's website.

## Scripts 

The scripts are organized in the following order: `1-collect_permits.py` -> `2-census_api.py` -> `3-permit_analysis.py` -> `4-census_analysis.py` -> `5-equity_race_analysis.py` -> `6-geo_analysis.qgz`.

1. `1-collect_permits.py`

This script uses the City of Chicago's API to pull building permit data for the requested variables and writes them into a CSV file called `chicago_building_permits.csv`. It also pulls column metadata for those same variables into a separate dataframe and saves that as `chicago_building_permits_metadata.csv`.

2. `2-census_api.py`

This script pulls census variables from the Census Bureau ACS as specified in the file list and organizes them into a dataframe with readable names. It calculates variables including poverty rate, unemployment rate, and percentage of the population with a bachelor's degree or higher. It then saves the dataframe as `chicago_census_data.csv`.

3. `3-permit_analysis.py`

This script adds column to the permit dataframe for issue day, month, and year by parsing the issue date category. It then separates out solar, flood mitigation, and green infrastructure permits out into separate dataframes based on if the keywords below were in the work description or type fields:

- __Solar__: solar, Small-Scale Solar PV System
- __Flood Mitigation__: flood, rain, stormwater, storm water
- __Green Infrastructure__: green roof, plant, planting, plants, or any of the other words and tree or trees

Then, the script creates bar charts for each of the three types showing permits by year. It stacks the three permit types into one dataset and visualizes all permit types by year before saving the permit data as CSV files and geopandas files.

4. `4-census_analysis.py`

This script downloads census tract cartographic shapefile data and merges the spatial data with the census demographic data before being reprojected to UTM 18N and clipped to the Chicago city boundary. It then converts permit data to a geodataframe and merges permit data with the census geodataframe before saving all spatial data to `chicago.gpkg`.

5. `5-equity_race_analysis.py`

This script analyzes and creates visualizations for:

- total permit counts by year
- permit rate by tract income quartile
- permit rate by tract racial majority
- median income vs permit rate
    - with vs without 99% outliers
- poverty rate vs permit rate 
    - with vs without 99% outliers
- permit counts by year and income quartile
    - solar
    - flood mitigation
    - green infrastructure

It then saves all visualizations in the Visualizations folder.

6. `6-geo_analysis.qgz`

This is a QGIS project with layers for census tracts, permit counts, and demographic census variables.

## Results


