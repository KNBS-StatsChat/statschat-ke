# %%
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urlparse
import json
from tqdm import tqdm

# %%

# Update for latest PDFs or setup when using for first time
PDF_FILES = "SETUP"

# Set relative paths
if PDF_FILES == "SETUP":
    DATA_DIR = Path.cwd().joinpath("data/pdf_downloads")
    print("STARTING DATABASE SETUP. IN PROGRESS...")
    
elif PDF_FILES == "UPDATE":
    DATA_DIR = Path.cwd().joinpath("data/latest_pdf_downloads")
    print("STARTING DATABASE UPDATE. IN PROGRESS...")

# Check if DATA_DIR exists, if not, create the folder
if not DATA_DIR.exists():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
# %%
# Initialise empty dict to store url and download links
url_dict = {}

# %%
# get all webpages on KNBS website that have PDFs and add them to a list

all_pdf_links = []

# select page for downloads to start from
# with 1 being the latest

page = 37
base_url = f'https://www.knbs.or.ke/all-reports/page'

continue_search = True

while continue_search:
    url = base_url + str(page) + '/'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Break the loop if no more quotes are found
    pdf_links = [
        a["href"] for a in soup.find_all("a", href=True) if a["href"].endswith(".pdf")
    ]
    
    if len(pdf_links) == 0:
        print('HAVE STOPPED GETTING WEBPAGES')
        continue_search = False
    
    page += 1
    all_pdf_links.append(url)

print('FINISHED COMPILING LINKS. START DOWNLOADS')

# %%
# print counter

# %%
# removes last append to list as that webpage has no pdfs (USE THIS)

all_pdf_links = all_pdf_links[:-1]
all_pdf_links

# %%
# gets links for every PDF from every KNBS webpage and adds to a list

all_knbs_pdf_file_links = []

for pdf_file in all_pdf_links:
    
    url = pdf_file
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    pdf_links = [
        a["href"] for a in soup.find_all("a", href=True) if a["href"].endswith(".pdf")
    ]
    
    all_knbs_pdf_file_links.append(pdf_links)

# %%
# gets page range for PDFs to loop through multiple lists made

pdf_page_range = len(all_knbs_pdf_file_links)

# %%
#total downloads
total_downloads = []
    
for i in range(pdf_page_range):
    for pdf in all_knbs_pdf_file_links[i]:
        total_downloads.append(pdf)

# downloads PDFs to relevant folder

counter = 0 

for i in range(pdf_page_range):
    for pdf in tqdm(all_knbs_pdf_file_links[i],
                    desc="DOWNLOADING PDF FILES",
                    bar_format='[{elapsed}<{remaining}] {n_fmt}/{total_fmt} | {l_bar}{bar} {rate_fmt}{postfix}', 
                    colour='yellow',
                    total = len(total_downloads)):

        url = pdf
        parsed_url = urlparse(url)
        pdf_name = parsed_url.path
        actual_pdf_file_name = pdf_name[28:]

        response = requests.get(url)
        file_path = f"{DATA_DIR}/{actual_pdf_file_name}"

        # Save file in binary mode if request is successful,
        # return error message if request fails.
        if response.status_code == 200:
            with open(file_path, "wb") as file:
                file.write(response.content)
                #print(f"File {actual_pdf_file_name} downloaded successfully")
            
            counter += 1
        
        else:
            print(f"ERROR. Failed to download file {actual_pdf_file_name}")
            
        
        # update dictionary
        url_dict[actual_pdf_file_name] = url
        #print(url_dict[actual_pdf_file_name])

# Export url link dictionary to json file
with open(f"{DATA_DIR}/url_dict.json", "w") as json_file:
    json.dump(url_dict, json_file, indent=4)
    print("url_dict saved to url_dict.json")

print("Finished PDF downloads")