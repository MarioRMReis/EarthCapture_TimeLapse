import os
import cv2
import math
import numpy as np
from PIL import Image
from skimage import util
from super_image import EdsrModel, ImageLoader


def enhance_image_save(image_data_path, scale, save_path, image_name) -> None:   
    # Takes the image data path and enhances it
    image_pil = Image.open(image_data_path)
    
    # The maximum scale is 4
    scale = min(scale, 4)
    # Enhance the image, and resize if needed
    if scale > 1:
        model = EdsrModel.from_pretrained('eugenesiow/edsr-base', scale=scale)
        image_input = ImageLoader.load_image(image_pil)
        pil_image_pred = model(image_input)
        image_enh = ImageLoader._process_image_to_save(pil_image_pred)
        
        # Save the image
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        cv2.imwrite(os.path.join(save_path, image_name), image_enh)

            
def cut_padding_and_enhance(image_data, opts, encode = True, band_comb = False) -> bytes:
    # Padding size
    padding_size = ((opts.padding_size,opts.padding_size),(opts.padding_size,opts.padding_size),(0,0))
    # Decode image
    decoded_image = cv2.imdecode(np.frombuffer(image_data, np.uint8), -1)

    # Set scale to 1
    scale = 1
    if opts.super_image or band_comb:
        image_pil = Image.fromarray(cv2.cvtColor(decoded_image, cv2.COLOR_BGR2RGB))
        scale = math.ceil(opts.window_size/decoded_image.shape[0])
        scale = min(scale, 4)   
        # Enhance the image, and resize if needed
        if scale > 1:
            model = EdsrModel.from_pretrained('eugenesiow/edsr-base', scale=scale)
            image_input = ImageLoader.load_image(image_pil)
            pil_image_pred = model(image_input)
            image_enh = ImageLoader._process_image_to_save(pil_image_pred)

            cropped_image = util.crop(image_enh, padding_size)
            cropped_image = cv2.resize(cropped_image, (opts.window_size, opts.window_size))

    # Remove padding if scale is 1, if greater than 1 the image is already cropped
    if scale == 1:     
        # Crop the image to remove the padding
        cropped_image = util.crop(decoded_image, padding_size)
    
    if encode:
        # Encode the image
        _, img_encoded = cv2.imencode('.png', cropped_image)
        cropped_image = img_encoded.tobytes()
    
    return cropped_image
