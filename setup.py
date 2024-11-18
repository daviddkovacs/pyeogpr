from setuptools import setup, find_packages
import os
readme_path = os.path.join(os.path.dirname(__file__), 'README.md')

setup(name="pyeogpr",
      version ="2.1.1",
      description="Python based library to use Earth Observation data to retrieve biophysical maps using Gaussian Process Regression",
      long_description=open(readme_path, 'r').read(),
      long_description_content_type='text/markdown',
      author = "Dávid D.Kovács",
      author_email = "daviddkovacs@gmail.com",
      packages = find_packages(),
      install_requires = ["numpy","openeo","scipy"])
