import ee
import os
import requests
from PIL import Image
from io import BytesIO
from utils import geometry, config_handler

def applyScaleFactors(image):
  opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
  thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
  return image.addBands(opticalBands, None, True)\
              .addBands(thermalBands, None, True)

def show_image(url):
    # Download the image
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))

    # Display the image
    img.show()

def main():
    # Trigger the authentication flow.
    SAccount_json = config_handler.load_config("service_account.json")
    service_account = SAccount_json["service_account"]
    credentials = ee.ServiceAccountCredentials(service_account, "ee-mariormr0010-a3b10aa94917.json")

    # Initialize the library.
    ee.Initialize(credentials)

    # File containing the areas of interest
    kml_files = os.listdir('roi')
    # Region of Interest
    aoi_names, aois = config_handler.kml_reader(kml_files)
    aoi_square =  geometry.get_squares(aois, 256, 5)
    aoi_geometry = ee.Geometry.Polygon(aoi_square[0],None,False)

    # Trigger the authentication flow.
    SAccount_json = config_handler.load_config("service_account.json")
    service_account = SAccount_json["service_account"]
    credentials = ee.ServiceAccountCredentials(service_account, "ee-mariormr0010-a3b10aa94917.json")

    # Initialize the library.
    ee.Initialize(credentials)

    ffa_s = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
                            .filterDate(ee.Date('2024-08-01'), ee.Date('2025-3-8'))\
                            .filterBounds(aoi_geometry)\
                            .filter(ee.Filter.lt('CLOUD_COVER', 11))
    ffa_s = ffa_s.map(applyScaleFactors)

    First_Image = ee.Image(ffa_s.first()).clip(aoi_geometry)

    rgb = ["SR_B4","SR_B3","SR_B2"]
    url = First_Image.getThumbURL({"min":0, "max":0.3,"bands":rgb})

    # Call function to show image
    show_image(url)


if __name__ == '__main__':
    main()