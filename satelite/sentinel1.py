import ee
import os
import requests

def ExportCol_Sentinel1(roi, channel, interval, aoi_num, jdx, timeframe, numImgs, opts, aoi_names):
  # interval-[min[num,num], max[num,num]]: Sentinel-1, Channel settings
  # channel: is the selected band for the sentinel-1
    try:
        for i in range(0,opts.numImgs,1):
            aoi_geometry = ee.Geometry.Polygon(roi ,None,False)
            ffa_s = ee.ImageCollection('COPERNICUS/S1_GRD') \
                            .filterBounds(aoi_geometry) \
                            .filterDate(ee.Date(timeframe[0]), ee.Date(timeframe[1]))
                            
            colList = ffa_s.toList(numImgs); 

            img = ee.Image(colList.get(i)).double().clip(aoi_geometry)
            # Exeption beacause to get a RGB channel with the Sentinel-1 we need to correspond each channel and compute the last
            if channel == 'RGB':
                imgR = img.select('VV')
                imgG = img.select('VH')
                imgB = img.select('VV').divide(img.select('VH'))
                url = ee.Image.rgb(imgR,imgG,imgB).getThumbURL({'min': [interval[0][0], interval[0][1], 0], 'max': [0, 0, 2]})
            else:
                url = img.select(channel).getThumbURL({'min': interval[0][jdx], 'max': interval[1][jdx]})

            id = img.id().getInfo()

            img_data = requests.get(url).content

            path = os.path.join(opts.save_folder, aoi_names[aoi_num], "Sentinel-1", channel)
            if not os.path.exists(path):
                os.makedirs(path)
            # Creates the folder but the flag need to be turned off beacause it will try to makedir after the creation
            try:
                with open(path  + '/' + id + '.tiff', 'wb') as handler:
                    handler.write(img_data)
            except:
            # This just saves the image in the correct folder with the name 'id' (var->'id')
                with open(path + channel + '.tiff', 'wb') as handler:
                    handler.write(img_data)
    except:
            return