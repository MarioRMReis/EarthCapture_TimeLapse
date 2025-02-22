
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
# warning spam prevention, huggingface 0.25 needed

import ee
import os 
import argparse
from datetime import datetime, date, timedelta
from utils import geometry, kml_handler, data_validation
from satelite import landsat, sentinel

def get_argparser():
    parser = argparse.ArgumentParser()

    parser.add_argument("--save_folder", type=str, default="results", 
                        help="Path to save the EarthEngine images and the corresponding masks.")
    parser.add_argument("--start_date", type=str, default=(str(date.today() - timedelta(days=64))), 
                        help="Format: YYYY-MM-DD, \nStarting date from witch we are going to start requesting images")
    parser.add_argument("--end_date", type=str, default=(str(date.today())), 
                        help="Format: YYYY-MM-DD, \nEnding date from witch we are going sto stop requesting images")
    parser.add_argument("--window_size", type=int, default=128, 
                        help="Options: 128, 256, 512, 1024. You can pick any resolution but keep and mind the area of your region, should be greater than 64.")
    parser.add_argument("--satelites", type=str, default="Sentinel-2, LANDSAT", 
                        help="Options: SENTINEL, [Sentinel-1, Sentinel-2], LANDSAT, [Landsat-8, Landsat-9]: ALL. Separate with a comma the different desired options, Sentinel and Landsat contains the other options. ALL selects all available options.")
    parser.add_argument("--enable_mask", type=bool, default=True,
                        help="Enable mask creation.")
    parser.add_argument("--super_image", type=bool, default=True, 
                        help="Enable super-image creation. Since different sensores output different image sizes this is a option to make the images all the same size.")
    parser.add_argument("--max_cloud_coverage", type=int, default=20, 
                        help="Must be a number between 0 and 100.")
    return parser



