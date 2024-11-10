import requests
import datetime
import ee
import os
import importlib
import sys
from io import StringIO

class EarthEngine:
    """


    pyeogpr.EarthEngine
    --------------------

        projectID : string
                    Your GEE projectID. Usually starts with "ee-...". You can find it next to your
                    profile picture, top right corner on: https://code.earthengine.google.com

        sensor :    string
            Satellite sensor to use.
            You can search for it on: https://developers.google.com/earth-engine/datasets/catalog
            Insert the string, as you would find it on the GEE catalog site:
            for example: "COPERNICUS/S3/OLCI" or "LANDSAT/LC08/C02/T1_L2"

        biovar :    string
            Biophysical variable to process.

            Currently "built-in" variables available for each sensor:

            - SENTINEL2_L1C: Cab, Cm, Cw, FVC, LAI, laiCab, laiCm, laiCw
            - SENTINEL2_L2A: Cab, Cm, Cw, FVC, LAI, laiCab, laiCm, laiCw, CNC_Cab, CNC_Cprot
            - SENTINEL3_OLCI_L1B: FAPAR, FVC, LAI, LCC

            If you have your own model trained with ARTMO (https://artmotoolbox.com), you need to
            insert the directory of the model, for example: r"C:/User/Models/My_custom_model.py"
            These models need to be in ".py" format, in order to achieve it, please consult:
            https://github.com/SentiFLEXinel/ARTMOtoGEE/

        bounding_box : list, ee.assetpath
            Your region of interest. Insert bbox as list. Can be selected from https://geojson.io/
            (e.g.: [-4.55, 42.73,-4.48, 42.77]).
            Alternatively, you can insert shapefiles, that are already uploaded to your GEE assets.
            Just copy the ee.assetpath which stores your SHP shapefile that you already uploaded to GEE.

        temporal_extent : list
            Your temporal extent to be processed. (e.g.: ["2021-01-01", "2021-12-31"])

        spatial_resolution : int
            Spatial resolution of the exported data. Value in meters.

        cloudmask : Boolean
            If set to "True", cloud masking will be done for Sentinel 2 and 3 sensors. Defaults to False.


    """

    def __init__(
        self,
        projectID,
        sensor,
        biovar,
        bounding_box,
        temporal_extent,
        spatial_resolution,
        cloudmask=False,
    ):
        self.projectID = projectID
        # EE Auth
        ee.Authenticate()
        ee.Initialize(project=self.projectID)

        self.sensor = sensor
        if self.sensor == "SENTINEL2_L1C" or "COPERNICUS/S2_HARMONIZED":
            self.sensor = "COPERNICUS/S2_HARMONIZED"
            search_sensor = "SENTINEL2_L1C"

        if self.sensor == "SENTINEL2_L2A" or "COPERNICUS/S2_SR_HARMONIZED":
            self.sensor = "COPERNICUS/S2_SR_HARMONIZED"
            search_sensor = "SENTINEL2_L2A"

        if self.sensor == "SENTINEL3_L1B" or "COPERNICUS/S3/OLCI":
            self.sensor = "COPERNICUS/S3/OLCI"
            search_sensor = "SENTINEL3_L1B"

        if biovar[-3:] == ".py":
            self.custom_model = biovar
            self.biovar = biovar.split("\\")[-1].split(".")[0]

        else:
            self.biovar = biovar

        if type(bounding_box) is list:  # To accept GeoJSON bbox
            self.bbox = ee.Geometry.BBox(
                bounding_box[0], bounding_box[1], bounding_box[2], bounding_box[3]
            )
        if "projects/ee-" in bounding_box:  # So it accepts shps too!
            self.bbox = ee.FeatureCollection(bounding_box)
            # self.bbox_fc2geo = ee.FeatureCollection(bounding_box).geometry()
            
        self.temporal_extent = temporal_extent
        self.spatial_resolution = spatial_resolution
        self.cloudmask = cloudmask
        self.timeWindows = None
        self.assetpath = None
        self.gpr_model = None
        self.reducer = None

        # User defined or default models import
        if biovar[-3:] == ".py":
            self.custom_model = biovar
            spec = importlib.util.spec_from_file_location(biovar, self.custom_model)
            user_module = importlib.util.module_from_spec(spec)
            sys.modules["user_module"] = user_module
            spec.loader.exec_module(user_module)

            self.model_imported = user_module
            print(self.model_imported.hyp_sig0_GREEN)

        else:
            url = f"https://raw.githubusercontent.com/daviddkovacs/pyeogpr/refs/heads/main/models/{search_sensor}_{self.biovar}_GEE.py"
            print(url)
            response = requests.get(url)

            with open("model_imported.py", "w") as f:
                f.write(response.text)

            if "model_imported" in sys.modules:
                del sys.modules["model_imported"]  # We do this to flush existing modules
            import model_imported

            self.model_imported = model_imported
            print(model_imported.hyp_sig0_GREEN)

        self.imcol = ee.ImageCollection(self.sensor).filterDate(
            ee.Date(self.temporal_extent[0]), ee.Date(self.temporal_extent[1])
        )

    def construct_datacube(self, composite=None):
        """

        composite :  Defaults to None
            The algorithm creates temporal composites, according to the number of days you assign.
            The temporal composites need to be 1 day smaller than the defined temporal_extent.
        """
        self.timeWindows = composite
        print(f"Temporal composites: {self.timeWindows} days")

        dif = (
            datetime.datetime.strptime(self.temporal_extent[1], "%Y-%m-%d").toordinal()
            - datetime.datetime.strptime(
                self.temporal_extent[0], "%Y-%m-%d"
            ).toordinal()
        )
        if dif <= composite:
            raise ValueError(
                f"Temporal composite ({str(composite)} days)  has to be shorter than defined temporal_extent"
            )

    def process_map(self, assetpath=None):
        """

        assetpath: str
            You need to define, which GEE asset (ImageCollection) you would want the maps to be exported to.
            To create your asset, go to top left corner on: https://code.earthengine.google.com/
            You will find three tabs: Scripts, Docs and Assets. Go to Assets and create a new ImageCollection.
            When you created your ImageCollection, copy its ID as a string and assign it to assetpath. If left blank, the script will automatically generate you a default asset.

        """

        if assetpath == None:
            assetpath = f"projects/{self.projectID}/assets/PyEOGPR_{self.biovar}"
            ee.data.createAsset({"type": "ImageCollection"}, assetpath)
            print(f"Assetpath NOT DEFINED:\nExporting to default EE asset: {assetpath}")
        else:
            print(f"Exporting to {assetpath}")
        self.assetpath = assetpath
        self.maploop()

    def sequence_GREEN(self, variable):
        # print(variable)  # Later this probably needs to be changed to select model
        sequence_GREEN = []
        model = self.model_imported
        for i in range(0, model.XTrain_dim_GREEN):
            sequence_GREEN.append(str(i))
        return sequence_GREEN

    def getInputDates(self, i):
        fecha_inicio = ee.Date(self.temporal_extent[0]).advance(
            ee.Number(i).multiply(self.timeWindows), "day"
        )
        fecha_fin = fecha_inicio.advance(self.timeWindows, "day")
        # fecha_fin = endDateGEE()
        fecha_str = datetime.datetime.utcfromtimestamp(
            fecha_inicio.getInfo()["value"] / 1000.0
        ).strftime("%Y%m%d")
        return {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "fecha_str": fecha_str,
        }

    def maskS3badPixels(self, image):
        qa = ee.Image(image.select("quality_flags"))
        coastLine = 1 << 30
        inLandWater = 1 << 29
        bright = 1 << 27
        invalid = 1 << 25
        Oa12Sat = 1 << 9
        mask = (
            qa.bitwiseAnd(coastLine)
            .eq(0)
            .And(qa.bitwiseAnd(inLandWater).eq(0))
            .And(qa.bitwiseAnd(bright).eq(0))
        )
        return image.updateMask(mask)

    def addVariables(image):
        date = ee.Date(image.get("system:time_start"))
        years = date.difference(ee.Date("1970-01-01"), "days")
        return image.addBands(ee.Image(years).rename("t").int())

    def calculate_GREEN(self, fecha_inicio, fecha_fin, variable):
        model = self.model_imported
        image = ee.Image(
            self.imcol.filterDate(fecha_inicio, fecha_fin)
            .filterBounds(ee.FeatureCollection(self.bbox))
            .map(self.maskS3badPixels)
            .select(model.bands)  # .cast(model.bands_dict, model.bands)
            .max()
            .clipToCollection(ee.FeatureCollection(self.bbox))
        )
        # .clip(fc));
        # TODO: I should play around with this .clip() here..
        im_norm_ell2D_hypell = (
            image.subtract(model.mx_GREEN)
            .divide(model.sx_GREEN)
            .multiply(model.hyp_ell_GREEN)
            .toArray()
            .toArray(1)
        )
        im_norm_ell2D = (
            image.subtract(model.mx_GREEN).divide(model.sx_GREEN).toArray().toArray(1)
        )
        PtTPt = (
            im_norm_ell2D_hypell.matrixTranspose()
            .matrixMultiply(im_norm_ell2D)
            .arrayProject([0])
            .multiply(-0.5)
        )

        PtTDX = (
            ee.Image(model.X_train_GREEN)
            .matrixMultiply(im_norm_ell2D_hypell)
            .arrayProject([0])
            .arrayFlatten([self.sequence_GREEN(self.biovar)])
        )
        arg1 = PtTPt.exp().multiply(model.hyp_sig0_GREEN)

        k_star = PtTDX.subtract(model.XDX_pre_calc_GREEN.multiply(0.5)).exp().toArray()
        mean_pred = k_star.arrayDotProduct(
            model.alpha_coefficients_GREEN.toArray()
        ).multiply(arg1)
        mean_pred = mean_pred.toArray(1).arrayProject([0]).arrayFlatten([[self.biovar]])
        mean_pred = mean_pred.add(model.mean_model_GREEN)
        filterDown = mean_pred.gt(0)

        mean_pred = mean_pred.multiply(filterDown)

        k_star_uncert = (
            PtTDX.subtract(model.XDX_pre_calc_GREEN.multiply(0.5))
            .exp()
            .multiply(arg1)
            .toArray()
        )
        Vvector = (
            ee.Image(model.LMatrixInverse)
            .matrixMultiply(k_star_uncert.toArray(0).toArray(1))
            .arrayProject([0])
        )
        Variance = (
            ee.Image(model.hyp_sig_GREEN)
            .toArray()
            .subtract(Vvector.arrayDotProduct(Vvector))
            .abs()
            .sqrt()
        )
        Variance = (
            Variance.toArray(1)
            .arrayProject([0])
            .arrayFlatten([[self.biovar + "_UNCERTAINTY"]])
        )

        image = image.addBands(mean_pred)
        image = image.addBands(Variance)

        return image.select(self.biovar, self.biovar + "_UNCERTAINTY")

    def maploop(self):
        startDate = datetime.datetime.strptime(
            self.temporal_extent[0], "%Y-%m-%d"
        ).date()
        daysIterations = abs(
            (
                startDate
                - datetime.datetime.strptime(self.temporal_extent[1], "%Y-%m-%d").date()
            )
            // self.timeWindows
        ).days

        for i in range(0, daysIterations):
            print(self.getInputDates(i)["fecha_str"])

            imageHolder = ee.Image().set(
                "system:time_start",
                ee.Date(self.temporal_extent[0])
                .advance(ee.Number(i).multiply(self.timeWindows), "days")
                .millis(),
            )

            imagen = self.calculate_GREEN(
                self.getInputDates(i)["fecha_inicio"],
                self.getInputDates(i)["fecha_fin"],
                self.biovar,
            )  # .multiply(10000).toInt32()
            imageHolder = imageHolder.addBands(imagen)
            image_export = imageHolder.select(self.biovar, self.biovar + "_UNCERTAINTY")

            # Optional masking
            bare_cover = (
                ee.Image("COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019")
                .select("bare-coverfraction")
                .lte(90)
            )
            lakes = (
                ee.Image("COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019")
                .select("discrete_classification")
                .eq(80)
            )
            lakemask = lakes.eq(0)
            image_export = image_export.mask(lakemask)
            image_export = image_export.mask(bare_cover)

            # Convert to uint8 for lower memory usage
            # image_export = image_export.multiply(255 / data_range).uint8()
            image_export = image_export.set(
                "system:time_start",
                ee.Date(self.temporal_extent[0])
                .advance(ee.Number(i).multiply(self.timeWindows), "days")
                .millis(),
            )

            # SHP-bbox misery
            region = None
            if type(self.bbox) is list:
                region=self.bbox
            elif isinstance(self.bbox, ee.FeatureCollection):
                region = self.bbox.geometry()
                
            # Export the image to an asset
            exportar = ee.batch.Export.image.toAsset(
                assetId=self.assetpath
                + "/"
                + self.getInputDates(i)["fecha_str"]
                + "_"
                + self.biovar,
                image=image_export,
                maxPixels=17210617060,
                description=self.getInputDates(i)["fecha_str"] + "_" + self.biovar,
                scale=self.spatial_resolution,
                region = region,  # .bounds().getInfo()['coordinates']
            )
            exportar.start()
            exportar.status()
