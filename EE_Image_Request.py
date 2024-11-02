import ee
import os 
import cv2
import math
import requests
import argparse
import numpy as np
from datetime import date, timedelta
from pykml import parser


def get_argparser():
    parser = argparse.ArgumentParser()

    parser.add_argument("--save_folder", type=str, default="save_folder", 
                        help="Path to save the EarthEngine images and the corresponding masks.")
    parser.add_argument("--start_date", type=str, default=str(date.today() - timedelta(days=14)), 
                        help="Starting date from witch we are going to start requesting images")
    parser.add_argument("--end_date", type=str, default=str(date.today()), 
                        help="Ending date from witch we are going to start requesting images")
    parser.add_argument("--window_size", type=int, default=128, 
                        help="Size of the square framing the area of interest.")

    return parser



# Trigger the authentication flow.
ee.Authenticate()
# Initialize the library.
ee.Initialize()

# Areas of interest
aois = []
aoi_names = []
# File containing the areas of interest
kml_files = os.listdir('roi')

# Sparate all areas of interest, append to the list. Append names to the names list
for kml in kml_files:
    with open('roi/' + kml, 'r') as f:
        root = parser.parse(f).getroot()
    namespace = {"kml": 'http://www.opengis.net/kml/2.2'}
    pms = root.xpath(".//kml:Placemark[.//kml:Polygon]", namespaces=namespace)
    roi_string = []
    for p in pms:
        if hasattr(p, 'MultiGeometry'):
            for poly in p.MultiGeometry.Polygon:
                roi_string.append(poly.outerBoundaryIs.LinearRing.coordinates)
        else:
            roi_string.append(p.Polygon.outerBoundaryIs.LinearRing.coordinates)

    dot = kml_files[0].find('.')
    name_kml = kml_files[0][:dot] + '-'
    for jdx, r in enumerate(roi_string):
        aoi_names.append(name_kml + str(jdx))
        roi_str = str(r).split(' ')
        aux = []
        for idx, rs in enumerate(roi_str):
            if idx == 0:
                n = rs[7::].split(',')
                aux.append([float(n[i]) for i in range(len(n)-1)])
            elif idx == (len(roi_str)-1): 
                print(rs)
            else:
                n = rs.split(',')
                aux.append([float(n[i]) for i in range(len(n)-1)])
        aois.append([aux])


def get_squares(aois):
    # 0.011377373345324189 0.014894925631009616 -> Height, Width 
    # Hight and Width of a 128 square in kml coords
    S128 = [0.014854925631009616, 0.011377373345324189]
    h_aux = S128[1]/2
    w_aux = S128[0]/2

    # 128x128 new image with the Area of interest in frame
    new_aois = []

    # With the size of the 128x128 square in coords we can add half of those values to the calculated center of the Aoi
    #   and find the coords of all 4 corners of our new AOI (Does not deal with areas of interst that do not fit a 128 by 128)
    for aoi in aois:
        # Find centeroid ----------------------------
        siz = len(aoi[0])
        list_width = []
        list_height = []
        for i in range(siz): 
            list_width.append(aoi[0][i][0])
            list_height.append(aoi[0][i][1])

        max_width = max(list_width)
        min_width = min(list_width)
        max_height = max(list_height)
        min_height = min(list_height)
        
        centroid_width = (max_width+min_width)/2
        centroid_height = (max_height+min_height)/2

        aoi_new = [[[(centroid_width-w_aux), (centroid_height+h_aux)], [(centroid_width-w_aux), (centroid_height-h_aux)], [(centroid_width+w_aux), (centroid_height-h_aux)], [(centroid_width+w_aux), (centroid_height+h_aux)]]]
        new_aois.append(aoi_new)
        size = [128,128]


    return new_aois, size

def get_mask(path, aoi, size, timeframe):
    # Inputs:
    #     - path -> path to the aoi saved images
    #     - aoi -> Area of interest of the landfield
    #     - size = [sizeX, sizeY] -> size of the mask, (ie: 128x128, 256x256, 354x128...)
    aoi_mask = ee.Geometry.Polygon(aoi,None,False)
    ffa_s2 = ee.ImageCollection('COPERNICUS/S2') \
                            .filterBounds(aoi_mask) \
                            .filterDate(ee.Date(timeframe[0]), ee.Date(timeframe[1]))
    colList = ffa_s2.toList(30)
    # This part get's the land area image needed to create the mask --------------
    img = ee.Image(colList.get(17)).double().clip(aoi_mask)
    rgb = ['B4','B3','B2']
    url = img.getThumbURL({"min":-200000, "max":-200000,"bands":rgb})

    img_data = requests.get(url).content

    img_aux = cv2.imdecode(np.frombuffer(img_data, np.uint8), -1)

    # Create mask ----------------------------------------------------------------
    # img_aux.shape -> [x,y,z]
    x = img_aux.shape[0]
    y = img_aux.shape[1]
    x_sum = math.ceil((size[0]-x)/2)
    y_sum = math.ceil((size[1]-y)/2)

    img_zeros = np.zeros([size[0], size[1], 3])
    img_zeros[x_sum:(x_sum+x), y_sum:(y_sum+y), :] = img_aux[:,:,0:3]
    try:
        os.makedirs(path)
        cv2.imwrite(path +'mask.jpg', img_zeros)
    except:
        cv2.imwrite(path +'mask.jpg', img_zeros)



    



