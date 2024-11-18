import openeo
import numpy as np
import scipy
import scipy.signal
import ee

import importlib.util
from pyeogpr.sensors import sensors_dict
from pyeogpr.udfgpr import udf_gpr, custom_model_import
from pyeogpr.udfsgolay import udf_sgolay
from pyeogpr.udf_L8_qa import L8_cloud_qa
import pyeogpr.udfgpr

class Datacube:
    """


    pyeogpr.Datacube
    ----------------

        sensor : SENTINEL2_L1C, SENTINEL2_L2A, SENTINEL3_OLCI_L1B
            Satellite sensor to process the data with.

        biovar : Biophysical variable to process. The selected variable's map will be retrieved.
            Currently "built-in" variables available for each sensor:

            - SENTINEL2_L1C: Cab, Cm, Cw, FVC, LAI, laiCab, laiCm, laiCw
            - SENTINEL2_L2A: Cab, Cm, Cw, FVC, LAI, laiCab, laiCm, laiCw, CNC_Cab, CNC_Cprot
            - SENTINEL3_OLCI_L1B: FAPAR, FVC, LAI, LCC

        bounding_box : list
            Your region of interest. Insert bbox as list. Can be selected from https://geojson.io/
            (e.g.: [-4.55, 42.73,-4.48, 42.77])

        temporal_extent : list
            Your temporal extent to be processed. (e.g.: ["2021-01-01", "2021-12-31"])

        cloudmask : Boolean
            If "True" the Sentinel 2 cloud mask will be applied (only to S2 data), with Gaussian convolution to have
            smoother edges when masking.
            
            
    """

    def __init__(
        self,
        sensor: str,
        biovar: str,
        bounding_box: list,
        temporal_extent: list,
        cloudmask=False,
        bands= None,
    ):
        self.connection = openeo.connect(
            "https://openeo.dataspace.copernicus.eu"
        ).authenticate_oidc()
        print("""\n\n""")
        self.sensor = sensor
        self.biovar = biovar
        self.bounding_box = bounding_box
        self.temporal_extent = temporal_extent
        self.cloudmask = cloudmask
        self.spatial_extent = {
            "west": self.bounding_box[0],
            "south": self.bounding_box[1],
            "east": self.bounding_box[2],
            "north": self.bounding_box[3],
        }
        self.sensors_dict = sensors_dict
        if bands == None:
            self.bands = self.sensors_dict[self.sensor]["bandlist"]
        if bands != None:
            self.bands = bands
        self.scale_factor = None
        self.data = None
        self.masked_data = None
        self.gpr_cube = None
        self.gpr_cube_gapfilled = None
        self.models_url = "https://github.com/daviddkovacs/pyeogpr/raw/main/models/GPR_models_bulk.zip#tmp/venv"

    def construct_datacube(self, composite=None):
        """


        Parameters
        ----------
        composite : "hour","day","dekad","week","season","month","year"
            Compositing temporal interval. The resulting maps will have the following temporal steps.
            For more information: https://processes.openeo.org/#aggregate_temporal_period



        Returns
        -------
        Datacube object containing user defined parameters and temporal compositing. This will be processed into an openEO datacube.

        """

        if self.sensor not in self.sensors_dict.keys():
            print("Sensor/satellite not available as default. Using user-defined sensor.")
            
        data = (
            self.connection.load_collection(
                self.sensor,
                self.spatial_extent,
                self.temporal_extent,
                self.bands,
            )
            * self.sensors_dict[self.sensor]["scale_factor"]
        )
        self.data = data
        print(self.data)
        if self.cloudmask == True and "SENTINEL2" in self.sensor:
            s2_cloudmask = self.connection.load_collection(
                "SENTINEL2_L2A", self.spatial_extent, self.temporal_extent, ["SCL"]
            )
            scl = s2_cloudmask.band("SCL")
            mask = ~((scl == 4) | (scl == 5))

            # Gaussian convolution to have a smooth edged cloud mask
            g = scipy.signal.windows.gaussian(11, std=1.6)
            kernel = np.outer(g, g)
            kernel = kernel / kernel.sum()
            mask = mask.apply_kernel(kernel)
            mask = mask > 0.1

            if composite != None:
                self.masked_data = self.data.aggregate_temporal_period(
                    composite, "mean"
                ).mask(mask)
                print(
                    f"Cloud masked, temporally composited datacube constructed: {composite} by mean values."
                )

            elif composite == None:
                self.masked_data = self.data.mask(mask)
                print("Cloud masked, datacube constructed")

        elif self.cloudmask == False and "SENTINEL2" in self.sensor:
            if composite != None:
                self.masked_data = self.data.aggregate_temporal_period(
                    composite, "mean"
                )
                print(
                    f"Temporally composited datacube constructed: {composite} by mean values. "
                )

            elif composite == None:
                self.masked_data = self.data
                print("Datacube constructed")

        elif self.cloudmask == True and "LANDSAT8_L2" in self.sensor:
            l8_qa = self.connection.load_collection(
                "LANDSAT8_L2", self.spatial_extent, self.temporal_extent, ["BQA"]
            )

            l8_cloudmask = l8_qa.apply(process=L8_cloud_qa)

            bqa = l8_cloudmask.band("BQA")
            mask = ~((bqa == 0))

            # apply kernel to mask without smoothing
            mask = mask > 0.1

            if composite != None:
                self.masked_data = self.data.aggregate_temporal_period(
                    composite, "mean"
                ).mask(mask)
                print(
                    f"Cloud masked, temporally composited datacube constructed: {composite} by mean values."
                )

            elif composite == None:
                self.masked_data = self.data.mask(mask)
                print("Cloud masked, datacube constructed")

        elif self.cloudmask == False and "LANDSAT8_L2" in self.sensor:
            if composite != None:
                self.masked_data = self.data.aggregate_temporal_period(
                    composite, "mean"
                )
                print(
                    f"Temporally composited datacube constructed: {composite} by mean values. "
                )

            elif composite == None:
                self.masked_data = self.data
                print("Datacube constructed")

        else:
            print(f"{self.sensor} can't be masked")

    def process_map(self, gapfill=False, fileformat="nc", own_model=None):
        """


        Parameters
        ----------

        gapfill : type, e.g. "Sgolay"
            To apply Savitzy Golay interpolator for cloud-induced gap 
            
        fileformat : string
                For netCDF4: "nc", for tiff: "tiff".
        
        own_model : dir
                Insert the dir of the model you developed with ARTMO. Just simply put the directory.
            

        """
        if self.biovar not in self.sensors_dict[self.sensor]["sensor_biovar"]:
            raise Exception(
                f"'{self.biovar}' not available for this satellite/sensor. Please select from: "
                + str(self.sensors_dict[self.sensor]["sensor_biovar"])
            )

        if gapfill == False:
            print(f"gapfill-> {str(gapfill)}")

            if own_model == None:
                print(f"own_model {str(own_model)}")

                context = {"sensor": self.sensor, "biovar": self.biovar}
                self.gpr_cube = self.masked_data.apply_dimension(
                    process=udf_gpr, dimension="bands", context=context
                ).filter_bands(bands=["B02"])

                self.gpr_cube.execute_batch(
                    title=f"{self.sensor}_{self.biovar}",
                    outputfile=f"{self.sensor}_{self.biovar}.{fileformat}",
                    job_options={
                        "executor-memory": "10g",
                        "udf-dependency-archives": [self.models_url],
                    },
                )
                return

            if own_model != None:
                print(f"own_model {str(own_model)}")

                spec = importlib.util.spec_from_file_location("user_module", own_model)
                user_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(user_module)
                # user_module = load_user_module(user_module_path)
                custom_udf = pyeogpr.udfgpr.custom_model_import(user_module)

                self.gpr_cube = self.masked_data.apply_dimension(
                    process=custom_udf, dimension="bands"
                ).filter_bands(bands=["B02"])

                self.gpr_cube.execute_batch(
                    title="User defined product",
                    outputfile=f"user_defined_product.{fileformat}",
                    job_options={"executor-memory": "10g"},
                )
                return

        elif gapfill == True:
            print(f"gapfill-> {str(gapfill)}")

            if own_model == None:
                print(f"own_model {str(own_model)}")

                context = {"sensor": self.sensor, "biovar": self.biovar}

                self.gpr_cube = self.masked_data.apply_dimension(
                    process=udf_gpr, dimension="bands", context=context
                ).filter_bands(bands=["B02"])

                self.gpr_cube_gapfilled = self.gpr_cube.apply_dimension(
                    process=udf_sgolay, dimension="t"
                )

                self.gpr_cube_gapfilled.execute_batch(
                    title=f"{self.sensor} {self.biovar} gapfill->{gapfill}",
                    outputfile=f"{self.sensor}_{self.biovar}_GF.{fileformat}",
                    job_options={
                        "executor-memory": "10g",
                        "udf-dependency-archives": [self.models_url],
                    },
                )
                return

            if own_model != None:
                print(f"own_model {str(own_model)}")

                spec = importlib.util.spec_from_file_location("user_module", own_model)
                user_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(user_module)
                # user_module = load_user_module(user_module_path)
                custom_udf = pyeogpr.udfgpr.custom_model_import(user_module)

                self.gpr_cube = self.masked_data.apply_dimension(
                    process=custom_udf, dimension="bands"
                ).filter_bands(bands=["B02"])

                self.gpr_cube_gapfilled = self.gpr_cube.apply_dimension(
                    process=udf_sgolay, dimension="t"
                )

                self.gpr_cube.execute_batch(
                    title="User defined product",
                    outputfile=f"user_defined_product.{fileformat}",
                    job_options={"executor-memory": "10g"},
                )
                return

        else:
            raise Exception(f"'{gapfill}' is not a valid smoother")
