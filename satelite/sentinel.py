import ee
import os
import requests
import numpy as np
import cv2
from utils import config_handler, geometry, helper
import visualizer

# !____________________________________________SENTINEL-1____________________________________________
def process_sentinel1(config, opts, aoi_names, aois, aoi_square):
    # Retrives the available bands from Sentinel-1
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
    
    # Image request
    for aoi_num, aoi in enumerate(aoi_square):
        for band_num, band in enumerate(bands_info):
            if band_num == 0:
                incomplete_images_empty = []    
                incomplete_images_list = image_request_Sentinel1(aoi, band_num, band, opts, aoi_names[aoi_num], incomplete_images_empty)
            else:
                incomplete_images_list = image_request_Sentinel1(aoi, band_num, band, opts, aoi_names[aoi_num], incomplete_images_list)

def image_request_Sentinel1(aoi, band_num, band, opts, aoi_name, incomplete_images):
    aoi_geometry = ee.Geometry.Polygon(aoi ,None,False)
    ffa_s = ee.ImageCollection('COPERNICUS/S1_GRD') \
                    .filterBounds(aoi_geometry) \
                    .filterDate(ee.Date(str(opts.start_date)), ee.Date(str(opts.end_date)))
    colec_size = ffa_s.size().getInfo()        
    colList = ffa_s.toList(colec_size)
    
    # Create the save folder for the result images
    path = os.path.join(opts.save_folder, aoi_name, "Sentinel", "Sentinel-1", band["name"])
    if not os.path.exists(path):
        os.makedirs(path)
            
    for i in range(colec_size):
        # Skip incomplete images
        if i in incomplete_images:
            continue
        
        # Get the image collection and clip aoi
        img = ee.Image(colList.get(i)).double().clip(aoi_geometry)
        id = img.id().getInfo()
        
        img_array = config_handler.Sentinel1_band_composition(img, band["bands"])
        # Get the image URL
        if len(img_array) == 1:    
            url = img_array[0].getThumbURL({'min': band["min"], 'max': band["max"]})
        elif len(img_array) == 3:
            url = ee.Image.rgb(img_array[0],img_array[1],img_array[2]).getThumbURL({'min': band["min"], 'max': band["max"]})
                
        # Download the image
        img_data = requests.get(url).content
        # Enhance the image
        img_data = geometry.cut_padding_and_enhance(img_data, opts)
        
        if band_num == 0:
            if not geometry.Check_image(img_data, opts.padding_size):
                incomplete_images.append(i)
                # Skips the iteration
                continue
            
        # Save the image
        with open(path  + '/' + id + '.png', 'wb') as handler:        
            handler.write(img_data)
    
    # Return the index of the incomplete images        
    return incomplete_images

# !____________________________________________SENTINEL-2____________________________________________
def process_sentinel2(config, opts, aoi_names, aois, aoi_square):
    # Retrives the available bands from Sentinel-2
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
                incomplete_images_list = image_request_Sentinel2(aoi, band_num, band, opts, aoi_names[aoi_num], incomplete_images_empty)
            else:
                incomplete_images_list = image_request_Sentinel2(aoi, band_num, band, opts, aoi_names[aoi_num], incomplete_images_list)        

def image_request_Sentinel2(aoi, band_num, config, opts, aoi_name, incomplete_images):
    # From the aoi given, get all images(colList) in the colection and the amout (colec_size)
    aoi_geometry = ee.Geometry.Polygon(aoi ,None,False)
    ffa_s = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
                    .filterDate(ee.Date(opts.start_date), ee.Date(opts.end_date)) \
                    .filterBounds(aoi_geometry) \
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', opts.max_cloud_coverage))
    colec_size = ffa_s.size().getInfo()        
    colList = ffa_s.toList(colec_size)
    
    # Make directory for the current band
    path = os.path.join(opts.save_folder, aoi_name, "Sentinel", "Sentinel-2", config["name"])
    if not os.path.exists(path):
        os.makedirs(path)
        
    for i in range(colec_size):
        # Skip iteration if i in incomplete_images
        if i in incomplete_images:
            continue
        
        # Get image colection
        img = ee.Image(colList.get(i)).double().clip(aoi_geometry)
        id = img.id().getInfo()
        
        # Check if the set of bands selected has the same resolution
        if isinstance(config['resolution'], list):
            img_array = []
            for j, band in enumerate(config['bands']):
                # Image request
                url = img.getThumbURL({"min":config["min"][j], "max":config["max"][j],"bands":band})
                img_req = requests.get(url).content
                
                # Check if the image is complete and add it to the list of incomplete images if true
                if band_num == 0:
                    # Check_image returns false if the image is incomplete
                    if not geometry.Check_image(img_req, opts.padding_size):
                        incomplete_images.append(i)
                        # Skips this for loop
                        break
                
                # Enhnacing the image
                img_eh = geometry.cut_padding_and_enhance(img_req, opts, False, band_comb=True)
                
                # The images come with 3 channels, so we need to convert them to grayscale
                gray_image = cv2.cvtColor(img_eh, cv2.COLOR_BGR2GRAY)
                img_array.append(gray_image)
                
            # Skip iteration 
            if i in incomplete_images:
                continue
            
            # Merge the images into a single image
            img_data = np.stack([img_array[0],img_array[1],img_array[2]], axis=-1)
            # Encode the image
            _, img_data = cv2.imencode(opts.image_format, img_data)
            img_data = img_data.tobytes()
        else:
            # Get the image with the selected band(s)
            url = img.getThumbURL({"min":config["min"], "max":config["max"],"bands":config["bands"]}) 
            # Get ID image data and cut the padding
            img_data = requests.get(url).content
            # Check if the image is complete and add it to the list of incomplete images if true
            if band_num == 0:
                # Check_image returns false if the image is incomplete
                if not geometry.Check_image(img_data, opts.padding_size):
                    incomplete_images.append(i)
                    # Skips this iteration
                    continue
            img_data = geometry.cut_padding_and_enhance(img_data, opts)
            
        # Save the image
        with open(path  + '/' + id + opts.image_format, 'wb') as handler:        
            handler.write(img_data)
                    
    # Return the index os the incomplete images, even if its not altered
    return incomplete_images

