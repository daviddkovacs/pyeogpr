import openeo

# TODO: This UDF could be redifined to work with the Landsat 8 QA band
# right now it checks only the 6th bit of the QA band
# for example, cloud shadow is not considered

L8_cloud_qa = openeo.UDF("""
from openeo.udf import XarrayDataCube
import numpy as np

def reclassify_number(number):
    # Convert the 16-bit integer to binary representation
    binary_representation = np.binary_repr(number, width=16)
    # Check state of Bit 6 (first of two Cloud Confidence Bits)
    if binary_representation[6] == '1':
        return 1
    else:
        return 0

# Vectorize the function
vectorized_reclassify_number = np.vectorize(reclassify_number)

def apply_datacube(cube: XarrayDataCube, context: dict) -> XarrayDataCube:
    array = cube.get_array()
    temp_array = array.values.astype(np.uint16)
    
    # Apply the vectorized function to the array
    results_array = vectorized_reclassify_number(temp_array)

    array.values = results_array
    return cube
""")
