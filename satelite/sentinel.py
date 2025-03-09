import ee
import os
import requests
from utils import config_handler, geometry

def ExportCol_Sentinel1(aoi, band_num, band, opts, aoi_name, incomplete_images):
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
        img = ee.Image(colList.get(i)).double().clip(aoi_geometry)
        img_array = config_handler.Sentinel1_band_composition(img, band["bands"])
        
        if len(img_array) == 1:    
            url = img_array[0].getThumbURL({'min': band["min"], 'max': band["max"]})
        elif len(img_array) == 3:
            url = ee.Image.rgb(img_array[0],img_array[1],img_array[2]).getThumbURL({'min': band["min"], 'max': band["max"]})
                
        id = img.id().getInfo()
        img_data = requests.get(url).content
        img_data = geometry.cut_padding_and_enhance(img_data, opts)
        
        if band_num == 0:
            img_skip_idx = geometry.Check_image(i, img_data, opts.window_size)
            if img_skip_idx != None:
                incomplete_images.append(img_skip_idx)
                    
        if i not in incomplete_images:
            with open(path  + '/' + id + '.png', 'wb') as handler:        
                handler.write(img_data)
                
    return incomplete_images
        

def ExportCol_Sentinel2(aoi, band_num, band, opts, aoi_name, incomplete_images):
    # From the aoi given, get all images(colList) in the colection and the amout (colec_size)
    aoi_geometry = ee.Geometry.Polygon(aoi ,None,False)
    ffa_s = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
                    .filterDate(ee.Date(opts.start_date), ee.Date(opts.end_date)) \
                    .filterBounds(aoi_geometry) \
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', opts.max_cloud_coverage))
    colec_size = ffa_s.size().getInfo()        
    colList = ffa_s.toList(colec_size)
    
    # Make directory for each band
    path = os.path.join(opts.save_folder, aoi_name, "Sentinel", "Sentinel-2", band["name"])
    if not os.path.exists(path):
        os.makedirs(path)
        
    for i in range(colec_size):
        img = ee.Image(colList.get(i)).double().clip(aoi_geometry)   
        
        # Get the image with the selected band(s)
        url = img.getThumbURL({"min":band["min"], "max":band["max"],"bands":band["bands"]}) 

        # Get ID image data and cut the padding
        id = img.id().getInfo()
        img_data = requests.get(url).content
        img_data = geometry.cut_padding_and_enhance(img_data, opts)
        
        # Check if the image is complete, due to the image capturing system sometimes the images apear cropped
        if band_num == 0:
            img_skip_idx = geometry.Check_image(i, img_data, opts.window_size)
            if img_skip_idx != None:
                incomplete_images.append(i)

        # If the image is complete it's saved as a png with the ID as a name
        if i not in incomplete_images:
            with open(path  + '/' + id + '.png', 'wb') as handler:        
                handler.write(img_data)
                
    # Return the index os the incomplete images, even if its not altered
    return incomplete_images

