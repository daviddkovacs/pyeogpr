PyEOGPR
========

**PyEOGPR** allows you to perform Gaussian Process Regression (GPR) on biophysical trait maps, using either of two back-ends—Google Earth Engine or openEO. Select the back-end that suits your needs; both are designed with user-friendly syntax.

Available Back-ends:
---------------------

- **Google Earth Engine (GEE)**: `EarthEngine documentation <earthengine.html>
- **openEO**: `openEO documentation <openeo.html>


Google Earth Engine (GEE) Back-end
-----------------------------------

.. autoclass:: pyeogpr.EarthEngine
   :members:
   :undoc-members:
   :show-inheritance:
   :exclude-members: maploop,getInputDates,calculate_GREEN,addVariables,maskS3badPixels,sequence_GREEN
   :special-members: __init__  # This explicitly shows the constructor (__init__)

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
   

openEO Back-end
-----------------

.. autoclass:: pyeogpr.Datacube  
   :members:
   :undoc-members:
   :show-inheritance:

Example:
--------

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