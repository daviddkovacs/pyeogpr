import openeo
gpr_string = "this is gpr"
udf_gpr = openeo.UDF("""

import importlib
import os
import sys
import time

dir_path = 'tmp/venv'
sys.path.insert(0, dir_path)

python_files = [f[:-3] for f in os.listdir(dir_path) if f.endswith('.py') and f !="__init__.py"]

for lib in python_files:
    globals()[lib] = __import__(lib)

from configparser import ConfigParser
from typing import Dict
from openeo.metadata import Band, CollectionMetadata
from openeo.udf import XarrayDataCube, inspect

import numpy as np
import xarray as xr
from pathlib import Path
from openeo.udf.debug import inspect

def broadcaster(array):
    return np.broadcast_to(array[:, np.newaxis, np.newaxis], (10, 256, 256))
    #TODO: use function to obtain x,ydim instead of hard coding 256
init_xr = xr.DataArray()
def apply_datacube(cube: xarray.DataArray, context: dict) -> xarray.DataArray:

    sensor = context["sensor"]
    variable = context["biovar"]
    model = globals()[sensor + "_" + variable]

    hyp_ell_GREEN = broadcaster(model.hyp_ell_GREEN)
    mx_GREEN = broadcaster(model.mx_GREEN.ravel())
    sx_GREEN = broadcaster(model.sx_GREEN.ravel())
    XDX_pre_calc_GREEN_broadcast = np.broadcast_to(model.XDX_pre_calc_GREEN.ravel()[:,np.newaxis,np.newaxis],(model.XDX_pre_calc_GREEN.shape[0],256,256))

    pixel_spectra = (cube.values)

    im_norm_ell2D_hypell  = ((pixel_spectra - mx_GREEN) / sx_GREEN) * hyp_ell_GREEN
    im_norm_ell2D  = ((pixel_spectra - mx_GREEN) / sx_GREEN)

    PtTPt = np.einsum('ijk,ijk->ijk', im_norm_ell2D_hypell, im_norm_ell2D) * (-0.5)
    PtTDX = np.einsum('ij,jkl->ikl', model.X_train_GREEN,im_norm_ell2D_hypell)
    arg1 = np.exp(PtTPt[0]) * model.hyp_sig_GREEN

    k_star_im = np.exp(PtTDX - (XDX_pre_calc_GREEN_broadcast * (0.5)))
    mean_pred = (np.einsum('ijk,i->jk',k_star_im, model.alpha_coefficients_GREEN.ravel()) * arg1) + model.mean_model_GREEN

    init_xr = mean_pred
    returned = xr.DataArray(init_xr)
    return returned
""",context={"from_parameter": "context"})


