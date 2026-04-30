# Climate Resilient Infrastructure in Chicago

## Introduction 

This project examines 2006-2025 building permit data in the City of Chicago to identify spatial and temporal trends in climate infrastructure development relative to climate infrastructure policies and neighborhood demographics. 

## Data

The City of Chicago maintains an online dataset with a record for every permit request filed, with information about the address of the property, the name of the person who filed the request, and the type of work that will be done at the property. The dataset ranges from 2006-2026, but for the purposes of this analysis, only 2006-2025 are included as 2026 has incomplete data.
The dataset used in this project can be found at the [City of Chicago's Data Portal](https://data.cityofchicago.org/Buildings/Building-Permits/ydr8-5enu/about_data).

Additionally, Census Bureau data was used for demographic purposes and geospatial visualization. American Community Survey 5-Year Estimates for Cook County (by census tract) with demographic data can be found [here](https://data.census.gov/table?g=050XX00US17031$1400000&y=2024), and cartographic shapefiles for geospatial visualization can be found [here](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html) on the Census Bureau's website.

## Scripts 

The scripts are organized in the following order: `1-collect_permits.py` -> `2-census_api.py` -> `3-permit_analysis.py` -> `4-census_analysis.py` -> `5-ward_time_analysis.py` -> `6-equity_race_analysis.py` -> `7-geo_analysis.qgz`.

1. `1-collect_permits.py`

This script uses the City of Chicago's API to pull building permit data for the requested variables and writes them into a CSV file called `chicago_building_permits.csv`. It also pulls column metadata for those same variables into a separate dataframe and saves that as `chicago_building_permits_metadata.csv`.

2. `2-census_api.py`

3. `3-permit_analysis.py`

4. `4-census_analysis.py`

5. `5-ward_time_analysis.py`

6. `6-equity_race_analysis.py`

7. `7-geo_analysis.qgz`

## Results


