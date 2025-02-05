import ee
import os
import requests

def applyScaleFactors(image):
  opticalBands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
  thermalBands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
  return image.addBands(opticalBands, None, True)\
              .addBands(thermalBands, None, True)


def ExportCol_landsat8(roi, channel, min, max, aoi_num, j, opts, aoi_names):
    for i in range(0,opts.numImgs,1):
        try:
            aoi_geometry = ee.Geometry.Polygon(roi ,None,False)
            ffa_s = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                            .filterDate(ee.Date(opts.start_date), ee.Date(opts.end_date)) \
                            .filterBounds(aoi_geometry)\
                            .filter(ee.Filter.lt('CLOUD_COVER', 60))
            ffa_s = ffa_s.map(applyScaleFactors)
            
            colList = ffa_s.toList(ffa_s.size())

            img = ee.Image(colList.get(i)).double().clip(aoi_geometry)
            
            path = os.path.join(opts.save_folder, aoi_names[aoi_num], "Landsat-8", channel)
            if not os.path.exists(path):
                os.makedirs(path)
            
            # Exeption beacause to get a RGB channel with the Sentinel-1 we need to correspond each channel and compute the last
            if channel == 'RGB':
                rgb = ['SR_B4','SR_B3','SR_B2']
                url = img.getThumbURL({"min":min[j], "max":max[j],"select":rgb})
            else:
                url = img.getThumbURL({"min":min[j], "max":max[j],"select":channel})

            id = img.id().getInfo()

            img_data = requests.get(url).content
  
            with open(path  + '/' + id + '.png', 'wb') as handler:        
                handler.write(img_data)


        except:
                return
            
    