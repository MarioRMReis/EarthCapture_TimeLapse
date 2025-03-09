import ee
import os
import requests
import config_handler
from PIL import Image
from io import BytesIO
import geometry

def applyScaleFactors(image):
  opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
  thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
  return image.addBands(opticalBands, None, True)\
              .addBands(thermalBands, None, True)

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

rgb = ["ST_B10"]
url = First_Image.getThumbURL({"min":222, "max":690,"bands":rgb})

# Download the image
response = requests.get(url)
img = Image.open(BytesIO(response.content))

# Display the image
#img.show()



def get_min_max(aoi_geometry, region=None, scale=30):
    """Compute min and max values for each band in an image."""
    # Load image
    ffa_s = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
                        .filterDate(ee.Date('2024-08-01'), ee.Date('2025-3-8'))\
                        .filterBounds(aoi_geometry)\
                        .filter(ee.Filter.lt('CLOUD_COVER', 11))
    ffa_s = ffa_s.map(applyScaleFactors)

    First_Image = ee.Image(ffa_s.first()).clip(aoi_geometry)
    
    bands = First_Image.bandNames().getInfo()
        
    # Reduce region to get min and max per band
    stats = First_Image.reduceRegion(
        reducer=ee.Reducer.minMax(),
        geometry=region if region else ffa_s.geometry(),
        scale=scale,
        maxPixels=1e13
    )
    
    # Convert results to dictionary
    min_max_values = {band: (stats.get(f'{band}_min').getInfo(), stats.get(f'{band}_max').getInfo()) for band in bands}
    
    return min_max_values

# Example Landsat image
region = aoi_geometry  # Define a region as an ee.Geometry if needed

min_max = get_min_max(aoi_geometry, region)
print(min_max)
