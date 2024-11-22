import ee
import os
import requests


def ExportCol_Sentinel1(geometry, roi, channel, interval, aoi_num, jdx, opts, aoi_names, percentage, incomplete_images):
  # interval-[min[num,num], max[num,num]]: Sentinel-1, Channel settings
  # channel: is the selected band for the sentinel-1
    for i in range(0,opts.numImgs,1):
        try:
            aoi_geometry = ee.Geometry.Polygon(roi ,None,False)
            ffa_s = ee.ImageCollection('COPERNICUS/S1_GRD') \
                            .filterBounds(aoi_geometry) \
                            .filterDate(ee.Date(str(opts.start_date)), ee.Date(str(opts.end_date)))
                            
            colList = ffa_s.toList(opts.numImgs); 

            img = ee.Image(colList.get(i)).double().clip(aoi_geometry)
            
            # Create the save folder for the result images
            path = os.path.join(opts.save_folder, aoi_names[aoi_num], "Sentinel-1", channel)
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
            
            if channel == 'RGB':
                img_skip_idx = geometry.Check_image(i, img_data, percentage, opts.window_size)
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
        
