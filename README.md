
<div style="display: flex; justify-content: center;">
  <img src="https://github.com/user-attachments/assets/a3ede50e-acbb-4375-bcfd-a3892f8c3c7d" alt="logo" width="200"/>
</div>

# pyeogpr [![GitHub](https://img.shields.io/badge/GitHub-pyeogpr-purple.svg)](https://github.com/daviddkovacs/pyeogpr)   [![Documentation](https://img.shields.io/badge/docs-pyeogpr-blue.svg)](https://pyeogpr.readthedocs.io/en/latest/pyeogpr.html) [![DOI](https://img.shields.io/badge/DOI-10.5281%2Fzenodo.13373838-green)](https://doi.org/10.5281/zenodo.13373838)



Python based machine learning library to use Earth Observation data to map biophysical traits using Gaussian Process Regression (GPR) models.

# Features

- Access to openEO is required. Works best with the Copernicus Data Space Ecosystem. Register [here](https://documentation.dataspace.copernicus.eu/Registration.html) or [here](https://docs.openeo.cloud/join/free_trial.html)
 - Hybrid retrieval methods were used: the Gaussian Process Regression retrieval algorithms were trained on biophysical trait specific radiative transfer model (RTM) simulations
- Built-in gap-filling to avoid cloud covers
- Runs "in the cloud" with the openEO API. No local processing is needed.
- Resulting maps in .tiff or netCDF format

# Get started

You can install pyeogpr using pip. Read the [documentation](https://pyeogpr.readthedocs.io/en/latest/pyeogpr.html)

```shell
pip install pyeogpr
```
Basic example:
```shell
import pyeogpr

# Your region of interest
bounding_box = [
         -73.98605881463239,
          40.763066527718536,
          -73.94617017216025,
          40.80083669627726
        ]

# Time window for processing Satellite observations
time_window = ["2022-07-01", "2022-07-07"]

dc = pyeogpr.Datacube(
    "SENTINEL2_L2A",  # Satellite sensor
    "FVC",            # Fractional Vegetation Cover
    bounding_box,
    time_window,
    cloudmask=True
)

dc.construct_datacube("dekad")  # Initiates openEO datacube

dc.process_map()  # Starts GPR processing
```
To download the GPR processed map go to the [openEO portal](https://openeo.dataspace.copernicus.eu/):

![download](https://github.com/user-attachments/assets/a869b60f-a420-4459-83ac-289c99758c8d)

You can use [QGIS](https://qgis.org/download/) or [Panoply](https://www.giss.nasa.gov/tools/panoply/) to visualize. IMPORTANT: The data range is off, due to few pixels being outliers.
Set the data range manually for the corresponding variable e.g. FVC--> 0 to 1.

![map](https://github.com/user-attachments/assets/6f2cc18c-1568-4aa5-a3d6-e028e69e361d)


# Satellites and biophysical variables

You can select from a list of trained variables developed for the following satellites:

[Sentinel-2 L1C](https://pyeogpr.readthedocs.io/en/latest/sensors.html#)

[Sentinel-2 L2A](https://pyeogpr.readthedocs.io/en/latest/sensors.html#)

[Sentinel-3 OLCI L1B](https://pyeogpr.readthedocs.io/en/latest/sensors.html#sentinel-3-ocean-and-land-colour-instrument-olci)

# Cite as


Dávid D.Kovács. (2024). pyeogpr (zenodo). Zenodo. https://doi.org/10.5281/zenodo.13373838

## 
Supported by the European Union (European Research Council, FLEXINEL, 101086622) project.

<a href="https://leoipl.uv.es/flexinel/">
  <img src="https://github.com/user-attachments/assets/940bf34f-04d3-4fb0-9d68-8d6f19c14bab" alt="ERC Logo">
</a>
