<div style="display: flex; flex-direction: column; align-items: center; justify-content: center;">
  <img src="https://github.com/user-attachments/assets/a3ede50e-acbb-4375-bcfd-a3892f8c3c7d" alt="logo" width="250"/>
  <div style="display: flex; justify-content: center; margin-top: 10px;">
    <img src="https://github.com/user-attachments/assets/9e748a0f-6594-4ed8-bb55-1e0ce53a1577" alt="logo" width="200"/>
    <img src="https://github.com/user-attachments/assets/37f31ff8-b4da-42a6-8497-ed0566555f82" alt="logo" width="200"/>
  </div>
</div>



# pyeogpr [![GitHub](https://img.shields.io/badge/GitHub-pyeogpr-purple.svg)](https://github.com/daviddkovacs/pyeogpr)   [![Documentation](https://img.shields.io/badge/docs-pyeogpr-blue.svg)](https://pyeogpr.readthedocs.io/en/latest/pyeogpr.html) [![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.13373838-green)](https://doi.org/10.5281/zenodo.13373838)



Python based machine learning library to use Earth Observation data to map biophysical traits using Gaussian Process Regression (GPR) models. Works with Google Earth Engine and openEO cloud back-ends.

# Features

- Access to GEE/openEO is required. Works best with the Copernicus Data Space Ecosystem. Register [here](https://code.earthengine.google.com/register) or [here](https://docs.openeo.cloud/join/free_trial.html)
 - Hybrid retrieval methods were used: the Gaussian Process Regression retrieval algorithms were trained on biophysical trait specific radiative transfer model (RTM) simulations
- Built-in gap-filling to avoid cloud covers
- Runs "in the cloud" with the GEE/openEO Python API. No local processing is needed.
- Resulting maps in .tiff or netCDF format

# Get started

Refer to the [Documentation](https://pyeogpr.readthedocs.io/en/latest/pyeogpr.html) for instructions and examples.


# Satellites and biophysical variables

You can select from a list of trained variables developed for the following satellites:

[Sentinel-2 L1C](https://pyeogpr.readthedocs.io/en/latest/sensors.html#)

[Sentinel-2 L2A](https://pyeogpr.readthedocs.io/en/latest/sensors.html#)

[Sentinel-3 OLCI L1B](https://pyeogpr.readthedocs.io/en/latest/sensors.html#sentinel-3-ocean-and-land-colour-instrument-olci)
<!-- TODO: Update Docs for Landsat 8 -->
[Landsat8_L2](https://pyeogpr.readthedocs.io/en/latest/sensors.html#)

# Cite as / Contact

- Kovács DD, Reyes-Muñoz P, Salinero-Delgado M, Mészáros VI, Berger K, Verrelst J. Cloud-Free Global Maps of Essential Vegetation Traits Processed from the TOA Sentinel-3 Catalogue in Google Earth Engine. Remote Sensing. 2023; 15(13):3404. https://doi.org/10.3390/rs15133404
  
or

- Dávid D.Kovács. (2024). pyeogpr (zenodo). Zenodo. https://doi.org/10.5281/zenodo.13373838
- david.kovacs@uv.es

## 
Supported by the European Union (European Research Council, FLEXINEL, 101086622) project.

<a href="https://leoipl.uv.es/flexinel/">
  <img src="https://github.com/user-attachments/assets/940bf34f-04d3-4fb0-9d68-8d6f19c14bab" alt="ERC Logo">
</a>
