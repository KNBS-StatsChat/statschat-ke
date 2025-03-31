# %%
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from dotenv import load_dotenv
import os

# %%
# Load the token for Hugging Face
load_dotenv()
sec_key = os.getenv("HF_TOKEN")

# %%

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
#swahili_text = "Ninaweza kupata wapi watoto walioandikishwa wakati wa umri wa mama na jimbo?"
swahili_text = "Hakuna jibu linalofaa linaloweza kupatikana hata ikiwa habari inayofaa inaweza kupatikana katika shirika la PDF"

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

# lang-codes https://huggingface.co/spaces/UNESCO/nllb/blob/d0a2f64cdae2fae119a127dba13609cb1d0b7542/flores.py

# %%
model_name = "facebook/nllb-200-distilled-600M"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

#prompt = "You are AI assistant who is translating swahili to english"

tokenizer.src_lang = "swh_Latn"
inputs = tokenizer(text="Bei ya mafuta ya gari ilikuwaje 2023?", return_tensors="pt")
translated_tokens = model.generate(
    **inputs, forced_bos_token_id=tokenizer.convert_tokens_to_ids("eng_Latn")
)
print(tokenizer.decode(translated_tokens[0], skip_special_tokens=True))

# %%
text="Bei ya mafuta ya gari ilikuwaje 2023?"

def sw_to_en(text):
    
    model_name = "facebook/nllb-200-distilled-600M"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    #prompt = "You are AI assistant who is translating swahili to english"

    tokenizer.src_lang = "swh_Latn"
    inputs = tokenizer(text, return_tensors="pt")
    translated_tokens = model.generate(
        **inputs, forced_bos_token_id=tokenizer.convert_tokens_to_ids("eng_Latn")
    )
    
    translation = tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
    
    return translation

sw_to_en(text)


# %%
