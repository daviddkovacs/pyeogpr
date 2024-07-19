from setuptools import setup, find_packages

setup(name="pyeogpr",
      version ="0.1",
      author = "Dávid D.Kovács",
      author_email = "daviddkovacs@gmail.com",
      packages = find_packages(include=["pyeogpr","pyeogpr.*"]),
      install_requires = ["numpy","openeo","scipy"])