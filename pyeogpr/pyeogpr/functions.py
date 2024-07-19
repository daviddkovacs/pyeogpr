import openeo
import numpy as np
import scipy
import scipy.signal
# from udf.gpr import udf_gpr
# from udf.sgolay import udf_sgolay
import warnings
fn=1
class gpr_mapper:
    
    def __init__(self,sensor:str, bounding_box: list, temporal_extent: list, bands:np.array, cloudmask = False):
        
        self.connection = openeo.connect("https://openeo.dataspace.copernicus.eu").authenticate_oidc()
        print("""\n\n""")
        self.sensor = sensor
        self.bounding_box = bounding_box
        self.temporal_extent = temporal_extent
        self.bands = bands
        self.cloudmask = cloudmask
        self.spatial_extent = {"west": self.bounding_box[0], "south": self.bounding_box[1], "east": self.bounding_box[2], "north": self.bounding_box[3]}
        self.data = None
        self.masked_data = None
        self.gpr_cube = None
        self.gpr_cube_gapfilled = None
        
    def construct_datacube(self, composite=None, method=None):

        sensor = self.sensor
        if "SENTINEL2" in sensor:
            scale_factor = 0.0001
        else:
            scale_factor = 1

        spatial_extent = self.spatial_extent
        temporal_extent = self.temporal_extent
        bands = self.bands
        data = self.connection.load_collection(sensor,spatial_extent,temporal_extent,bands) * scale_factor
        self.data = data

        if self.cloudmask == True and "SENTINEL2" in self.sensor:
            
            print("Using Sentinel 2 Cloud Mask")
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
                print(f"Cloud masked, temporally composited datacube constructed: {composite} by {method} values. ")
                
            elif composite == None:
                
                self.masked_data = self.data.mask(mask)
                
        elif self.cloudmask == False and "SENTINEL2" in self.sensor:
            
            self.masked_data = self.data
            print(f"""Warning: You are not using the cloudmask \n{self.sensor} has a cloudmask, if you want to use it pass the 'cloudmask = True' argument""")
            
        else:
            print(f"{self.sensor} can't be masked")
    
    def process_map(self,biovar, gapfill = False):

        biovar_combos = {"SENTINEL2_L1C":["Cab","Cm","Cw","FVC","LAI","laiCab","laiCm","laiCw"],
                         "SENTINEL2_L2A":["CNC_Cab","CNC_Cprot"],
                         "SENTINEL3_OLCI_L1B": ["FAPAR","FVC","LAI","LCC"]}
        
        if biovar not in biovar_combos[self.sensor]:
            raise Exception(f"'{biovar}' not available for this satellite/sensor. Please select from: " +  str(biovar_combos[self.sensor]))
        
        print(f"Processing {self.sensor} based {biovar}")
        context = {"sensor": self.sensor,"biovar":biovar}
        
        self.gpr_cube = self.masked_data.apply_dimension(process=udf_gpr,
                                                         dimension="bands",
                                                         context =context).filter_bands(bands = ["B02"])
                   
        if gapfill == False:
            print("""----\nTo check the progress login to your openEO editor:\nhttps://openeo.dataspace.copernicus.eu/\n----""")
            
            self.gpr_cube.execute_batch(title=f"{self.sensor}_{biovar}",outputfile=f"{self.sensor}_{biovar}.nc",
                                        job_options = {'executor-memory': '10g','udf-dependency-archives': 
                                                       ['https://github.com/daviddkovacs/openEO/raw/main/Models/GPR_models_bulk.zip#tmp/venv']})
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