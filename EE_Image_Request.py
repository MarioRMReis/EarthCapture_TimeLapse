
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
# warning spam prevention, huggingface 0.25 needed

import ee
import os
import argparse
from datetime import date, timedelta
from utils import config_handler, geometry, data_validation, helper
from satelite import landsat, sentinel

def get_argparser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_file", type=str, default='config.json',
                        help="Config file saves information like, skiping bands and values that adjust the image quality.")
    parser.add_argument("--save_folder", type=str, default="results", 
                        help="Path to save the EarthEngine images and the corresponding masks.")
    parser.add_argument("--start_date", type=str, default=(str(date.today() - timedelta(days=64))), 
                        help="Format: YYYY-MM-DD, \nStarting date from witch we are going to start requesting images")
    parser.add_argument("--end_date", type=str, default=(str(date.today())), 
                        help="Format: YYYY-MM-DD, \nEnding date from witch we are going sto stop requesting images")
    parser.add_argument("--window_size", type=int, default=128, 
                        help="Options: 128, 256, 512, 1024. You can pick any resolution but keep and mind the area of your region, should be greater than 64.")
    parser.add_argument("--satelites", type=str, default="LANDSAT", 
                        help="Options: SENTINEL, [Sentinel-1, Sentinel-2], LANDSAT, [LandSat-8, LandSat-9]: ALL. Separate with a comma the different desired options, Sentinel and Landsat contains the other options. ALL selects all available options.")
    parser.add_argument("--enable_mask", type=bool, default=True,
                        help="Enable mask creation.")
    parser.add_argument("--super_image", type=bool, default=True, 
                        help="Enable super-image creation. Since different sensores output different image sizes this is a option to make the images all the same size.")
    parser.add_argument("--max_cloud_coverage", type=int, default=20, 
                        help="Must be a number between 0 and 100.")
    parser.add_argument("--padding_size", type=int, default=4,
                        help="This will determine the size of the padding used in the fetched request. Padding size, used to get sharper edgeds on the image. If the image request is the same size as the intended the image is blurry at the edges.")
    parser.add_argument("--min_max_values", type=bool, default=True,
                        help="Changes the min_max values of the configuration file to the ones provided by the Reducer.minMax() function.")
    return parser