def main():
    # Get input arguments
    opts = get_argparser().parse_args()
    
    # Just to make sure that the arguments added by the user are valid
    data_validation.check_opts(opts)
    
    # Trigger the authentication flow.
    ee.Authenticate()
    # Initialize the library.
    ee.Initialize()

    # ----------------------- Takes the KML file creates a frame with the chosen window_size and saves a mask of the area.
    # File containing the areas of interest
    kml_files = os.listdir('roi')
    # Sparate all areas of interest, append to the list. Append names to the names list
    aoi_names, aois = kml_handler.kml_reader(kml_files)
    
    # Padding size, used to get sharper edgeds on the image. If the image request is the same size as the intended the image is blurry at the edges.
    padding_size = 4
    
    # Get the areas of interst framed and the size of the images that are going to get created
    aoi_square =  geometry.get_squares(aois, opts.window_size, padding_size)
    if opts.enable_mask:
        # Save the mask
        for idx, a in enumerate(aois):
            path = opts.save_folder + '/' + aoi_names[idx] + '/Mask/'
            geometry.get_mask(path, a, opts.window_size, ["2022-03-12","2022-04-12"])

    # ================== Sentinel-1 ============================================
    if "Sentinel-1" in opts.satelites or "SENTINEL" in opts.satelites or "ALL" in opts.satelites:
        # -------------------------  Retrives the availabe bands from Sentinel-1
        aoi_bands = ee.Geometry.Polygon(aois[0],None,False)
        ffa_db = ee.Image(ee.ImageCollection('COPERNICUS/S1_GRD') 
                            .filterBounds(aoi_bands)
                            .first() 
                            .clip(aoi_bands))
        # Variables needed to save images
        bands_s1 = ffa_db.bandNames().getInfo()
        bands_s1.remove('angle')
        bands_s1.insert(0,'RGB')

        # Defined values to be the best for these bands
        # intervals - [min[num,num], max[num,num]]
        interval = [[-14, -25], [-7, -7]]
        
        for i_aoi, aoi in enumerate(aoi_square):
            for j_ch, channel in enumerate(bands_s1):
                if channel == "RGB":
                    incomplete_images_S1 = []    
                    incomplete_images_RGB = sentinel.ExportCol_Sentinel1(geometry, aoi, channel, interval, i_aoi, j_ch, opts, aoi_names, incomplete_images_S1, padding_size)
                else:
                    sentinel.ExportCol_Sentinel1(geometry, aoi, channel, interval, i_aoi, j_ch, opts, aoi_names, incomplete_images_RGB, padding_size)

    # ================== Sentinel-2 ============================================
    if  'Sentinel-2' in opts.satelites or "SENTINEL" in opts.satelites or "ALL" in opts.satelites:
        # -------------------------  Retrives the availabe bands from Sentinel-2
        aoi_bands = ee.Geometry.Polygon(aois[0],None,False)
        ffa_s2 = ee.Image(ee.ImageCollection('COPERNICUS/S2_HARMONIZED') 
                            .filterBounds(aoi_bands) 
                            .first()
                            .clip(aoi_bands))
        bands_s2 = ffa_s2.bandNames().getInfo()
        aux_bands_s2 =  bands_s2.copy()
        for x in aux_bands_s2: 
            if x in  ['B2', 'B3', 'B4','QA10','QA20','QA60','B10', "MSK_CLASSI_CIRRUS", "MSK_CLASSI_OPAQUE", "MSK_CLASSI_SNOW_ICE"]: 
                bands_s2.remove(x)
        bands_s2.insert(0,'RGB')

        # Defined best values for these bands, these can be changed.
        min = [0] * len(bands_s2)
        max = [2700, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 2000, 3200, 2500, 3000]
        
        # Image request
        for i_aoi, roi in enumerate(aoi_square):
            for j_ch, channel in enumerate(bands_s2):
                if channel == 'RGB':
                    incomplete_images_S2 = []
                    incomplete_images_B2 = sentinel.ExportCol_Sentinel2(geometry, roi, channel, min, max, i_aoi, j_ch, opts, aoi_names, incomplete_images_S2, padding_size)
                else:
                    sentinel.ExportCol_Sentinel2(geometry, roi, channel, min, max, i_aoi, j_ch, opts, aoi_names, incomplete_images_B2, padding_size)

    # ================== Landsat-8 ==============================================
    if 'Landsat-8' in opts.satelites or 'LANDSAT' in opts.satelites or "ALL" in opts.satelites:
        # -------------------------  Retrives the availabe bands from Landsat-8
        aoi_bands = ee.Geometry.Polygon(aois[0],None,False)
        ffa_db = ee.Image(ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') 
                            .filterBounds(aoi_bands)
                            .first() 
                            .clip(aoi_bands))
        # Variables needed to save images
        bands_l8 = ffa_db.bandNames().getInfo()
        bands_l8 =  [b for b in bands_l8 if b not in ['SR_B2', 'SR_B3', 'SR_B4','SR_QA_AEROSOL', 'ST_B10', 'ST_ATRAN', 'ST_CDIST', 'ST_DRAD', 'ST_EMIS', 'ST_EMSD', 'ST_QA', 'ST_TRAD', 'ST_URAD',  'QA_PIXEL', 'QA_RADSAT']]
        bands_l8.insert(0,'RGB')

        # Values can be changed based on the band
        min = [0] * len(bands_l8)
        max = [0.3] * len(bands_l8)
        
        for i_aoi, aoi in enumerate(aoi_square):
            for j_ch, channel in enumerate(bands_l8): 
                landsat.ExportCol_landsat8(geometry, aoi, channel, min, max, i_aoi, j_ch, opts, aoi_names, padding_size)       

    # ================== Landsat-9 ==============================================                   
    if 'Landsat-9' in opts.satelites or 'LANDSAT' in opts.satelites or "ALL" in opts.satelites:
        # -------------------------  Retrives the availabe bands from Landsat-9
        aoi_bands = ee.Geometry.Polygon(aois[0],None,False)
        ffa_db = ee.Image(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') 
                            .filterBounds(aoi_bands)
                            .first() 
                            .clip(aoi_bands))
 
        # Variables needed to save images
        bands_l9 = ffa_db.bandNames().getInfo()
        bands_l9 =  [b for b in bands_l9 if b not in ['SR_B2', 'SR_B3', 'SR_B4', 'SR_QA_AEROSOL', 'ST_B10', 'ST_ATRAN', 'ST_CDIST', 'ST_DRAD', 'ST_EMIS', 'ST_EMSD', 'ST_QA', 'ST_TRAD', 'ST_URAD', 'QA_PIXEL', 'QA_RADSAT']]
        bands_l9.insert(0,'RGB')
        # Values can be changed based on the band
        min = [0] * len(bands_l9)
        max = [0.3] * len(bands_l9)
        
        
        for i_aoi, aoi in enumerate(aoi_square):
            for j_ch, channel in enumerate(bands_l9): 
                landsat.ExportCol_landsat9(geometry, aoi, channel, min, max, i_aoi, j_ch, opts, aoi_names, padding_size)       
    
        
if __name__ == '__main__':
    main()  