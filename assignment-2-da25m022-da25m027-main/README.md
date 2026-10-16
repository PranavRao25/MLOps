# assignment-2 da5402: the multi-modal orchestrated cluster

# Assignment 2 : The Multi-Modal Orchaestrated Cluster

Authors : Pranav Rao (PranavRao25) and Sanved Bangale (uhloofstardust)
Roll Nos: DA25M022 and DA25M027

## Video Demo Link

[video demo](https://drive.google.com/drive/folders/10S6qqgUVIuuHTxgncjN75xMPchrnEXBO?usp=sharing)

## Named Entity Recognition (NER)

This feature takes a string input and displays the named entities present in the sentence. It is served at the API endpoint ```/ner```. It internally runs using Spacy.

<p>For example:</p>
<p>Text : Why Apple is looking at buying U.K. startup for $1 billion ?</p>
Output:

- Apple 4 9 ORG
- U.K. 31 35 GPE
- $1 billion 48 58 MONEY

## Speech Synthesis (TTS)

This feature takes a string input and produces an audio file of a person saying that sentence. It is served at the API endpoint ```/tts```. It internally runs using pyt2s.

Input: I am Pranav Rao
Output:
<audio controls>
  <source src="output/tts.mp3" type="audio/mpeg">
  Your browser does not support the audio element.
</audio>


## Translation

It is served at the API endpoint `/translate`. It uses a python wrapper for Google Translate.

Input : '何でもは 知らないわよ 知ってることだけ は〜ん'
Output: "I don't know everything. I only know what I know." 

## Image Generation

It is served at the API endpoint `/generate_img`. It uses the HF Interface for `stabilityai/stable-diffusion-xl-base-1.0`.

<img src="mail_cat.jpg" alt="Cat postman">

## structure of the folder:
```
.
├── cat.jpg
├── cat_witch_hat.jpg
├── config.yaml
├── conflict.md
├── debug.log
├── deployment_log.csv
├── mail_cat.jpg
├── mail_witch_cat.jpg
├── output
│   ├── frog.jpg
│   ├── ner.html
│   └── tts.mp3
├── progress.md
├── README.md
├── requirements.txt
├── src
│   ├── app.py
│   ├── generate_img.py
│   ├── ner.py
│   ├── output
│   ├── __pycache__
│   │   ├── generate_img.cpython-313.pyc
│   │   ├── ner.cpython-313.pyc
│   │   ├── test_app.cpython-313-pytest-8.3.5.pyc
│   │   ├── test_ner.cpython-313-pytest-8.3.5.pyc
│   │   ├── translate.cpython-313.pyc
│   │   └── tts.cpython-313.pyc
│   ├── test_app.py
│   ├── test_ner.py
│   ├── test_translate.py
│   ├── test_tts.py
│   ├── translate.py
│   └── tts.py
└── temp.jpg
```

## Instructions:
- run `pip install -r requirements.txt`
- run `python -m spacy download en_core_web_sm`
- run the test scripts
- make sure to have a huggingface token in a .env file in the project directory as an env var called `HF_TOKEN`

