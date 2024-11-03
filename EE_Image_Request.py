import ee
import os 
import cv2
import math
import requests
import argparse
import numpy as np
from datetime import date, timedelta
from pykml import parser
from utils import geometry
from satelite import sentinel1, sentinel2

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



    



