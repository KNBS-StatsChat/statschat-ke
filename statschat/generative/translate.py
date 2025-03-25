# %%
from transformers import pipeline, AutoTokenizer
from dotenv import load_dotenv
import os

# %%
# Load the token for Hugging Face
load_dotenv()
sec_key = os.getenv("HF_TOKEN")

#english_text = "Where can I find the registered births by age of mother and county?"
english_text = "How is core inflation calculated?"

def english_to_swahili(english_text):
    
    translation = pipeline("translation", model="Rogendo/en-sw")
        
    translated_text = translation(english_text)

    for dictionary in translated_text:
        for translation in dictionary.values():
            print(translation)
            
    return translation


english_to_swahili(english_text)

# %%
swahili_text = "Ninaweza kupata wapi watoto walioandikishwa wakati wa umri wa mama na jimbo?"

def swahili_to_english(swahili_text):
    
    translation = pipeline("translation", 
                           model="Rogendo/sw-en",  
                           tokenizer = AutoTokenizer.from_pretrained("Rogendo/sw-en"))
    
    #prompt = """You are an AI assistant that translates text from Swahili to English. 
    # The text will be a question from the public on official statistics from the Kenya National Bureau of Statistics. 
    # Ensure the translated sentence makes sense grammatically in english.
    
    
    #"""
        
    translated_text = translation(swahili_text)
        
    for dictionary in translated_text:
        for translation in dictionary.values():
            print(translation)
            
    return translation

swahili_to_english(swahili_text)

# seems like prompts can't be added to this to finetune

# https://dataloop.ai/library/model/rogendo_sw-en/#capabilities