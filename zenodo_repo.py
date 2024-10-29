import json as json
import urllib.request
import traceback
from bs4 import BeautifulSoup
import zipfile
import tarfile

#------------------------------
### Zenodo models
#------------------------------

# Check if the url is a zenodo repository
def is_zenodo_page (url_link: str) -> bool:
    
    if url_link.startswith("https://zenodo.org/"):
        return True
    return False

# Return the list of archive links found
def get_zenodo_download_link_from_page (zenodo_page_url: str):
    
    links = []
    to_return = []
    
    try:
        response = urllib.request.urlopen(zenodo_page_url)
        data = response.read() # a `bytes` object
        soup = BeautifulSoup(data, 'html.parser')
        data_json = json.loads(soup.find(id="recordVersions")["data-record"])["files"]["entries"]
        
        # Get all file packages download links
        for iitem in data_json:
            links.append(data_json[iitem]["links"])
            # print(data_json[iitem]["links"])

        # Select archive links
        for iitem in links:
            if iitem["self"].endswith("zip") or iitem["self"].endswith("tar"):
                to_return.append(iitem["content"])

    except Exception as e:
        print (str("".join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))))
        links = None

    return to_return

#------------------------------