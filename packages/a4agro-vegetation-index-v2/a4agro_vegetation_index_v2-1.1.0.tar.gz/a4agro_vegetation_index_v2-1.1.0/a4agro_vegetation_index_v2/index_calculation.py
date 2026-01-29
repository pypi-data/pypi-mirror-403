import json
import rasterio
import numpy as np

from .exceptions import InvalidImageException


class IndexCalculation:
    """
    # Contact:
        email: Jesus Aguirre @jaguirre@a4agro.com
        Github: JesusxAguirre


    # Class summary
       This algorithm consists in calculating vegetation indices, these
        indices can be used for precision agriculture for example (or remote
        sensing). There are functions to define the data and to calculate the
        implemented indices.

    # Vegetation index
        https://en.wikipedia.org/wiki/Vegetation_Index
        A Vegetation Index (VI) is a spectral transformation of two or more bands
        designed to enhance the contribution of vegetation properties and allow
        reliable spatial and temporal inter-comparisons of terrestrial
        photosynthetic activity and canopy structural variations

    # Information about channels (Wavelength range for each)
        * nir - near-infrared
            https://www.malvernpanalytical.com/br/products/technology/near-infrared-spectroscopy
            Wavelength Range 700 nm to 2500 nm
        * Red Edge
            https://en.wikipedia.org/wiki/Red_edge
            Wavelength Range 680 nm to 730 nm
        * red
            https://en.wikipedia.org/wiki/Color
            Wavelength Range 635 nm to 700 nm
        * blue
            https://en.wikipedia.org/wiki/Color
            Wavelength Range 450 nm to 490 nm
        * green
            https://en.wikipedia.org/wiki/Color
            Wavelength Range 520 nm to 560 nm


    # IMPORTANT
    this is a class especially uses form 8bands images from planet subscrition imagery sr

        Band 1 : coastal blue
        Band 2 : blue
        Band 3 : greenI
        band 4 : green
        Band 5 : yellow
        Band 6 : red
        Band 7 : RedEdge
        Band 8 : Near-Infrared



    """

    def __init__(
        self,
        image_file: str= None,
        udm_file: str = None,
    ):
        # Image, metadata
        self.image_file = image_file
       
        self.udm_file = udm_file


        # Bands

        self.band_red = None
        self.band_nir = None
        self.band_green = None
        self.band_greenI = None
        self.band_red = None
        self.band_redEdge = None
        self.band_swir1 = None
        self.band_swir2 = None

        # UDM BANDS
        self.shadow_band = None
        self.cloud_band = None

        # Vegetation indices
        self.ndvi = None
        self.ndwi = None
        self.gndvi = None
        self.cgi = None
        self.ndre = None

        # Json properties
        self.visible_percent = None
        self.cloud_percent = None





    def mask_index(self, index, mask):

        return np.ma.masked_array(index, mask)

    def calculate_ndvi(self):
        np.seterr(divide="ignore", invalid="ignore")
        self.ndvi = (self.band_nir.astype(float) - self.band_red.astype(float)) / (
            self.band_nir + self.band_red
        )
        return self.ndvi

    def calculate_ndwi(self):
        "(Float(nir) - Float(green)) / (Float(nir) + Float(green))"
        np.seterr(divide="ignore", invalid="ignore")
        
        if self.band_swir1 is not None:
            self.ndwi = (self.band_nir - self.band_swir1) / (
                self.band_nir + self.band_swir1
            )
            return self.ndwi
 
        self.ndwi = (self.band_nir - self.band_green) / (
            self.band_nir + self.band_green
        )
        return self.ndwi

    def calculate_gndvi(self):
        """
        Normalized Difference self.nir/self.green self.green NDVI
        https://www.indexdatabase.de/db/i-single.php?id=401
        :return: index
        
        (Float(nir) - Float(green)) / (Float(nir) + Float(green))
        """

        np.seterr(divide="ignore", invalid="ignore")
        self.gndvi = (self.band_nir - self.band_green) / (
            self.band_nir + self.band_green
        )



        return self.gndvi

    def calculate_cgi(self):
        "(Float(nir) / Float(greenI)) - 1"

        np.seterr(divide="ignore", invalid="ignore")
        self.cgi = (self.band_nir / self.band_green) - 1
        return self.cgi

    def calculate_ndre(self):
        "(Float(nir) - Float(redEdge)) / (Float(nir) + Float(redEdge))"

        np.seterr(divide="ignore", invalid="ignore")
        self.ndre = (self.band_nir - self.band_redEdge) / (
            self.band_nir + self.band_redEdge
        )
        return self.ndre

    def calculate_5_index(self) -> tuple:
        """This function calculates the five vegetation indices

        Returns:
            tuple: (ndvi, ndwi, gndvi, cgi, ndre)
        """

        if self.cloud_band.any() and self.shadow_band.any():
            mask = self.shadow_band + self.cloud_band
            self.ndvi = self.mask_index(self.calculate_ndvi(), mask)
            self.ndwi = self.mask_index(self.calculate_ndwi(), mask)
            self.gndvi = self.mask_index(self.calculate_gndvi(), mask)
            self.cgi = self.mask_index(self.calculate_cgi(), mask)
            self.ndre = self.mask_index(self.calculate_ndre(), mask)

            return (
                self.ndvi,
                self.ndwi,
                self.gndvi,
                self.cgi,
                self.ndre,
            )

        return (
            self.calculate_ndvi(),
            self.calculate_ndwi(),
            self.calculate_gndvi(),
            self.calculate_cgi(),
            self.calculate_ndre(),
        )



    def set_matricies(self, red, nir, green, redEdge, greenI = None, swir1 = None, swir2 = None, shadow = None, cloud = None):
        
        self.band_red = red
        self.band_nir = nir
        self.band_green = green
        self.band_redEdge = redEdge
        self.band_greenI = greenI
        self.band_swir1 = swir1
        self.band_swir2 = swir2
        
        # UDM BANDS
        self.shadow_band = shadow
        self.cloud_band = cloud

        return True