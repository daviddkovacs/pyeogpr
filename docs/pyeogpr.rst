.. image:: https://github.com/user-attachments/assets/9e748a0f-6594-4ed8-bb55-1e0ce53a1577
   :alt: Google Earth Engine Overview
   :align: center
   :width: 20%
   
   

Google Earth Engine (GEE) Back-end
===================================

This section covers the usage of the Google Earth Engine (GEE) back-end for Gaussian Process Regression (GPR) using PyEOGPR.

.. autoclass:: pyeogpr.EarthEngine
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: maploop,getInputDates,calculate_GREEN,addVariables,maskS3badPixels,sequence_GREEN
   :special-members: __init__  # This explicitly shows the constructor (__init__)

Example Usage
-------------

.. code-block:: python

   from pyeogpr import EarthEngine

   bounding_box = [
       17.83670163256923,
       46.55399091975397,
       18.368529333383833,
       46.935776495476205
     ]

   dc = EarthEngine(projectID  = "ee-dkvcsdvd",
                    sensor ="SENTINEL3_L1B", 
                    biovar = "FVC",        
                    bounding_box = bounding_box,
                    temporal_extent =  ["2021-07-01", "2021-07-08"],
                    spatial_resolution  = 300,
                    cloudmask =True)

   dc.construct_datacube(composite = 4)

   dc.process_map(assetpath = "projects/ee-dkvcsdvd/assets/MyImageCollection") 


.. image:: https://github.com/user-attachments/assets/37f31ff8-b4da-42a6-8497-ed0566555f82
   :alt: openEO Overview
   :align: center
   :width: 20%
   
   
   
openEO Back-end
===============

This section covers the usage of the openEO back-end for Gaussian Process Regression (GPR) using PyEOGPR.

.. autoclass:: pyeogpr.Datacube
   :members:
   :undoc-members:
   :show-inheritance:

Example Usage
-------------

.. code-block:: python

   from pyeogpr import Datacube

   bounding_box = [
              -0.305543150556133,
              39.29253033906926,
              -0.28169853763617425,
              39.303338211248104
            ]

   time_window = ["2022-05-01", "2022-06-01"]

   dc = pyeogpr.Datacube(
       "SENTINEL2_L2A",  
       "FVC",            
       bounding_box,
       time_window,
       cloudmask=True
   )

   dc.construct_datacube("dekad") 

   dc.process_map(gapfill=True, fileformat="nc", own_model=None)
   
To download the GPR processed map go to the `openEO portal <https://openeo.dataspace.copernicus.eu/>`_:

.. image:: https://github.com/user-attachments/assets/a869b60f-a420-4459-83ac-289c99758c8d
   :alt: download

You can use `QGIS <https://qgis.org/download/>`_ or `Panoply <https://www.giss.nasa.gov/tools/panoply/>`_ to visualize. 
IMPORTANT: The data range is off, due to few pixels being outliers.
Set the data range manually for the corresponding variable e.g. FVC --> 0 to 1.

.. image:: https://github.com/user-attachments/assets/6f2cc18c-1568-4aa5-a3d6-e028e69e361d
   :alt: map