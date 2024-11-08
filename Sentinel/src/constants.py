from enum import Enum, unique

@unique
class S2_Bands(Enum):
    COASTAL_AEROSOL = 'B01'
    BLUE = 'B02'
    GREEN = 'B03'
    RED = 'B04'
    RED_EDGE_1 = 'B05'
    RED_EDGE_2 = 'B06'
    RED_EDGE_3 = 'B07'
    NIR = 'B08'
    NARROW_NIR = 'B08A'
    WATER_VAPOUR = 'B09'
    CIRRUS = 'B10'
    SWIR_1 = 'B11'
    SWIR_2 = 'B12'
    AEROSOL_OPTICAL_THICKNESS = 'AOT'
    SCENE_CLASSIFICATION_DATA = 'SCL'
    SNOW_PROBABILITY = 'SNW'
    CLOUD_PROBABILITY = 'CLD'
    
    @classmethod
    def true_color_bands(cls) -> list[str]:
        return [cls.RED.value, cls.GREEN.value, cls.BLUE.value]
    
    @classmethod
    def false_color_bands(cls) -> list[str]:
        return [cls.NIR.value, cls.GREEN.value, cls.BLUE.value]
    
    @classmethod
    def swir_bands(cls) -> list[str]:
        return [cls.SWIR_2.value, cls.NIR.value, cls.RED.value]
    
    @classmethod
    def agriculture_bands(cls) -> list[str]:
        return [cls.SWIR_1.value, cls.NIR.value, cls.BLUE.value]
    
    @classmethod
    def geology_bands(cls) -> list[str]:
        return [cls.SWIR_2.value, cls.SWIR_1.value, cls.BLUE.value]
    
    @classmethod
    def bathimetric_bands(cls) -> list[str]:
        return [cls.RED.value, cls.GREEN.value, cls.COASTAL_AEROSOL.value]