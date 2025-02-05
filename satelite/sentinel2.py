import ee
import os
import requests

def ExportCol_Sentinel2(geometry, roi, channel, min, max, aoi_num, j, opts, aoi_names, percentage, incomplete_images):
    for i in range(0,opts.numImgs,1):
        try:
            aoi_geometry = ee.Geometry.Polygon(roi ,None,False)
            ffa_s = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
                            .filterDate(ee.Date(opts.start_date), ee.Date(opts.end_date)) \
                            .filterBounds(aoi_geometry) \
                            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            colList = ffa_s.toList(ffa_s.size())

            img = ee.Image(colList.get(i)).double().clip(aoi_geometry)
            
            path = os.path.join(opts.save_folder, aoi_names[aoi_num], "Sentinel-2", channel)
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
            
            # Check the image
            if channel == 'RGB':
                img_skip_idx = geometry.Check_image(i, img_data, percentage, opts.window_size)
                if img_skip_idx != None:
                    incomplete_images.append(img_skip_idx)

            # Image path
            if i not in incomplete_images:
                with open(path  + '/' + id + '.png', 'wb') as handler:
                    handler.write(img_data)


        except:
            if channel == 'RGB':
                return incomplete_images
            else:
                return
        