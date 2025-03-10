import ee
import os
import requests
from utils import geometry, config_handler, helper

# ? Apply scale factors to Landsat-8 and Landsat-9 images
def applyScaleFactors(image):
  opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
  thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
  return image.addBands(opticalBands, None, True)\
              .addBands(thermalBands, None, True)

# !____________________________________________LANDSAT-8____________________________________________
def process_landsat8(config, opts, aoi_names, aois, aoi_square):
    # Retrives the available bands from Landsat-8
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
    
    # Image request
    for aoi_num, aoi in enumerate(aoi_square):
        for band_num, band in enumerate(bands_info): 
            image_request_landsat8(aoi, band, opts, aoi_names[aoi_num])

def image_request_landsat8(roi, band, opts, aoi_name):
    # From the roi given, get all images(colList) in the colection and the amout (colec_size)
    aoi_geometry = ee.Geometry.Polygon(roi ,None,False)
    ffa_s = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                    .filterDate(ee.Date(opts.start_date), ee.Date(opts.end_date)) \
                    .filterBounds(aoi_geometry)\
                    .filterMetadata('CLOUD_COVER', 'less_than', opts.max_cloud_coverage)
    ffa_s = ffa_s.map(applyScaleFactors)
    colec_size = ffa_s.size().getInfo()
    colList = ffa_s.toList(colec_size)
    
    # Create the save folder for the result images
    path = os.path.join(opts.save_folder, aoi_name, "Landsat","Landsat-8", band["name"])
    if not os.path.exists(path):
        os.makedirs(path)
        
    for i in range(colec_size):
        img = ee.Image(colList.get(i)).clip(aoi_geometry)

        url = img.getThumbURL({"min":band["min"], "max":band["max"],"bands":band["bands"]})

        id = img.id().getInfo()
        img_data = requests.get(url).content
        img_data = geometry.cut_padding_and_enhance(img_data, opts)
        
        with open(path  + '/' + id + '.png', 'wb') as handler:        
            handler.write(img_data)

# !____________________________________________LANDSAT-9____________________________________________
def process_landsat9(config, opts, aoi_names, aois, aoi_square):
    # Retrives the available bands from Landsat-9
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
    
    # Image request
    for aoi_num, aoi in enumerate(aoi_square):
        for band_num, band in enumerate(bands_info): 
            image_request_landsat9(aoi, band, opts, aoi_names[aoi_num])

def image_request_landsat9(roi, band, opts, aoi_name):
    aoi_geometry = ee.Geometry.Polygon(roi ,None,False)
    ffa_s = ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') \
                    .filterDate(ee.Date(opts.start_date), ee.Date(opts.end_date)) \
                    .filterBounds(aoi_geometry)\
                    .filter(ee.Filter.lt('CLOUD_COVER', opts.max_cloud_coverage))
    ffa_s = ffa_s.map(applyScaleFactors)
    colec_size = ffa_s.size().getInfo()
    colList = ffa_s.toList(colec_size)

    path = os.path.join(opts.save_folder, aoi_name, "Landsat", "Landsat-9", band["name"])
    if not os.path.exists(path):
        os.makedirs(path)
    
    for i in range(colec_size):
        img = ee.Image(colList.get(i)).clip(aoi_geometry)
        
        url = img.getThumbURL({"min":band["min"], "max":band["max"],"bands":band["bands"]})

        id = img.id().getInfo()
        img_data = requests.get(url).content
        img_data = geometry.cut_padding_and_enhance(img_data, opts)

        with open(path  + '/' + id + '.png', 'wb') as handler:        
            handler.write(img_data)