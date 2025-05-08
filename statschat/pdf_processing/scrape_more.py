# %%
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse
import json
from urllib.request import Request, urlopen

# %% Scrape PDF links from KNBS website
base_url = "https://www.knbs.or.ke/reports/gross-county-product-2024/"

# %%
# works to avoid 403 error
req = Request(base_url, headers={'User-Agent': 'Mozilla/5.0'})
web_byte = urlopen(req).read()

#html = urlopen(base_url).read()
soup = BeautifulSoup(web_byte, features="html.parser")

# kill all script and style elements
for script in soup(["script", "style"]):
    script.extract()    # rip it out

# get text
text = soup.body.get_text(separator=' ')

#print(text)
# %%
# need to extract these sentences from text or split based one these

""" About Report 
Publications 
Gross County Product 
December 2024 

Overview 
This report aims to update the economic size of counties. 
These estimates are crucial for counties to assess their revenue potential, 
attract investment in sectors where they have competitive advantage, and monitor economic progress over time. 
The GCP offer a monetary measure of the net market value of all final goods and services produced within 
each of the 47 counties from 2019 to 2023. Below are the key findings from the report. 
There are significant disparities in the size of county economies. 
Nairobi City contributed a notably large share of the total GVA at 27.5 per cent. 
Kiambu, Nakuru, and Mombasa also have substantial contributions, accounting for 5.6 per cent, 5.2 per cent, 
and 4.8 per cent, respectively. However, a total of 33 counties, each contributed less than 2.0 per cent of the overall GVA. 
Gross County Product – 2024 Share This Page """

# %%
# Get relevant substring of text on PDF from more page
# Define the start and end substrings
start = "About Report "
end = "Share This Page"

# Find the index of the start substring
index_1 = text.find(start)

index_2 = text.find(end, index_1 + len(start))

# Check if both delimiters are found and extract the substring between them
if index_1 != -1 and index_2 != -1:
    pdf_substring = text[index_1 + len(start):index_2]
    #print(pdf_substring) 
else:
    print("Delimiters not found")
    
# %% 
# Get relevant substring of text on PDF from more page
# Publication substring

start = "Publications "
end = " Overview"

# Find the index of the start substring
index_1 = pdf_substring.find(start)

index_2 = pdf_substring.find(end, index_1 + len(start))

# Check if both delimiters are found and extract the substring between them
if index_1 != -1 and index_2 != -1:
    publication_info = pdf_substring[index_1 + len(start):index_2]
    print(publication_info) 
else:
    print("Delimiters not found")

# need to add strings in for reference points separate

# add one at start "about report", one at end "share page", one before "overview"