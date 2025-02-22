
import ee
import os
import cv2
import math
import pickle
import requests
import numpy as np
from PIL import Image
from skimage import util
from super_image import EdsrModel, ImageLoader

# new_aoi() takes the irreguar area of interest and finds the new coords of a square containg the old area
def new_squareAOI(size_square, aoi):
    h_aux = size_square[1]/2
    w_aux = size_square[0]/2

    # With the size of the 128x128 square in coords we can add half of those values to the calculated center of the Aoi
    #   and find the coords of all 4 corners of our new AOI (Does not deal with areas of interst that do not fit a 128 by 128)
    # Find centeroid ----------------------------
    siz = len(aoi[0])
    list_width = []
    list_height = []
    for i in range(siz): 
        list_width.append(aoi[0][i][0])
        list_height.append(aoi[0][i][1])

    max_width = max(list_width)
    min_width = min(list_width)
    max_height = max(list_height)
    min_height = min(list_height)
    
    centroid_width = (max_width+min_width)/2
    centroid_height = (max_height+min_height)/2

    #if ((centroid_width + w_aux) > max_width) or ((centroid_height + h_aux) > max_height) or ((centroid_width - w_aux) < min_width) or((centroid_height - h_aux) < min_height):
        #raise Exception("Area of interst outside of choosen frame.")
        

    aoi_new = [[[(centroid_width-w_aux), (centroid_height+h_aux)], [(centroid_width-w_aux), (centroid_height-h_aux)], [(centroid_width+w_aux), (centroid_height-h_aux)], [(centroid_width+w_aux), (centroid_height+h_aux)]]]
    
    return aoi_new
    
            
def get_squares(aois, inp_size, padding_size):
    # Buffer for the image
    inp_size = inp_size + (padding_size*2)

    if os.path.isfile('utils/coords_dict.pkl'):
        with open('utils/coords_dict.pkl', 'rb') as f:
            coords_dict = pickle.load(f)
    else:
        # Tested vale to start creating the value list, at the moment the relation of coords and pixels are a bit off so a bit of trial and error is required.
        S128 = [0.014854925631009616, 0.011377373345324189]
        coords_dict = {
            128:S128
        }
        with open('utils/coords_dict.pkl', 'wb') as f:
            pickle.dump(coords_dict, f)
            
    aois_square = []
    if inp_size in coords_dict:
        size_square = coords_dict[inp_size]
        for aoi in aois:
            aois_square.append(new_squareAOI(size_square, aoi))
    else:
        flag = False
        add_value = 0.000005
        S128 = coords_dict[128]
        size_square = [(S128[0]*inp_size)/128, (S128[1]*inp_size)/128]
        while flag == False:
            aois_square = []
            for aoi in aois:
                aois_square.append(new_squareAOI(size_square,aoi))
                
            aux = check_imgShape(aois_square[0], inp_size)
            if aux == 0:
                coords_dict[inp_size] = size_square 
                with open('utils/coords_dict.pkl', 'wb') as f:
                    pickle.dump(coords_dict, f)
                flag = True
            elif aux == 1:
                size_square = [size_square[0] - (add_value), size_square[1] - (add_value)]
            elif aux == 2:
                size_square = [size_square[0] + add_value, size_square[1] + add_value]
            elif aux == 3:
                size_square = [size_square[0] - (add_value), size_square[1] + (add_value)]
            elif aux == 4:
                size_square = [size_square[0] + (add_value), size_square[1] - (add_value)]
            elif aux == 5:
                size_square = [size_square[0] - (add_value), size_square[1]]
            elif aux == 6:
                size_square = [size_square[0] + (add_value), size_square[1]]
            elif aux == 7:
                size_square = [size_square[0], size_square[1] - (add_value)]
            elif aux == 8:
                size_square = [size_square[0], size_square[1] + (add_value)]
                
    
    return aois_square

