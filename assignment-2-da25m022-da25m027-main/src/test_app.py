'''
just test script to check if app works
'''


import requests
from pathlib import Path
import yaml

parent = Path(__file__).resolve().parent.parent

with open(parent / 'config.yaml') as f:
    config = yaml.safe_load(f)
    
    
PORT = config['deployment']['port']
BASE_URI = 'http://127.0.0.1:' + str(PORT) + '/'


#################################################################################

def test_translate():
    TRANSLATE_ENDPOINT = config['features']['translate']['endpoint']
    TRANSLATE_URL = BASE_URI + TRANSLATE_ENDPOINT

    translate_data = {
            'text': '何でもは 知らないわよ 知ってることだけ は〜ん',
            'target': 'en', 
            'source': 'auto'
    }

    response = requests.get(BASE_URI)
    assert response.status_code == 200
    print("Translation")
    print(response.json())
    response = requests.post(TRANSLATE_URL, json=translate_data)
    k = response.json()
    print(k)
    for target in ['original text', 'translated', 'target', 'source']:
        assert target in k

    print("Translation done")

#################################################################################

def test_ner():
    NER_ENDPOINT = config['features']['ner']['endpoint']
    NER_ENDPOINT_WO_SLASH = NER_ENDPOINT[1:]
    NER_URL = BASE_URI + NER_ENDPOINT
    # NER_URL is http://127.0.0.1:5000/ner

    ner_data = {
        'sentence': 'I am Pranav Rao from IIT Madras'
    }

    response = requests.get(BASE_URI)
    assert response.status_code == 200
    print("NER")
    print(response.json())
    response = requests.post(NER_URL, json=ner_data)
    k = response.json()
    print(k)
    assert isinstance(k, list)
    assert len(k) > 0
    print("NER Done")

#################################################################################


# testing img gen
def test_image_gen():
    IMG_GEN_ENDPOINT = config['features']['generate_img']['endpoint']
    IMG_GEN_PATH = config['features']['generate_img']["path"]
    IMG_GEN_URL = BASE_URI + IMG_GEN_ENDPOINT

    img_gen_prompt = {
        'prompt': f'a frog eating ice cream', 
        'path_to_save': f'{IMG_GEN_PATH}frog.jpg'
    }

    response = requests.get(BASE_URI)
    assert response.status_code == 200
    print(response.json())
    generated_img_response =  requests.post(IMG_GEN_URL, json=img_gen_prompt)
    print("GEN")
    print(generated_img_response)
    assert "img_path" in generated_img_response.json()
    print("GEN Done")


#################################################################################

# testing with tts
def test_tts():
    TTS_ENDPOINT = config['features']['tts']['endpoint']
    TTS_ENDPOINT_WO_SLASH = TTS_ENDPOINT[1:]
    TTS_URL = BASE_URI + TTS_ENDPOINT

    tts_data = {
        'sentence': 'I am Pranav Rao'
    }

    response = requests.get(BASE_URI)
    assert response.status_code == 200
    print("TTS")
    print(response.json())
    response = requests.post(TTS_URL, json=tts_data)
    k = response.json()
    print(k)
    for target in ["audio", "text"]:
        assert target in k
    print("TTS Done")
