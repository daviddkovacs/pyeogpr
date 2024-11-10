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