def main():
    # Get input arguments
    opts = get_argparser().parse_args()
    
    # Load configuration file
    config = config_handler.load_config(opts.config_file)

    # Just to make sure that the arguments added by the user are valid
    data_validation.check_opts(opts)
    
    # Trigger the authentication flow.
    SAccount_json = config_handler.load_config("service_account.json")
    service_account = SAccount_json["service_account"]
    credentials = ee.ServiceAccountCredentials(service_account, "ee-mariormr0010-a3b10aa94917.json")
    
    # Initialize the library.
    ee.Initialize(credentials)
    
    # ----------------------- Takes the KML file creates a frame with the chosen window_size and saves a mask of the area.
    # File containing the areas of interest
    kml_files = os.listdir('roi')
    # Sparate all areas of interest, append to the list. Append names to the names list
    aoi_names, aois = config_handler.kml_reader(kml_files)
    
    # Get the areas of interst framed and the size of the images that are going to get created
    aoi_square =  geometry.get_squares(aois, opts.window_size, opts.padding_size)
    if opts.enable_mask:
        # Save the mask
        for idx, a in enumerate(aois):
            path = opts.save_folder + '/' + aoi_names[idx] + '/Mask/'
            geometry.get_mask(path, a, opts.window_size, ["2022-03-12","2022-04-12"])

    # ============================================================== Sentinel-1 ============================================
    if "Sentinel-1" in opts.satelites or "SENTINEL" in opts.satelites or "ALL" in opts.satelites:
        # -------------------------  Retrives the availabe bands from Sentinel-1
        aoi_bands = ee.Geometry.Polygon(aois[0],None,False)
        ffa_db = ee.Image(ee.ImageCollection('COPERNICUS/S1_GRD') 
                            .filterBounds(aoi_bands)
                            .first() 
                            .clip(aoi_bands))
        # Variables needed to save images
        bands_s1 = ffa_db.bandNames().getInfo()
        
        if opts.min_max_values:
            # Compute min and max values for each band
            helper.get_min_max(config, "Sentinel-1", image=ffa_db, bands=bands_s1)
        
        bands_info = config_handler.get_config_param(config, bands_s1, 'Sentinel-1')
        
        
        for aoi_num, aoi in enumerate(aoi_square):
            for band_num, band in enumerate(bands_info):
                if band_num == 0:
                    incomplete_images_empty = []    
                    incomplete_images_list = sentinel.ExportCol_Sentinel1(aoi, band_num, band, opts, aoi_names[aoi_num], incomplete_images_empty)
                else:
                    incomplete_images_list = sentinel.ExportCol_Sentinel1(aoi, band_num, band, opts, aoi_names[aoi_num], incomplete_images_list)

    # ============================================================== Sentinel-2 ============================================
    if  'Sentinel-2' in opts.satelites or "SENTINEL" in opts.satelites or "ALL" in opts.satelites:
        # -------------------------  Retrives the availabe bands from Sentinel-2
        aoi_bands = ee.Geometry.Polygon(aois[0],None,False)
        ffa_db = ee.Image(ee.ImageCollection('COPERNICUS/S2_HARMONIZED') 
                            .filterBounds(aoi_bands) 
                            .first()
                            .clip(aoi_bands))
        bands_s2 = ffa_db.bandNames().getInfo()
        
        if opts.min_max_values:
            # Compute min and max values for each band
            helper.get_min_max(config, "Sentinel-2", image=ffa_db, bands=bands_s2)
                   
        bands_info = config_handler.get_config_param(config, bands_s2, 'Sentinel-2')
        
        # Image request
        for aoi_num, aoi in enumerate(aoi_square):
            for band_num, band in enumerate(bands_info):
                if band_num == 0:
                    incomplete_images_empty = []
                    incomplete_images_list = sentinel.ExportCol_Sentinel2(aoi, band_num, band, opts, aoi_names[aoi_num], incomplete_images_empty)
                else:
                    incomplete_images_list = sentinel.ExportCol_Sentinel2(aoi, band_num, band, opts, aoi_names[aoi_num], incomplete_images_list)

    # ============================================================== Landsat-8 ==============================================
    if 'LandSat-8' in opts.satelites or 'LANDSAT' in opts.satelites or "ALL" in opts.satelites:
        # -------------------------  Retrives the availabe bands from Landsat-8
        aoi_bands = ee.Geometry.Polygon(aois[0],None,False)
        ffa_db = ee.Image(ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') 
                            .filterBounds(aoi_bands)
                            .first() 
                            .clip(aoi_bands))
        bands_l8 = ffa_db.bandNames().getInfo()
        
        if opts.min_max_values:
            # Compute min and max values for each band
            helper.get_min_max(config, "LandSat-8", image=ffa_db, bands=bands_l8)
            
        bands_info = config_handler.get_config_param(config, bands_l8, 'LandSat-8')
        
        for aoi_num, aoi in enumerate(aoi_square):
            for band_num, band in enumerate(bands_info): 
                landsat.ExportCol_landsat8(aoi, band, opts, aoi_names[aoi_num])

    # ============================================================== Landsat-9 ==============================================                   
    if 'LandSat-9' in opts.satelites or 'LANDSAT' in opts.satelites or "ALL" in opts.satelites:
        # -------------------------  Retrives the availabe bands from Landsat-9
        aoi_bands = ee.Geometry.Polygon(aois[0],None,False)
        ffa_db = ee.Image(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') 
                            .filterBounds(aoi_bands)
                            .first() 
                            .clip(aoi_bands))
        bands_l9 = ffa_db.bandNames().getInfo()
        
        if opts.min_max_values:
            # Compute min and max values for each band
            helper.get_min_max(config, "LandSat-9", image=ffa_db, bands=bands_l9)
            
        bands_info = config_handler.get_config_param(config, bands_l9, 'LandSat-9')
        
        for aoi_num, aoi in enumerate(aoi_square):
            for band_num, band in enumerate(bands_info): 
                landsat.ExportCol_landsat9(aoi, band, opts, aoi_names[aoi_num])

        
if __name__ == '__main__':
    main()  