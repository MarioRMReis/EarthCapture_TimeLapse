
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
    parser.add_argument("--start_date", type=str, default=(str(date.today() - timedelta(days=31))), 
                        help="Format: YYYY-MM-DD, \nStarting date from witch we are going to start requesting images")
    parser.add_argument("--end_date", type=str, default=(str(date.today())), 
                        help="Format: YYYY-MM-DD, \nEnding date from witch we are going sto stop requesting images")
    parser.add_argument("--window_size", type=int, default=124, 
                        help="Options: 128, 256, 512, 1024. You can pick any resolution but keep and mind the area of your region, should be greater than 64.")
    parser.add_argument("--satelites", type=str, default="LANDSAT", 
                        help="Options: SENTINEL, [Sentinel-1, Sentinel-2], LANDSAT, [LandSat-8, LandSat-9]: ALL. Separate with a comma the different desired options, Sentinel and Landsat contains the other options. ALL selects all available options.")
    parser.add_argument("--enable_mask", type=bool, default=True,
                        help="Enable mask creation.")
    parser.add_argument("--super_image", type=bool, default=False, 
                        help="Enable super-image creation. Since different sensores output different image sizes this is a option to make the images all the same size.")
    parser.add_argument("--max_cloud_coverage", type=int, default=10, 
                        help="Must be a number between 0 and 100.")
    parser.add_argument("--padding_size", type=int, default=8,
                        help="This will determine the size of the padding used in the fetched request. Padding size, used to get sharper edgeds on the image. If the image request is the same size as the intended the image is blurry at the edges.")
    parser.add_argument("--min_max_values", type=bool, default=False,
                        help="Changes the min_max values of the configuration file to the ones provided by the Reducer.minMax() function.")
    parser.add_argument("--image_format", type=str, default=".png",
                        help="Options: .png, .jpg, .tiff. The default is .png.")
    return parser


def main():
    opts = get_argparser().parse_args()
    config = config_handler.load_config(opts.config_file)
    data_validation.check_opts(opts)

    SAccount_json = config_handler.load_config("service_account.json")
    service_account = SAccount_json["service_account"]
    credentials = ee.ServiceAccountCredentials(service_account, "generated_EE.json")
    ee.Initialize(credentials)


    kml_files = os.listdir('roi')
    
    # Sparate all areas of interest, append to the list. Append names to the names list
    # Takes all the areas of interest and are named afeter the kml file
    aoi_names, aois = config_handler.kml_reader(kml_files)
    
    # With the chosen window from the user, get the squares that will be used to fetch the images
    aoi_square =  geometry.get_squares(aois, opts.window_size, opts.padding_size)
    
    # If the user wants to create a mask, this will create a mask where white is the region of interest, image size is the same as the window size
    if opts.enable_mask:
        # Save the mask
        for idx, a in enumerate(aois):
            path = opts.save_folder + '/' + aoi_names[idx] + '/Mask/'
            geometry.get_mask(path, a, opts.window_size, ["2022-03-12","2022-04-12"])

    # Get the satelites selected by the user
    sat_list = helper.get_satelites(opts.satelites)

    # Process the images for each selected satelite
    for sat in sat_list:
        if sat == "sentinel-1":
            sentinel.process_sentinel1(config, opts, aoi_names, aois, aoi_square)
        if sat == "sentinel-2":
            sentinel.process_sentinel2(config, opts, aoi_names, aois, aoi_square)
        if sat == "landsat-8":
            landsat.process_landsat8(config, opts, aoi_names, aois, aoi_square)
        if sat == "landsat-9":
            landsat.process_landsat9(config, opts, aoi_names, aois, aoi_square)
    
if __name__ == '__main__':
    main()  