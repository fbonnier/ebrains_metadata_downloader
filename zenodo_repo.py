import os
import json as json
import urllib.request
import traceback
from bs4 import BeautifulSoup
import zipfile
import tarfile
import re

#------------------------------
### Zenodo models
#------------------------------

# Check if the url is a zenodo repository
def is_zenodo_page (url_link: str) -> bool:
    
    if url_link.startswith("https://zenodo.org/"):
        return True
    return False

# Return the list of archive links found
def get_zenodo_code_metadata_from_page (zenodo_page_url: str):
    to_return = None

    code_list = []
    links = []
    zenodo_record_page = None

    try:
        # Get record page in cases the URL has been wrongly saved. The record page is like
        # https://zenodo.org/records/$model_id

        if match := re.search("https://zenodo.org/records/[0-9]+", zenodo_page_url, re.IGNORECASE):
            zenodo_record_page = match.group(0)
        elif match := re.search("https://zenodo.org/record/[0-9]+", zenodo_page_url, re.IGNORECASE):
            zenodo_record_page = match.group(0)

        response = urllib.request.urlopen(zenodo_record_page)
        data = response.read() # a `bytes` object
        soup = BeautifulSoup(data, 'html.parser')
        data_json = json.loads(soup.find(id="recordVersions")["data-record"])["files"]["entries"]
        
        # Get all file packages download links
        for iitem in data_json:
            links.append(data_json[iitem]["links"])

        # Select archive links
        for iitem in links:
            if iitem["self"].endswith("zip") or iitem["self"].endswith("tar") or iitem["self"].endswith("rar"):
                code_list.append({"url": iitem["content"], "filepath": os.path.basename(iitem["self"]), "path": os.path.basename(iitem["self"]).split(".")[0]})
        to_return = code_list[0]
    except Exception as e:
        print (str("".join(traceback.format_exception(e))))
        to_return = None

    return to_return

def get_zenodo_code_path (zenodo_code_link: str):

    to_return = "" 

    return to_return

#------------------------------