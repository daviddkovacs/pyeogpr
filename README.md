
<div style="display: flex; justify-content: center;">
  <img src="https://github.com/user-attachments/assets/a3ede50e-acbb-4375-bcfd-a3892f8c3c7d" alt="logo" width="200"/>
</div>

# pyeogpr [![GitHub](https://img.shields.io/badge/GitHub-pyeogpr-purple.svg)](https://github.com/daviddkovacs/pyeogpr)   [![Documentation](https://img.shields.io/badge/docs-pyeogpr-blue.svg)](https://pyeogpr.readthedocs.io/en/latest/pyeogpr.html)


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
          -0.305543150556133,
          39.29253033906926,
          -0.28169853763617425,
          39.303338211248104
        ]

# Time window for processing Satellite observations
time_window = ["2022-05-01", "2022-06-01"]

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


# Available biophysical variables
## **- Sentinel 2 MultiSpectral Instrument (MSI)**

 - **Top of atmosphere: Level 1C**  
 
	*Model training details:* Estévez et al. 2022 [![DOI](https://img.shields.io/badge/DOI-j.rse.2022.112958-doi.svg)](https://doi.org/10.1016/j.rse.2022.112958)
 
	 Leaf variables:
	 - _Cab_: Leaf chlorophyll content
	 - _Cm_: Leaf dry matter content
	 - _Cw_: Leaf water content
	 	 
	Canopy variables
	 - 	 _FVC_: Fractional Vegetation Cover
	 - _LAI_: Leaf Area Index
	 - _laiCab_ Canopy chlorophyll content
	 - _laiCm_: Leaf dry matter content
	 - _laiCw_ Canopy water content

- **Bottom of atmosphere: Level 2A** 

	*Model training details:* Salinero et al. 2021 & De Clecrk et al.
 [![DOI](https://img.shields.io/badge/DOI-rs14010146-doi.svg)](https://doi.org/10.3390/rs14010146) [![DOI](https://img.shields.io/badge/DOI-under_review-doi.svg)](https://doi.org/)   

	 Leaf variables:
  	 - _Cab_: Leaf chlorophyll content
	 - _Cm_: Leaf dry matter content
	 - _Cw_: Leaf water content

  	Canopy variables:
	 -  _CNC_Cab_: Canopy Nitrogen Content (via chlorophyl-nitrogen relationship)
	 - 	 _CNC_Cprot_: Canopy Nitrogen Content (via protein content
	 - _FVC_: Fractional Vegetation Cover
	 - _LAI_: Leaf Area Index
	 - _laiCab_ Canopy chlorophyll content
	 - _laiCm_: Leaf dry matter content
	 - _laiCw_ Canopy water content

## **- Sentinel 3 Ocean and Land Colour Instrument (OLCI)**

 - **Top of atmosphere: Level 1B**
 
	*Model training details:* D.Kovács et al. 2023 & Reyes-Muñoz et al. 2022  [![DOI](https://img.shields.io/badge/DOI-rs15133404-doi.svg)](https://doi.org/10.3390/rs15133404)[![DOI](https://img.shields.io/badge/DOI-rs14061347-doi.svg)](https://doi.org/10.3390/rs14061347)
 
 
	 - _FAPAR_: Fraction of Absorbed Photosynthetically Active Radiation
	 - _FVC_ Fractional Vegetation Cover
	 - _LAI_: Leaf Area Index
	 - _LCC_ Leaf Chlorophyll Content

## 
Supported by the European Union (European Research Council, FLEXINEL, 101086622) project.

<a href="https://leoipl.uv.es/flexinel/">
  <img src="https://github.com/user-attachments/assets/940bf34f-04d3-4fb0-9d68-8d6f19c14bab" alt="ERC Logo">
</a>
