import ee
import os
import requests
from PIL import Image
from io import BytesIO
from super_image import EdsrModel, ImageLoader

def ExportCol_Sentinel1(geometry, roi, channel, interval, aoi_num, jdx, opts, aoi_names, incomplete_images, padding_size):
    aoi_geometry = ee.Geometry.Polygon(roi ,None,False)
    ffa_s = ee.ImageCollection('COPERNICUS/S1_GRD') \
                    .filterBounds(aoi_geometry) \
                    .filterDate(ee.Date(str(opts.start_date)), ee.Date(str(opts.end_date)))
                            
    colList = ffa_s.toList(opts.numImgs); 
    for i in range(0,opts.numImgs,1):
        try:
            img = ee.Image(colList.get(i)).double().clip(aoi_geometry)
            # Create the save folder for the result images
            path = os.path.join(opts.save_folder, aoi_names[aoi_num], "Sentinel", "Sentinel-1", channel)
            if not os.path.exists(path):
                os.makedirs(path)
                
            # Exeption beacause to get a RGB channel with the Sentinel-1 we need to correspond each channel and compute the last
            if channel == 'RGB':
                imgR = img.select('VV')
                imgG = img.select('VH')
                imgB = img.select('VV').divide(img.select('VH'))
                url = ee.Image.rgb(imgR,imgG,imgB).getThumbURL({'min': [interval[0][0], interval[0][1], 0], 'max': [0, 0, 2]})
            elif channel == 'VV':
                img = img.select('VV')
                url = img.getThumbURL({'min': interval[0][jdx-1], 'max': interval[1][jdx-1]})
            elif channel == 'VH':
                img = img.select('VH')
                url = img.getThumbURL({'min': interval[0][jdx-1], 'max': interval[1][jdx-1]})
            else: 
                raise Exception("Unknown channel selected.")

            
            id = img.id().getInfo()
            img_data = requests.get(url).content
            img_data = geometry.cut_padding_and_enhance(img_data, padding_size, opts)
            
            if channel == 'RGB':
                img_skip_idx = geometry.Check_image(i, img_data, opts.window_size)
                if img_skip_idx != None:
                    incomplete_images.append(img_skip_idx)  
                        
            if i not in incomplete_images:
                with open(path  + '/' + id + '.png', 'wb') as handler:        
                    handler.write(img_data)

        except:
            if channel == 'RGB':
                return incomplete_images
            else:
                return
        

def ExportCol_Sentinel2(geometry, roi, channel, min, max, aoi_num, j, opts, aoi_names, incomplete_images, padding_size):
    aoi_geometry = ee.Geometry.Polygon(roi ,None,False)
    ffa_s = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
                    .filterDate(ee.Date(opts.start_date), ee.Date(opts.end_date)) \
                    .filterBounds(aoi_geometry) \
                    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', opts.max_cloud_coverage))
    colList = ffa_s.toList(ffa_s.size())

    for i in range(0,opts.numImgs,1):
        try:
            img = ee.Image(colList.get(i)).double().clip(aoi_geometry)
            
            path = os.path.join(opts.save_folder, aoi_names[aoi_num],"Sentinel", "Sentinel-2", channel)
            if not os.path.exists(path):
                os.makedirs(path)
            
            # Exeption beacause to get a RGB channel with the Sentinel-1 we need to correspond each channel and compute the last
            if channel == 'RGB':
                rgb = ['B4','B3','B2']
                url = img.getThumbURL({"min":min[j], "max":max[j],"bands":rgb})
            else:
                url = img.getThumbURL({"min":min[j], "max":max[j],"bands":channel})


            id = img.id().getInfo()
            img_data = requests.get(url).content
            img_data = geometry.cut_padding_and_enhance(img_data, padding_size, opts)
            
            # Check the image
            if channel == 'RGB':
                img_skip_idx = geometry.Check_image(i, img_data, opts.window_size)
                if img_skip_idx != None:
                    incomplete_images.append(i)

            # Image path
            if i not in incomplete_images:
                with open(path  + '/' + id + '.png', 'wb') as handler:        
                    handler.write(img_data)


        except:
            if channel == 'RGB':
                return incomplete_images
            else:
                return
        