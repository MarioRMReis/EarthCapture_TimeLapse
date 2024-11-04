import ee
import os 
import cv2
import math
import requests
import argparse
import numpy as np
from datetime import date, timedelta
from pykml import parser
from utils import geometry, kml_handler
from satelite import sentinel1, sentinel2

def get_argparser():
    parser = argparse.ArgumentParser()

    parser.add_argument("--save_folder", type=str, default="results", 
                        help="Path to save the EarthEngine images and the corresponding masks.")
    parser.add_argument("--start_date", type=str, default=str(date.today() - timedelta(days=14)), 
                        help="Starting date from witch we are going to start requesting images")
    parser.add_argument("--end_date", type=str, default=str(date.today()), 
                        help="Ending date from witch we are going to start requesting images")
    parser.add_argument("--window_size", type=int, default=128, 
                        help="Size of the square framing the area of interest.")

    return parser



def main():
    # Get input arguments
    opts = get_argparser().parse_args()
    
    # Trigger the authentication flow.
    ee.Authenticate()
    # Initialize the library.
    ee.Initialize()

    # File containing the areas of interest
    kml_files = os.listdir('roi')

    # Sparate all areas of interest, append to the list. Append names to the names list
    aoi_names, aois = kml_handler.kml_reader(kml_files)
    # Get the areas of interst framed and the size of the images that are going to get created
    aoi_square, size =  geometry.get_squares(aois)
    # Save the mask
    for idx, a in enumerate(aois):
        path = opts.save_folder + '/' + aoi_names[idx] + '/Mask/'
        geometry.get_mask(path, a, size, ["2022-03-12","2022-04-12"])


    aoi_bands = ee.Geometry.Polygon(aois[0],None,False)

    ffa_db = ee.Image(ee.ImageCollection('COPERNICUS/S1_GRD') 
                        .filterBounds(aoi_bands)
                        .first() 
                        .clip(aoi_bands))

    # Variables needed to save images
    bands_s1 = ffa_db.bandNames().getInfo()
    bands_s1.remove('angle')
    bands_s1.append('RGB')

    # Defined values to be the best for these bands
    # intervals - [min[num,num], max[num,num]]
    interval = [[-14, -25], [[-7] * 2]]
    #-------------------
    for i, aoi in enumerate(aoi_square):
        for j, channel in enumerate(bands_s1):
            # def ExportCol_Sentinel1(roi, channel, interval, aoi_num, jdx, timeframe, numImgs, save_folder, aoi_names):
            sentinel1.ExportCol_Sentinel1(aoi, channel, interval, i, j, [opts.start_date, opts.end_date])
            


    aoi_bands = ee.Geometry.Polygon(aois[0],None,False)

    ffa_s2 = ee.Image(ee.ImageCollection('COPERNICUS/S2') 
                        .filterBounds(aoi_bands) 
                        .first() 
                        .clip(aoi_bands))

    bands_s2 = ffa_s2.bandNames().getInfo()
    aux_bands_s2 =  bands_s2.copy()

    for x in aux_bands_s2: 
        if x in  ['QA10','QA20','QA60','B10']: 
            bands_s2.remove(x) #bands_s2.remove(['QA10','QA20','QA60','B10'])
    bands_s2.append('RGB')

    # Defined best values for these bands
    min = [0] * len(bands_s2)
    max = [2700, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 2000, 3200, 2500, 3000]

    bands_s2.insert(0,bands_s2.pop(bands_s2.index('B2')))

    for idx, a in enumerate(aoi_square):
        for jdx, b in enumerate(bands_s2):
            if b == 'B2':
                incomplete_images = []
                incomplete_images_B2 =sentinel2.ExportCol_Sentinel2(a, b, min, max, idx, jdx, 99, incomplete_images)
            else:
                sentinel2.ExportCol_Sentinel2(a, b, min, max, idx, jdx, 99, incomplete_images_B2)


if __name__ == '__main__':
    main()