# %%
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse
import json
from urllib.request import Request, urlopen

# %% Scrape PDF links from KNBS website
url = "https://www.knbs.or.ke/reports/2025-economic-survey/"

# %%
# works to avoid 403 error
req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
web_byte = urlopen(req).read()

#html = urlopen(url).read()
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
    
    # add str to start of text variable as anchor point for substring extraction
    # add str to end of text variable as anchor point for substring extraction
    pdf_substring = "About-Report" + " " + pdf_substring + "Overview-End"
    #print(pdf_substring)
else:
    print("Delimiters not found")

# %% 
# Get relevant substring of text on PDF from "more" page
# Publication substring

start = "About-Report"
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
    print(overview_info) 
else:
    print("Delimiters not found")
    
# %% 
publication_info_split = publication_info.split()
#print(publication_info_split)

# publication date
publication_date = ' '.join(publication_info_split[-2:])
print(publication_date)

# publication area
publication_theme = ' '.join(publication_info_split[1:-2])
print(publication_theme)

# publication type 
publication_type = ' '.join(publication_info_split[:1])
print(publication_type)

# create empty dictionary
url_dict_abstract = {}

# add keys and values for metadata
url_dict_abstract["pdf_url"] = url
url_dict_abstract["overview"] = overview_info
url_dict_abstract["date"] = publication_date
url_dict_abstract["publication_type"] = publication_type
url_dict_abstract["publication_theme"] = publication_theme