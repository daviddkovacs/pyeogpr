import requests
import datetime
import ee


class EarthEngine:
    def __init__(
        self,
        sensor: str,
        biovar: str,
        bounding_box: list,
        temporal_extent: list,
        spatial_resolution: int,
        cloudmask=False,
    ):
        self.sensor = sensor
        self.biovar = biovar
        self.bbox = bounding_box
        self.temporal_extent = temporal_extent
        self.spatial_resolution = spatial_resolution
        self.cloudmask = cloudmask
        self.timeWindows = None
        self.assetpath = None
        self.gpr_model = None
        self.reducer = None

        ee.Authenticate()
        ee.Initialize()
        
        if self.sensor == "SENTINEL2_L1C":
            self.sensor = "COPERNICUS/S2_HARMONIZED"
            search_sensor = "SENTINEL2_L1C"
            
        if self.sensor == "SENTINEL2_L2A":
            self.sensor = "COPERNICUS/S2_SR_HARMONIZED"
            search_sensor = "SENTINEL2_L2A"
            
        if self.sensor == "SENTINEL3_L1B":
            self.sensor = "COPERNICUS/S3/OLCI"
            search_sensor = "SENTINEL3_L1B"
            
        self.imcol = ee.ImageCollection(self.sensor).filterDate(
            ee.Date(self.temporal_extent[0]), ee.Date(self.temporal_extent[1])
        )

        url = f"https://raw.githubusercontent.com/daviddkovacs/pyeogpr/refs/heads/main/models/{search_sensor}_{self.biovar}_GEE.py"

        response = requests.get(url)

        with open("model_imported.py", "w") as f:
            f.write(response.text)

        import model_imported

        self.model_imported = model_imported

    def construct_datacube(self, composite=None):
        self.timeWindows = composite
        print(f"Temporal composites: {self.timeWindows} days")

    def process_map(self, assetpath=None):
        self.assetpath = assetpath
        print(self.assetpath)

        # print(f"Check progress on: https://code.earthengine.google.com/tasks")
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
            .filterBounds(
                ee.FeatureCollection(
                    ee.Geometry.BBox(
                        self.bbox[0], self.bbox[1], self.bbox[2], self.bbox[3]
                    )
                )
            )
            .map(self.maskS3badPixels)
            .select(model.bands)  # .cast(model.bands_dict, model.bands)
            .max()
            .clipToCollection(
                ee.FeatureCollection(
                    ee.Geometry.BBox(
                        self.bbox[0], self.bbox[1], self.bbox[2], self.bbox[3]
                    )
                )
            )
        )
        # .clip(fc));

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
            bare_cover = ee.Image("COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019").select('bare-coverfraction').lte(90);
            lakes = ee.Image("COPERNICUS/Landcover/100m/Proba-V-C3/Global/2019").select('discrete_classification').eq(80)
            lakemask = lakes.eq(0);
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

            # Export the image to an asset
            exportar = ee.batch.Export.image.toAsset(
                assetId = self.assetpath
                + "/"
                + self.getInputDates(i)["fecha_str"]
                + "_"
                + self.biovar,
                image=image_export,
                maxPixels=17210617060,
                description=self.getInputDates(i)["fecha_str"] + "_" + self.biovar,
                scale=self.spatial_resolution,
                region=ee.Geometry.BBox(
                    self.bbox[0], self.bbox[1], self.bbox[2], self.bbox[3]
                ),  # .bounds().getInfo()['coordinates']
            )
            exportar.start()
            exportar.status()
