# pyeogpr

Python based machine learning library to use Earth Observation data to retrieve biophysical maps using Gaussian Process Regression.

## Features

- Uses satellite observations and machine learning to infer biophysical maps
- Get your maps in a few lines of code: select your region, temporal domain and satellite sensor to get the maps you are looking for!
- Runs "in the cloud" with the openEO API. No local processing needed!

## Available Biophysical Variables

This package currently features the following satellite sensors and biophysical variables for mapping:

- **Sentinel 2**
  - **Top of atmosphere: Level 1C** [![DOI](https://img.shields.io/badge/DOI-10.1016/estevez_et_al_2022-doi.svg)](https://doi.org/10.1016/j.rse.2022.112958)
    
    **Leaf variables:**
    - _Cab_: Leaf chlorophyll content
    - _Cm_: Leaf dry matter content
    - _Cw_: Leaf water content
    
    **Canopy variables:**
    - _FVC_: Fractional Vegetation Cover
    - _LAI_: Leaf Area Index
    - _laiCab_: Canopy chlorophyll content
    - _laiCm_: Canopy dry matter content
    - _laiCw_: Canopy water content
