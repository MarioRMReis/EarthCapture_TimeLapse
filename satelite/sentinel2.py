import ee
import os
import requests
from utils import geometry

def ExportCol_Sentinel2(roi, channel,  min, max, idx, jdx, percentage, incomplete_images, opts, aoi_names):
  # 
  for i in range(0,opts.numImgs,1):
    try:
        aoi_geometry = ee.Geometry.Polygon(roi ,None,False)
        ffa_s = ee.ImageCollection('COPERNICUS/S2') \
                        .filterBounds(aoi_geometry) \
                        .filterDate(ee.Date(opts.starting_date), ee.Date(opts.ending_date)) \
                        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
        colList = ffa_s.toList(ffa_s.size());                   

        img = ee.Image(colList.get(i)).double().clip(aoi_geometry)
        # Exeption beacause to get a RGB channel with the Sentinel-1 we need to correspond each channel and compute the last
        if channel == 'RGB':
            rgb = ['B4','B3','B2']
            url = img.getThumbURL({"min":min[jdx], "max":max[jdx],"bands":rgb})
        else:
            url = img.getThumbURL({"min":min[jdx], "max":max[jdx],"bands":channel})

        id = img.id().getInfo()
        id_short = id[16::]

        img_data = requests.get(url).content
      
        # Check the image
        if channel == 'B2':
            img_idx = geometry.Check_image(i, img_data, percentage)
            if img_idx != None:
                incomplete_images.append(img_idx)
      
        # Image path
        path =  + '/' + aoi_names[idx] + '/Sentinel-2/' + id_short + '/' # new path needed !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        if i not in incomplete_images:
            # Creates the folder but the flag need to be turned off beacause it will try to makedir after the creation
            try:
                os.makedirs(path)
                with open(path + channel + '.tiff', 'wb') as handler:
                    handler.write(img_data)
            except:
                # This just saves the image in the correct folder with the name 'id' (var->'id')
                with open(path + channel + '.tiff', 'wb') as handler:
                    handler.write(img_data)
        else:
                path = "redothepath"
                try:
                    os.makedirs(path)
                    with open(path + channel + '.tiff', 'wb') as handler:
                        handler.write(img_data)
                except:
                    # This just saves the image in the correct folder with the name 'id' (var->'id')
                    with open(path + channel + '.tiff', 'wb') as handler:
                        handler.write(img_data)

    except:
        if channel == 'B2':
            return incomplete_images
        else:
            return
        