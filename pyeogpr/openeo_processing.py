import openeo
import numpy as np
import scipy.signal
import importlib.util
from pyeogpr.sensors import sensors_dict
from pyeogpr.udfgpr import udf_gpr, custom_model_import
from pyeogpr.udfsgolay import udf_sgolay


class Datacube:
    """

    pyeogpr.Datacube
    ----------------

        sensor : SENTINEL2_L1C, SENTINEL2_L2A, SENTINEL3_OLCI_L1B, SENTINEL3_SYN_L2_SYN
            Satellite sensor to process the data with.

        biovar : Biophysical variable to process. The selected variable's map will be retrieved.
            Currently "built-in" variables available for each sensor:

            ======================  =====================================================
            Satellite sensor        Available vegetation traits
            ======================  =====================================================
            SENTINEL2_L1C           Cab, Cm, Cw, FVC, LAI, laiCab, laiCm, laiCw
            SENTINEL2_L2A (no unc.) Cab, Cm, Cw, FVC, LAI, laiCab, laiCm, laiCw, CNC_Cab, CNC_Cprot,
                                    mangrove_LAI, mangrove_Cm, mangrove_Cw, mangrove_Cab
            SENTINEL3_OLCI_L1B      FAPAR, FVC, LAI, LCC
            SENTINEL3_SYN_L2_SYN    FAPAR, FVC
            ======================  =====================================================

            - for own model, simply put the directory of your model on your machine.

        bounding_box : list
            Your region of interest. Insert bbox as list. Can be selected from https://geojson.io/
            (e.g.: [-4.55, 42.73,-4.48, 42.77])

        temporal_extent : list
            Your temporal extent to be processed. (e.g.: ["2021-01-01", "2021-12-31"])

        cloudmask : Boolean
            If "True" the Sentinel 2 cloud mask will be applied (only to S2 data), with Gaussian convolution to have
            smoother edges when masking.


    """


    def __init__(self, sensor, biovar, bounding_box, temporal_extent, cloudmask=False, bands=None):
        self.connection = openeo.connect("https://openeo.dataspace.copernicus.eu").authenticate_oidc()
        self.sensor = sensor
        self.own_model = biovar if biovar.endswith(".py") else None
        self.biovar = "Own_variable" if self.own_model else biovar
        self.bounding_box = bounding_box
        self.temporal_extent = temporal_extent
        self.cloudmask = cloudmask
        self.sensors_dict = sensors_dict
        self.bands = bands or self.sensors_dict.get(sensor, {}).get("bandlist")
        self.scale_factor = None
        self.data = None
        self.masked_data = None
        self.gpr_cube = None
        self.gpr_cube_gapfilled = None
        self.models_url = "https://github.com/daviddkovacs/pyeogpr/raw/main/models/GPR_models_bulk.zip#tmp/venv"
        self.ex_memory = "2g"
        self.py_memory = "12g"
        self.spatial_extent = {
            "west": bounding_box[0],
            "south": bounding_box[1],
            "east": bounding_box[2],
            "north": bounding_box[3],
        }


    def _load_base_collection(self):
        scale = self.sensors_dict.get(self.sensor, {}).get("scale_factor", 0.0001)
        return self.connection.load_collection(
            self.sensor,
            spatial_extent=self.spatial_extent,
            temporal_extent=self.temporal_extent,
            bands=self.bands,
        ) * scale


    def _apply_s2_cloudmask(self, data):
        s2_cloudmask = self.connection.load_collection(
            "SENTINEL2_L2A", self.spatial_extent, self.temporal_extent, ["SCL"]
        )
        scl = s2_cloudmask.band("SCL")
        mask = ~((scl == 4) | (scl == 5))

        kernel = np.outer(
            scipy.signal.windows.gaussian(11, std=1.6),
            scipy.signal.windows.gaussian(11, std=1.6)
        )
        kernel /= kernel.sum()
        smoothed_mask = mask.apply_kernel(kernel) > 0.1

        return data.mask(smoothed_mask)


    def _load_custom_model(self):
        spec = importlib.util.spec_from_file_location("user_module", self.own_model)
        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)
        return custom_model_import(user_module)

    def _apply_gpr(self):
        if self.own_model:
            print("Applying user-defined model.")
            custom_udf = self._load_custom_model()
            return self.masked_data.apply_dimension(process=custom_udf, dimension="bands")
        else:
            print(f"Applying default GPR model: {self.biovar}")
            context = {"sensor": self.sensor, "biovar": self.biovar}
            result = (
                self.masked_data
                .apply_dimension(process=udf_gpr, dimension="bands", context=context)
                .filter_bands(bands=[self.bands[0], self.bands[1]])
                .rename_labels(
                    dimension="bands",
                    target=[f"{self.biovar}",f"{self.biovar}_unc"]
                )
            )
            return result

    def construct_datacube(self, composite=None):
        """
        Build the datacube with optional temporal compositing and cloud masking.

        Parameters
        ----------
        composite : str, optional
            Temporal compositing interval (e.g., 'month', 'dekad').
        """
        data = self._load_base_collection()

        if self.cloudmask and "SENTINEL2" in self.sensor:
            data = self._apply_s2_cloudmask(data)
            print("Applied Sentinel-2 cloud mask.")
        else:
            print(f"Cloud masking not applied or not supported for {self.sensor}.")

        if composite:
            data = data.aggregate_temporal_period(composite, "mean")
            print(f"Applied temporal compositing: {composite} by mean.")

        self.data = data
        self.masked_data = data
        print("Datacube constructed.")


    def process_map(self, gapfill=False, fileformat="tiff"):
        """
        Process the datacube into maps, by applying GPR algorithm on the spectral image stack.

        Parameters
        ----------
        gapfill : bool, default=False
            Apply Savitzky-Golay interpolator for gap filling.
        fileformat : str, default='tiff'
            Output file format ('nc' or 'tiff').
        """
        gpr_cube = self._apply_gpr()

        if gapfill:
            print("Applying Savitzky-Golay gapfilling.")
            gpr_cube_gapfilled = gpr_cube.apply_dimension(process=udf_sgolay, dimension="t")
            outputfile = f"{self.sensor}_{self.biovar}_GF.{fileformat}"
            title = f"{self.sensor} {self.biovar} gapfilled"
            cube_to_execute = gpr_cube_gapfilled
        else:
            outputfile = f"{self.sensor}_{self.biovar}.{fileformat}" if not self.own_model else "user_defined_product.{fileformat}"
            title = f"{self.sensor}_{self.biovar}" if not self.own_model else "User defined product"
            cube_to_execute = gpr_cube

        job_options = {"executor-memory": self.ex_memory,
                       "python-memory": self.py_memory}
        if not self.own_model:
            job_options["udf-dependency-archives"] = [self.models_url]

        cube_to_execute.execute_batch(
            title=title,
            outputfile=outputfile,
            job_options=job_options,
        )

        self.gpr_cube = gpr_cube
        if gapfill:
            self.gpr_cube_gapfilled = gpr_cube_gapfilled
