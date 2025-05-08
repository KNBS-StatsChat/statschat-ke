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

# %%
# Get relevant substring of text on PDF from "more" page
# Define the start and end substrings
start = "About Report "
end = "Share This Page"

# Find the index of the start substring
index_1 = text.find(start)

index_2 = text.find(end, index_1 + len(start))

# Check if both delimiters are found and extract the substring between them
if index_1 != -1 and index_2 != -1:
    pdf_substring = text[index_1 + len(start):index_2]
    
    # add str to end of text variable as anchor point for substring extraction
    pdf_substring = pdf_substring + "Overview-End"
    #print(pdf_substring)
else:
    print("Delimiters not found")

# %% 
# Get relevant substring of text on PDF from "more" page
# Publication substring

start = "Publications "
end = " Overview"

# Find the index of the start substring
index_1 = pdf_substring.find(start)

index_2 = pdf_substring.find(end, index_1 + len(start))

# Check if both delimiters are found and extract the substring between them
if index_1 != -1 and index_2 != -1:
    publication_info = pdf_substring[index_1 + len(start):index_2]
    #print(publication_info) 
else:
    print("Delimiters not found")

# %% 
# Get relevant substring of text on PDF from "more" page
# Overview substring
start = "Overview "
end = " Overview-End"

# Find the index of the start substring
index_1 = pdf_substring.find(start)

index_2 = pdf_substring.find(end, index_1 + len(start))

# Check if both delimiters are found and extract the substring between them
if index_1 != -1 and index_2 != -1:
    overview_info = pdf_substring[index_1 + len(start):index_2]
    #print(overview_info) 
else:
    print("Delimiters not found")
    
# %% 
# put publication info in list to stop coming on separate lines
publication_info_split = publication_info.split()
#print(publication_info_split)

# publication type
publication_type = ' '.join(publication_info_split[:-2])
print(publication_type)

# publication date
publication_date = ' '.join(publication_info_split[-2:])
print(publication_date)
# %% 

