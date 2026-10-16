import spacy
from spacy import displacy
import yaml
from pathlib import Path

def ner(sentence):
    """
    Performs Named Entity Recognition
    
    :param sentence: Input sentence
    """
    
    parent = Path(__file__).resolve().parent.parent

    with open(parent / 'config.yaml') as f:
        config = yaml.safe_load(f)
    
    print(sentence)
    nlp = spacy.load('en_core_web_sm')
    doc = nlp(sentence)
    ner_output = [{
                "text": ent.text,
                "start_char": ent.start_char,
                "end_char": ent.end_char,
                "label": ent.label_
            } for ent in doc.ents]
    
    # SAVE viz
    viz = displacy.render(doc, style="ent", page=True, jupyter=False)
    with open(config["features"]["ner"]["path"], "w") as f:
        f.write(viz)

    return ner_output

if __name__ == "__main__":
    print(ner("I am Pranav Rao from IIT Madras"))
