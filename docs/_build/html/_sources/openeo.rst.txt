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

    import pyeogpr

    bounding_box = [
        17.897539591074604,
        46.59810244496674,
        17.96594608650338,
        46.639078751019014
      ]

    time_window = ["2020-07-01", "2020-07-10"]

    dc = pyeogpr.Datacube(
        "SENTINEL2_L1C",
        "Cm",
        bounding_box,
        time_window,
        cloudmask=False)

    dc.construct_datacube("dekad")

    dc.process_map(gapfill=False, fileformat="tiff")
   
To download the GPR processed map go to the `openEO portal <https://openeo.dataspace.copernicus.eu/>`_:

.. image:: https://github.com/user-attachments/assets/a869b60f-a420-4459-83ac-289c99758c8d
   :alt: download

You can use `QGIS <https://qgis.org/download/>`_ or `Panoply <https://www.giss.nasa.gov/tools/panoply/>`_ to visualize. 
IMPORTANT: The data range is off, due to few pixels being outliers.
Set the data range manually for the corresponding variable e.g. FVC --> 0 to 1.

.. image:: https://github.com/user-attachments/assets/6f2cc18c-1568-4aa5-a3d6-e028e69e361d
   :alt: map