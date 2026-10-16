from flask import Flask, request, jsonify
import yaml
from pathlib import Path
from translate import translate_txt
from tts import tts
from ner import ner

import socket

parent = Path(__file__).resolve().parent.parent

with open(parent / 'config.yaml') as f:
    config = yaml.safe_load(f)

PORT = config['deployment']['port']

app = Flask(__name__)


#####################################################################################################  
@app.route('/')
def root():
    return {
        'message': 'API is alive',
        'container_id': socket.gethostname()
    }
#####################################################################################################  

#####################################################################################################
# translate  
TRANSLATE_ENDPOINT = config['features']['translate']['endpoint']

@app.route(f'/{TRANSLATE_ENDPOINT}', methods=['POST'])
def translate():
    '''
    input data should be of the format 
    {
        'text': '何でもは 知らないわよ 知ってることだけ は〜ん',
        'target': 'en', 
        'source': 'auto' (or any other valid language code)
    }
    '''
    
    data = request.get_json()
    text = data.get('text', '何でもは 知らないわよ 知ってることだけ は〜ん') # 何でもは 知らないわよ 知ってることだけ は〜ん is default
    target = data.get('target', 'en') # en is def
    source = data.get('source', 'auto')
    
    res = translate_txt(txt=text, target=target, source=source)
    return jsonify(res)
#####################################################################################################  

#####################################################################################################
#ner

NER_ENDPOINT = config['features']['ner']['endpoint']

@app.route(f'{NER_ENDPOINT}', methods=['POST'])
def ner_api():
    '''
    input data should be of the format 
    {
        'sentence': 'Hello World!'
    }
    '''

    data = request.get_json()
    text = data.get('sentence', 'I am Pranav Rao from IIT Madras')
    output = ner(sentence=text)

    return jsonify(output)

#####################################################################################################

#####################################################################################################
# image gen

from generate_img import generate_img

GENERATE_IMG_ENDPOINT = config['features']['generate_img']['endpoint']
IMG_PATH = config['features']['generate_img']["path"]

@app.route(f'/{GENERATE_IMG_ENDPOINT}', methods=['POST'])
def generate_image():
    data = request.get_json()
    prompt = data.get('prompt', 'cat delivering postcards')
    output_path = data.get('path_to_save', f'{IMG_PATH}mailcat.jpg')
    
    res = generate_img(prompt, output_path)
    return jsonify(res)

#####################################################################################################

#####################################################################################################

#####################################################################################################
# tts

TTS_ENDPOINT = config['features']['tts']['endpoint']

@app.route(f'{TTS_ENDPOINT}', methods=['POST'])
def tts_api():
    '''
    input data should be of the format 
    {
        'sentence': 'Hello World'
    }
    '''
    
    data = request.get_json()
    text = data.get('sentence', 'Hello World')
    res = tts(sentence=text)
    return jsonify(res)

#####################################################################################################  

#####################################################################################################
if __name__ == '__main__':
    app.run("0.0.0.0", port=PORT)
