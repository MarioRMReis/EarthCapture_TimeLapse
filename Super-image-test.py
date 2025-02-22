from super_image import EdsrModel, ImageLoader
from PIL import Image
import requests
import os

sentinel_path  = "results/green-botics-fields_2-0/Landsat/Landsat-8/RGB"


imgs = os.listdir(sentinel_path)

image = Image.open(os.path.join(sentinel_path,imgs[0]))
print(image.format)

model = EdsrModel.from_pretrained('eugenesiow/edsr-base', scale=4)
inputs = ImageLoader.load_image(image)
preds = model(inputs)

image = ImageLoader._process_image_to_save(preds)