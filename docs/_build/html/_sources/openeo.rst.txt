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