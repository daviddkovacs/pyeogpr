import openeo

test_udf = "Udf test passed"

udf_gpr = openeo.UDF(
    """

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



chunks = 128
def broadcaster(array,bands_from_model):
    return np.broadcast_to(array[:, np.newaxis, np.newaxis], (bands_from_model, chunks, chunks))


init_xr = xr.DataArray()
def apply_datacube(cube: xarray.DataArray, context: dict) -> xarray.DataArray:

    sensor = context["sensor"]
    variable = context["biovar"]
    model = globals()[sensor + "_" + variable]
    bands = len(model.mx_GREEN.ravel())

    hyp_ell_GREEN = broadcaster(model.hyp_ell_GREEN,bands)
    mx_GREEN = broadcaster(model.mx_GREEN.ravel(),bands)
    sx_GREEN = broadcaster(model.sx_GREEN.ravel(),bands)

    XDX_pre_calc_GREEN_broadcast = np.broadcast_to(model.XDX_pre_calc_GREEN.ravel()[:,np.newaxis,np.newaxis],(model.XDX_pre_calc_GREEN.shape[0],chunks,chunks))


    pixel_spectra = (cube.values)

    im_norm_ell2D_hypell  = ((pixel_spectra - mx_GREEN) / sx_GREEN) * hyp_ell_GREEN
    im_norm_ell2D  = ((pixel_spectra - mx_GREEN) / sx_GREEN)

    PtTPt = np.einsum('ijk,ijk->ijk', im_norm_ell2D_hypell, im_norm_ell2D) * (-0.5)
    PtTDX = np.einsum('ij,jkl->ikl', model.X_train_GREEN,im_norm_ell2D_hypell)
    arg1 = np.exp(PtTPt[0]) * model.hyp_sig_GREEN

    k_star_im = np.exp(PtTDX - (XDX_pre_calc_GREEN_broadcast * (0.5)))
    mean_pred = (np.einsum('ijk,i->jk',k_star_im, model.alpha_coefficients_GREEN.ravel()) * arg1) + model.mean_model_GREEN

    init_xr = np.clip(mean_pred, a_min=0, a_max=None)
    returned = xr.DataArray(init_xr)
    return returned
""",
    context={"from_parameter": "context"},
)


udf_gpr_customized = """

import importlib
import os
import sys
import time

from configparser import ConfigParser
from typing import Dict
from openeo.metadata import Band, CollectionMetadata
from openeo.udf import XarrayDataCube, inspect

import numpy as np
import xarray as xr
from pathlib import Path
from openeo.udf.debug import inspect

bands = len(np.array({mx_GREEN_placeholder}).ravel())
chunks = 128

def broadcaster(array):
    array = np.array(array)
    return np.broadcast_to(array[:, np.newaxis, np.newaxis], (bands, chunks, chunks))

#hyperparameters that need broadcasting

hyp_ell_GREEN = broadcaster(np.array({hyp_ell_GREEN_placeholder}))
mx_GREEN = broadcaster(np.array({mx_GREEN_placeholder}).ravel())
sx_GREEN = broadcaster(np.array({sx_GREEN_placeholder}).ravel())
XDX_pre_calc_GREEN_broadcast = np.broadcast_to(np.array({XDX_pre_calc_GREEN_placeholder}).ravel()[:,np.newaxis,np.newaxis],
                                               (np.array({XDX_pre_calc_GREEN_placeholder}).shape[0],chunks,chunks))

#hyperparameters that don't need broadcasting
X_train_GREEN = np.array({X_train_GREEN_placeholder})
hyp_sig_GREEN = np.array({hyp_sig_GREEN_placeholder})
alpha_coefficients_GREEN = np.array({alpha_coefficients_GREEN_placeholder})
mean_model_GREEN = {mean_model_GREEN_placeholder}

init_xr = xr.DataArray()
def apply_datacube(cube: xarray.DataArray, context: dict) -> xarray.DataArray:

    pixel_spectra = (cube.values)

    im_norm_ell2D_hypell  = ((pixel_spectra - mx_GREEN) / sx_GREEN) * hyp_ell_GREEN
    im_norm_ell2D  = ((pixel_spectra - mx_GREEN) / sx_GREEN)
    
    inspect(data=[im_norm_ell2D_hypell.dtype], message="im_norm_ell2D_hypell.dtype")
    inspect(data=[im_norm_ell2D.dtype], message="im_norm_ell2D.dtype")
    inspect(data=[hyp_ell_GREEN.dtype], message="hyp_ell_GREEN.dtype")
    
    inspect(data=[im_norm_ell2D_hypell.shape], message="im_norm_ell2D_hypell.shape")
    inspect(data=[im_norm_ell2D.shape], message="im_norm_ell2D.shape")
    inspect(data=[hyp_ell_GREEN.shape], message="hyp_ell_GREEN.shape")
    
    PtTPt = np.einsum('ijk,ijk->ijk', im_norm_ell2D_hypell.astype(np.float16), im_norm_ell2D.astype(np.float16)) * (-0.5)
    inspect(data=[PtTPt.shape], message="PtTPt.shape")
    PtTDX = np.einsum('ij,jkl->ikl', X_train_GREEN.astype(np.float16),im_norm_ell2D_hypell.astype(np.float16))
    arg1 = np.exp(PtTPt[0]) * hyp_sig_GREEN

    k_star_im = np.exp(PtTDX - (XDX_pre_calc_GREEN_broadcast * (0.5)))
    mean_pred = (np.einsum('ijk,i->jk',k_star_im.astype(np.float16), alpha_coefficients_GREEN.ravel().astype(np.float16)) * arg1.astype(np.float16)) + mean_model_GREEN

    init_xr = np.clip(mean_pred, a_min=0, a_max=None)
    returned = xr.DataArray(init_xr)
    return returned
"""


def custom_model_import(user_module):
    custom_gpr = udf_gpr_customized.format(
        hyp_ell_GREEN_placeholder=repr(user_module.hyp_ell_GREEN.tolist()),
        mx_GREEN_placeholder=repr(user_module.mx_GREEN.tolist()),
        sx_GREEN_placeholder=repr(user_module.sx_GREEN.tolist()),
        XDX_pre_calc_GREEN_placeholder=repr(user_module.XDX_pre_calc_GREEN.tolist()),
        X_train_GREEN_placeholder=repr(user_module.X_train_GREEN.tolist()),
        hyp_sig_GREEN_placeholder=repr(user_module.hyp_sig_GREEN),
        alpha_coefficients_GREEN_placeholder=repr(
            user_module.alpha_coefficients_GREEN.tolist()
        ),
        mean_model_GREEN_placeholder=repr(user_module.mean_model_GREEN),
    )

    custom_udf = openeo.UDF(custom_gpr)

    return custom_udf


# %%
