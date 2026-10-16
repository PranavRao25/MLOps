from deep_translator import GoogleTranslator

translator = GoogleTranslator()

def translate_txt(txt='何でもは 知らないわよ 知ってることだけ は〜ん', target='en', source='auto'):
    
    translator = GoogleTranslator(
        source=source,
        target=target
    )
    res = translator.translate(txt)
    # print(res)
    
    return {
        'original text': txt,
        f'translated': res,
        'target': target,
        'source': translator.source
    }
    
if __name__ == '__main__':
    print(translate_txt())