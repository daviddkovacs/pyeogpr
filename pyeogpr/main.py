import openeo
import numpy as np
import scipy
import scipy.signal
from src.pyeogpr.sensors import sensors_dict
from src.pyeogpr.udfgpr import udf_gpr
from src.pyeogpr.udfsgolay import udf_sgolay

class Datacube:
    
    def __init__(self,sensor:str, bounding_box: list, temporal_extent: list, cloudmask = False):
        
        self.connection = openeo.connect("https://openeo.dataspace.copernicus.eu").authenticate_oidc()
        print("""\n\n""")
        self.sensor = sensor
        self.bounding_box = bounding_box
        self.temporal_extent = temporal_extent
        self.cloudmask = cloudmask
        self.spatial_extent = {"west": self.bounding_box[0], "south": self.bounding_box[1], "east": self.bounding_box[2], "north": self.bounding_box[3]}
        self.sensors_dict = sensors_dict  
        self.bands = None
        self.scale_factor = None
        self.data = None
        self.masked_data = None
        self.gpr_cube = None
        self.gpr_cube_gapfilled = None

        
    def construct_datacube(self, composite=None, method=None):
        """
        

        Parameters
        ----------
        composite : TYPE, string
            Compositing temporal interval. The resulting maps will have the following temporal steps use: "hour","day","dekad","week","season","month","year"
            for more information visit: https://processes.openeo.org/#aggregate_temporal_period
        
        method : TYPE, string
            Type of reducer to use when aggregating temporal periods. A reducer to be applied for the values contained in each period. 
            A reducer is a single process such as mean or a set of processes, which computes a single value for a list of values, see the category 'reducer' for such processes.

        Raises
        ------
        Exception
            DESCRIPTION.

        Returns
        -------
        Datacube object containing user defined parameters. This will be processed into an openEO datacube.

        """
        if self.sensor not in self.sensors_dict.keys():
            raise Exception("Sensor/satellite not available.")
                
        data = self.connection.load_collection(self.sensor,
                                               self.spatial_extent,
                                               self.temporal_extent,
                                               self.sensors_dict[self.sensor]["bandlist"]) * self.sensors_dict[self.sensor]["scale_factor"]
        self.data = data
        print(self.data)
        if self.cloudmask == True and "SENTINEL2" in self.sensor:

            s2_cloudmask = self.connection.load_collection("SENTINEL2_L2A",self.spatial_extent, self.temporal_extent, ["SCL"])
            scl = s2_cloudmask.band("SCL")
            mask = ~((scl == 4) | (scl == 5))
            
            #Gaussian convolution to have a smooth edged cloud mask
            g = scipy.signal.windows.gaussian(11, std=1.6)
            kernel = np.outer(g, g)
            kernel = kernel / kernel.sum()
            mask = mask.apply_kernel(kernel)
            mask = mask > 0.1

            if composite != None:
                
                self.masked_data = self.data.aggregate_temporal_period(composite,method).mask(mask)
                print(f"Cloud masked, temporally composited datacube constructed: {composite} by {method} values.")
                
            elif composite == None:
                
                self.masked_data = self.data.mask(mask)
                print("Cloud masked, datacube constructed")
                
        elif self.cloudmask == False and "SENTINEL2" in self.sensor:
            
            if composite != None:
                
                self.masked_data = self.data.aggregate_temporal_period(composite,method)
                print(f"Temporally composited datacube constructed: {composite} by {method} values. ")
                
            elif composite == None:
                
                self.masked_data = self.data
                print("Datacube constructed")

        else:
            print(f"{self.sensor} can't be masked")
    
    def process_map(self, biovar, gapfill = False):
        """
        

        Parameters
        ----------
        biovar : string
            Biophysical varaiable to process. Check the available ones for your sensor/satellite of choice: https://pypi.org/project/pyeogpr/
        gapfill : Boolen, optional
            Set to "True" if you want to apply Savitzy Golay interpolator for cloud induced gap filling

        Returns
        -------
        Starts the openEO based GPR processing of the biophsycal maps.

        """
        if biovar not in self.sensors_dict[self.sensor]["sensor_biovar"]:
            raise Exception(f"'{biovar}' not available for this satellite/sensor. Please select from: " +  str(self.sensors_dict[self.sensor]["sensor_biovar"]))
        
        print(f"Processing {self.sensor} based {biovar}")
        
        context = {"sensor": self.sensor,"biovar":biovar}
        
        self.gpr_cube = self.masked_data.apply_dimension(process=udf_gpr,
                                                         dimension="bands",
                                                         context =context).filter_bands(bands = ["B02"])
                   
        if gapfill == False:
            
            print("""----\nTo check the progress login to your openEO editor:\nhttps://openeo.dataspace.copernicus.eu/\n----""")
            self.gpr_cube.execute_batch(title=f"{self.sensor}_{biovar}",outputfile=f"{self.sensor}_{biovar}.nc",
                                        job_options = {'executor-memory': '10g','udf-dependency-archives': 
                                                       ['https://github.com/daviddkovacs/openeo_models/raw/main/GPR_models_bulk.zip#tmp/venv']})
        #TODO: implement Whittaker smoother
        elif gapfill == "Sgolay":
            print("Smoother: Savitzky-Golay")
            self.gpr_cube_gapfilled = self.gpr_cube.apply_dimension(process=udf_sgolay, dimension="t")

            self.gpr_cube_gapfilled.execute_batch(title=f"{self.sensor} {biovar} {gapfill}", outputfile=f"{self.sensor}_{biovar}_GF.nc",
                                                  job_options={'executor-memory': '10g', 'udf-dependency-archives': 
                                                                ['https://github.com/daviddkovacs/openEO/raw/main/Models/GPR_models_bulk.zip#tmp/venv']})
        else:
            raise Exception(f"'{gapfill}' is not a valid smoother")
   
        #TODO: Download local. currently giving error 403