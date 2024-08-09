

.. pyeogpr documentation master file, created by
   sphinx-quickstart on Mon Jul 23 2024.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. image:: logo.png
   :scale: 50%

Welcome to pyeogpr's documentation!
====================================

.. image:: https://img.shields.io/pypi/v/pyeogpr.svg
    :target: https://pypi.org/project/pyeogpr/

.. image:: https://img.shields.io/badge/GitHub-pyeogpr-purple.svg
    :target: https://github.com/daviddkovacs/pyeogpr

.. image:: https://img.shields.io/badge/IPL-Flexinel-yellow
    :target: https://leoipl.uv.es/flexinel/
    :alt: Flexinel

Python based library to use Earth Observation data to retrieve biophysical maps using Gaussian Process Regression

Features
--------

- `Access`_ to **openEO** is required. Works best with the Copernicus Data Space Ecosystem.
- The package uses satellite observations and machine learning to infer biophyiscal maps.
- Get your maps in a few lines of code: select your region, temporal domain and satellite sensor to get the maps you are looking for!
- Built in gap filling to avoid cloud cover
- Runs "in the cloud" with the openEO API. No local processing needed.
- Resulting maps in .tiff or netCDF format

Installation
------------

You can install pyeogpr using pip:

.. code-block:: shell

    pip install pyeogpr

Usage
-----

Here is a basic example to get you started with pyeogpr:

.. code-block:: python

    

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
        
.. toctree::
   :maxdepth: 2
   :caption: Documentation

   pyeogpr

.. toctree::
   :maxdepth: 2
   :caption: Satellites and variables

   sensors
   


Contact
=======

Dávid D.Kovács - `daviddkovacs@gmail.com <mailto:daviddkovacs@gmail.com>`_

.. image:: flexinel.png
s

.. _Access: https://documentation.dataspace.copernicus.eu/Registration.html
