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
   :special-members: __init__  # This explicitly shows the constructor 3(__init__)

Step-by-Step tutorial
---------------------

1. Go to `Google Earth Engine <https://earthengine.google.com/>`_ and register your account.
2. Open the GEE `Code Editor <https://code.earthengine.google.com/>`_ . We will connect the pyeogpr client to GEE now.
3. On the top right corner you should see the projectID of your account starting with "ee-..." This, you should copy in the projectID parameter (see Example below).
4. Top left corner go to "Assets" tab. Go to red "New" button, and create an ImageCollection. When created, copy its ImageCollection ID, and use it as your assetpath for mapping.
   (See process_map function in the Example below).
5. Now you are ready to go, Open up the command line, type "pip install pyeogpr". This will install the package.
6. Run pyeogpr as per your needs, you can test with the Example script.
7. Check the status of the process on: `Task manager <https://code.earthengine.google.com/tasks>`_



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