def get_mask(path, aoi, size, timeframe):
    # Inputs:
    #     - path -> path to the aoi saved images
    #     - aoi -> Area of interest of the landfield
    #     - size = [sizeX, sizeY] -> size of the mask, (ie: 128x128, 256x256, 354x128...)
    aoi_mask = ee.Geometry.Polygon(aoi,None,False)
    ffa_s2 = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
                            .filterBounds(aoi_mask) \
                            .filterDate(ee.Date(timeframe[0]), ee.Date(timeframe[1]))
    colList = ffa_s2.toList(30)
    # This part get's the land area image needed to create the mask --------------
    img = ee.Image(colList.get(-1)).double().clip(aoi_mask)
    rgb = ['B4','B3','B2']
    url = img.getThumbURL({"min":-200000, "max":-200000,"bands":rgb})

    img_data = requests.get(url).content
    
    img_aux = cv2.imdecode(np.frombuffer(img_data, np.uint8), -1)

    # Create mask ----------------------------------------------------------------
    # img_aux.shape -> [x,y,z]
    x = img_aux.shape[0]
    y = img_aux.shape[1]
    x_sum = math.ceil((size-x)/2)
    y_sum = math.ceil((size-y)/2)

    img_zeros = np.zeros([size, size, 3])
    img_zeros[x_sum:(x_sum+x), y_sum:(y_sum+y), :] = img_aux[:,:,0:3]
    try:
        os.makedirs(path)
        cv2.imwrite(path +'mask.jpg', img_zeros)
    except:
        cv2.imwrite(path +'mask.jpg', img_zeros)


def Check_image(idx, image, size):
    # Image in cv2
    decoded = cv2.imdecode(np.frombuffer(image, np.uint8), -1)
    if decoded.shape[:2] == (size, size):
        size_match = True
    else:
        size_match = False
        
    if size_match == False or np.any(decoded[:,:,3] == 0):
        return idx
    else:
        return
    
def check_imgShape(aoi, size):
    aoi_mask = ee.Geometry.Polygon(aoi,None,False)
    ffa_s2 = ee.ImageCollection('COPERNICUS/S2_HARMONIZED') \
                            .filterBounds(aoi_mask) \
                            .filterDate(ee.Date("2022-03-12"), ee.Date("2022-04-12"))
    colList = ffa_s2.toList(30)
    # This part get's the land area image needed to create the mask --------------
    img = ee.Image(colList.get(-1)).double().clip(aoi_mask)
    rgb = ['B4','B3','B2']
    url = img.getThumbURL({"min":-200000, "max":-200000,"bands":rgb})

    img_data = requests.get(url).content

    img_aux = cv2.imdecode(np.frombuffer(img_data, np.uint8), -1)
    

    if img_aux.shape[0] == size and img_aux.shape[1] == size:
        return 0
    elif img_aux.shape[0] > size and img_aux.shape[1] > size:
        return 1
    elif img_aux.shape[0] < size and img_aux.shape[1] < size:
        return 2
    elif img_aux.shape[0] > size and img_aux.shape[1] < size:
        return 3
    elif img_aux.shape[0] < size and img_aux.shape[1] > size:
        return 4
    elif img_aux.shape[0] == size and img_aux.shape[1] > size:
        return 5
    elif img_aux.shape[0] == size and img_aux.shape[1] < size:
        return 6
    elif img_aux.shape[0] > size and img_aux.shape[1] == size:
        return 7
    elif img_aux.shape[0] < size and img_aux.shape[1] == size:
        return 8  
    else:
        raise Exception("New case needs implementation.")
    
    
    
def cut_padding_and_enhance(image_data, ps, opts):
    # Padding size
    padding_size = ((ps,ps),(ps,ps),(0,0))
    # Decode image
    decoded_image = cv2.imdecode(np.frombuffer(image_data, np.uint8), -1)
    
    if opts.super_image:
        image_pil = Image.fromarray(cv2.cvtColor(decoded_image, cv2.COLOR_BGR2RGB))
        scale = math.ceil(opts.window_size/decoded_image.shape[0])
        if scale > 4:
            scale = 4
        if scale > 1:
            model = EdsrModel.from_pretrained('eugenesiow/edsr-base', scale=scale)
            image_input = ImageLoader.load_image(image_pil)
            image_pil_pred = model(image_input)
            image_enh = ImageLoader._process_image_to_save(image_pil_pred)
            cropped_image = util.crop(image_enh, padding_size)
            cropped_image = cv2.resize(cropped_image, (opts.window_size, opts.window_size))
        else:
            # Crop the image to remove the padding
            cropped_image = util.crop(decoded_image, padding_size)
    else:     
        # Crop the image to remove the padding
        cropped_image = util.crop(decoded_image, padding_size)
      
    # Encode the image
    _, img_encoded = cv2.imencode('.png', cropped_image)
    encoded_image_bytes = img_encoded.tobytes()
    
    return encoded_image_bytes