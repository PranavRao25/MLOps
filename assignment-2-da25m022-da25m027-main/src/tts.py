import base64
from email.mime import audio
from pyt2s.services import speechify
import io
import yaml
from pathlib import Path

def tts(sentence):
    """
    Text-To-Speech Feature
    
    :param sentence: Input sentence
    """
    
    parent = Path(__file__).resolve().parent.parent

    with open(parent / 'config.yaml') as f:
        config = yaml.safe_load(f)

    data = speechify.requestTTS(sentence, voice = speechify.Voice.Jason)

    encoded_audio = {
        "audio": base64.b64encode(data).decode(),
        "text": sentence
    }

    # Save mem_stream
    mem_stream = io.BytesIO(data)
    mem_stream.seek(0)
    with open(f"{config['features']['tts']['path']}", "wb") as f:
       f.write(data)
    
    return encoded_audio

if __name__ == "__main__":
    print(tts("I am Pranav Rao"))
