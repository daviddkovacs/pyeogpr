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

.. image:: https://img.shields.io/badge/DOI-10.5281%2Fzenodo.13373838-blue
    :target: https://doi.org/10.5281/zenodo.13373838
    :alt: Zenodo DOI


Python based library to use Earth Observation data to retrieve biophysical maps using Gaussian Process Regression

Features
--------

- Access to `openEO <https://documentation.dataspace.copernicus.eu/Registration.html>`_ or `Google Earth Engine <https://earthengine.google.com/>`_ is required.
- Advantages of **openEO**: Download locally netcdf or tiff format. no uncertainty estimates, smaller areas
- Advantages of **Google Earth Engine**: Export to ee.Assets with Uncertainty estimates, and up to global scale processing. 
- The package uses satellite observations and machine learning to create vegetation trait maps
- Get your maps in a few lines of code: no Machine Learning, coding or remote sensing knowledge needed!
- Built in gap filling to avoid cloud cover
- Runs "in the cloud" with the GEE/openEO API. No local processing needed.


Installation
------------

You can install pyeogpr using pip via the command line:

.. code-block:: shell

    pip install pyeogpr

Usage
-----

Please refer to the documentation to use either GEE or openEO based processing.
        
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

