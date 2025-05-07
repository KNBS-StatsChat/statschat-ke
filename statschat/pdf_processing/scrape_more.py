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

print(text)
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