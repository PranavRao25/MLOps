import requests
import os
from dotenv import load_dotenv
import base64

load_dotenv()

HF_TOKEN = os.getenv('HF_TOKEN')

import os

API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# headers = {
#     "Authorization": f"Bearer {HF_TOKEN}",
# }

# def query(payload):
#     response = requests.post(API_URL, headers=headers, json=payload)
#     return response.content

# image_bytes = query({
#     "inputs": "Astronaut riding a horse",
# })

# import io
# from PIL import Image
# image = Image.open(io.BytesIO(image_bytes))
# image.show()
# image.save('temp.jpg')

import io
from PIL import Image


def generate_img(prompt, path_to_save):
  response = requests.post(API_URL, headers=headers, json={'inputs':prompt})
  img = Image.open(io.BytesIO(response.content))
  img.save(path_to_save)
  return {'img_path': f'{path_to_save}'}


if __name__ == '__main__':
  print(generate_img('a cat in a witch hat delivering mail', 'output/mail_witch_cat.jpg'))








# client = InferenceClient(
#     provider="hf-inference",
#     api_key=os.environ["HF_TOKEN"],
# )

# # output is a PIL.Image object
# image = client.text_to_image(
#     "Astronaut riding a horse",
#     model="stabilityai/stable-diffusion-xl-base-1.0",
# )

# image.save('temp.jpg')