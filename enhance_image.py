import os
from utils import geometry

def get_bands_path():
     # Go through all of the contents of the results folder
    aois = os.listdir('results')
    if not isinstance(aois, list):
        aois = [aois]

    # Get all the satelite types in each AOI, [[Satelite,Landsat],[Satelite,Landsat]]
    satelite_type = []
    for aoi in aois:
        aux = os.listdir(os.path.join('results',aoi))
        # Remove mask from aoi
        aux.remove('Mask')
        if not isinstance(aux, list):
            aux = [aux]
        # Add to the created list
        satelite_type.append(aux)

    # List of each satelite present in the satelite type present on aois [[[]]]
    satelites = []
    for i, aoi in enumerate(aois):
        aux = []
        for sat_t in satelite_type[i]:
            aux.append(os.listdir(os.path.join('results',aoi,sat_t)))
        satelites.append(aux)

    sats_path = []
    for i, aoi in enumerate(aois):
        for sat in satelites[i]:
            for s in sat:    
                if "Landsat" in s:     
                    sats_path.append(os.path.join('results',aoi,'Landsat',s))    
                elif "Sentinel" in s:
                    sats_path.append(os.path.join('results',aoi,'Sentinel',s))
    
    bands_path = []
    for i, s_path in enumerate(sats_path):
        bands = os.listdir(s_path)
        for band in bands:
            bands_path.append(os.path.join(s_path,band))
            
    return bands_path

def main():
    # Pick the scale the max is 4
    scale = 4
    # Get all bands path for each roi
    bands_path = get_bands_path()
    for b_path in bands_path:
        image_list = os.listdir(b_path)
        image_list = [x for x in image_list if not x.startswith('enhanced')]
        for img_name in image_list:
            # Get the image path
            img_path = os.path.join(b_path,img_name)
            save_path = os.path.join(b_path,'enhanced'+'_'+str(scale))
            # Enhance the image
            geometry.enhance_image_save(img_path, scale, save_path, img_name)

    
    
if __name__ == '__main__':
    main()  