import ee
import os 
import argparse
from datetime import datetime, date, timedelta
from utils import geometry, kml_handler
from satelite import sentinel1, sentinel2, landsat9, landsat8

def get_argparser():
    parser = argparse.ArgumentParser()

    parser.add_argument("--save_folder", type=str, default="results", 
                        help="Path to save the EarthEngine images and the corresponding masks.")
    parser.add_argument("--start_date", type=str, default=(str(date.today() - timedelta(days=64))), 
                        help="Format: YYYY-MM-DD, \nStarting date from witch we are going to start requesting images")
    parser.add_argument("--end_date", type=str, default=(str(date.today())), 
                        help="Format: YYYY-MM-DD, \nEnding date from witch we are going sto stop requesting images")
    parser.add_argument("--window_size", type=int, default=512, 
                        help="Options: 124, 256, 512, 1024.")
    parser.add_argument("--satelite", type=str, default="ALL", 
                        help="Options: Sentinel -> [Sentinel-1, Sentinel-2], Landsat -> [Landsat-8, Landsat-9]: ALL. Separate with a comma the different desired options, Sentinel and Landsat contains the other options. ALL selects all available options.")

    return parser



def main():
    # Get input arguments
    opts = get_argparser().parse_args()
    
    # Gets the dates and the number of days between those dates.
    start_date = datetime.strptime(opts.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(opts.end_date, "%Y-%m-%d")
    
    numDays = end_date.date() - start_date.date()
    opts.numImgs = int(numDays.days)
    
    # Trigger the authentication flow.
    ee.Authenticate()
    # Initialize the library.
    ee.Initialize()
    
    # ----------------------- List of all opted satelites
    aux_sSatelites = opts.satelite.replace(" ", "")
    selectedSatelites = aux_sSatelites.split(',')
    
    # ----------------------- Takes the KML file creates a frame with the chosen window_size and saves a mask of the area.
    # File containing the areas of interest
    kml_files = os.listdir('roi')
    # Sparate all areas of interest, append to the list. Append names to the names list
    aoi_names, aois = kml_handler.kml_reader(kml_files)
    # Get the areas of interst framed and the size of the images that are going to get created
    aoi_square =  geometry.get_squares(aois, opts.window_size)
    # Save the mask
    for idx, a in enumerate(aois):
        path = opts.save_folder + '/' + aoi_names[idx] + '/Mask/'
        geometry.get_mask(path, a, opts.window_size, ["2022-03-12","2022-04-12"])

    skip = True
    if skip == False:
        # ================== Sentinel-1 ============================================
        if "Sentinel-1" in selectedSatelites or "Sentinel" in selectedSatelites or "ALL" in selectedSatelites:
            # -------------------------  Retrives the availabe bands from Sentinel-1
            aoi_bands = ee.Geometry.Polygon(aois[0],None,False)
            ffa_db = ee.Image(ee.ImageCollection('COPERNICUS/S1_GRD') 
                                .filterBounds(aoi_bands)
                                .first() 
                                .clip(aoi_bands))
            # Variables needed to save images
            bands_s1 = ffa_db.bandNames().getInfo()
            bands_s1.remove('angle')
            bands_s1.insert(0,'RGB')

            # Defined values to be the best for these bands
            # intervals - [min[num,num], max[num,num]]
            interval = [[-14, -25], [-7, -7]]
            
            for i_aoi, aoi in enumerate(aoi_square):
                for j_ch, channel in enumerate(bands_s1):
                    if channel == "RGB":
                        incomplete_images_S1 = []    
                        incomplete_images_RGB = sentinel1.ExportCol_Sentinel1(geometry, aoi, channel, interval, i_aoi, j_ch, opts, aoi_names, 90, incomplete_images_S1)
                    else:
                        sentinel1.ExportCol_Sentinel1(geometry, aoi, channel, interval, i_aoi, j_ch, opts, aoi_names, 90, incomplete_images_RGB)

        # ================== Sentinel-2 ============================================
        if  'Sentinel-2' in selectedSatelites or "Sentinel" in selectedSatelites or "ALL" in selectedSatelites:
            # -------------------------  Retrives the availabe bands from Sentinel-2
            aoi_bands = ee.Geometry.Polygon(aois[0],None,False)
            ffa_s2 = ee.Image(ee.ImageCollection('COPERNICUS/S2_HARMONIZED') 
                                .filterBounds(aoi_bands) 
                                .first()
                                .clip(aoi_bands))
            bands_s2 = ffa_s2.bandNames().getInfo()
            aux_bands_s2 =  bands_s2.copy()
            for x in aux_bands_s2: 
                if x in  ['B2', 'B3', 'B4','QA10','QA20','QA60','B10', "MSK_CLASSI_CIRRUS", "MSK_CLASSI_OPAQUE", "MSK_CLASSI_SNOW_ICE"]: 
                    bands_s2.remove(x)
            bands_s2.insert(0,'RGB')

            # Defined best values for these bands, these can be changed.
            min = [0] * len(bands_s2)
            max = [2700, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 3000, 2000, 3200, 2500, 3000]
            
            # Image request
            for i_aoi, roi in enumerate(aoi_square):
                for j_ch, channel in enumerate(bands_s2):
                    if channel == 'RGB':
                        incomplete_images_S2 = []
                        incomplete_images_B2 = sentinel2.ExportCol_Sentinel2(geometry, roi, channel, min, max, i_aoi, j_ch, opts, aoi_names, 90, incomplete_images_S2)
                    else:
                        sentinel2.ExportCol_Sentinel2(geometry, roi, channel, min, max, i_aoi, j_ch, opts, aoi_names, 90, incomplete_images_B2)

        # ================== Landsat-8 ==============================================
        if 'Landsat-8' in selectedSatelites or 'Landsat' in selectedSatelites or "ALL" in selectedSatelites:
            # -------------------------  Retrives the availabe bands from Landsat-8
            aoi_bands = ee.Geometry.Polygon(aois[0],None,False)
            ffa_db = ee.Image(ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') 
                                .filterBounds(aoi_bands)
                                .first() 
                                .clip(aoi_bands))
            # Variables needed to save images
            bands_l8 = ffa_db.bandNames().getInfo()
            bands_l8 =  [b for b in bands_l8 if b not in ['SR_B2', 'SR_B3', 'SR_B4','SR_QA_AEROSOL', 'ST_B10', 'ST_ATRAN', 'ST_CDIST', 'ST_DRAD', 'ST_EMIS', 'ST_EMSD', 'ST_QA', 'ST_TRAD', 'ST_URAD',  'QA_PIXEL', 'QA_RADSAT']]
            bands_l8.insert(0,'RGB')

            # Values can be changed based on the band
            min = [0] * len(bands_l8)
            max = [0.3] * len(bands_l8)
            
            
            for i_aoi, aoi in enumerate(aoi_square):
                for j_ch, channel in enumerate(bands_l8): 
                    landsat8.ExportCol_landsat8(aoi, channel, min, max, i_aoi, j_ch, opts, aoi_names)       

    # ================== Landsat-9 ==============================================                   
    if 'Landsat-9' in selectedSatelites or 'Landsat' in selectedSatelites or "ALL" in selectedSatelites:
        # -------------------------  Retrives the availabe bands from Landsat-9
        aoi_bands = ee.Geometry.Polygon(aois[0],None,False)
        ffa_db = ee.Image(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2') 
                            .filterBounds(aoi_bands)
                            .first() 
                            .clip(aoi_bands))
 
        # Variables needed to save images
        bands_l9 = ffa_db.bandNames().getInfo()
        bands_l9 =  [b for b in bands_l9 if b not in ['SR_B2', 'SR_B3', 'SR_B4', 'SR_QA_AEROSOL', 'ST_B10', 'ST_ATRAN', 'ST_CDIST', 'ST_DRAD', 'ST_EMIS', 'ST_EMSD', 'ST_QA', 'ST_TRAD', 'ST_URAD', 'QA_PIXEL', 'QA_RADSAT']]
        bands_l9.insert(0,'RGB')
        # Values can be changed based on the band
        min = [0] * len(bands_l9)
        max = [0.3] * len(bands_l9)
        
        
        for i_aoi, aoi in enumerate(aoi_square):
            for j_ch, channel in enumerate(bands_l9): 
                landsat9.ExportCol_landsat9(aoi, channel, min, max, i_aoi, j_ch, opts, aoi_names)       
    

if __name__ == '__main__':
    main()  