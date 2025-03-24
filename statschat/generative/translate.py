from transformers import pipeline
from dotenv import load_dotenv
import os

#pip install sacremoses
#pip install sentencepiece

# Load the token for Hugging Face
load_dotenv()
sec_key = os.getenv("HF_TOKEN")

text = "The weather outside is good"

#translate = pipeline("translation", model="Rogendo/en-sw")

#print(translate(text))

#def translate_question(text):
    
 #   translation = pipeline("translation", model="Rogendo/en-sw")
    
  #  answer = translation(text)
    
   # print(answer)
    #print(list[(answer)])
    
    #return answer

#translate_question(text)

def translate_question(text):
    
    translation = pipeline("translation", model="Rogendo/en-sw")
        
    translated_text = translation(text)
        
    #print(answer)

    for dictionary in translated_text:
        for translation in dictionary.values():
            print(translation)
            
    return translation

translate_question(text)



