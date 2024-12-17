import os
import re
import traceback
import urllib.request

#------------------------------
### ModelDB models
#------------------------------

def is_modeldb_page (url_link: str) -> bool:
    
    if url_link.startswith("https://senselab.med.yale.edu/") or url_link.startswith("http://modeldb.science/") or url_link.startswith("http://modeldb.yale.edu/"):
        return True
    return False

def get_modeldb_download_link_from_page (modeldb_page_url: str)-> int: 
    
    modeldb_id = None

    try:
        modeldb_id = re.findall("\d+", modeldb_page_url)[0]
    except Exception as e:
        print (str("".join(traceback.format_exception(e))))
        
    code = {"url": None, "filename": None, "path": None}
    
    code["url"] = get_modeldb_download_link_from_id (int(modeldb_id))
    response = urllib.request.urlopen(code["url"])
    if "Content-Disposition" in response.headers.keys():
        dhead = response.headers['Content-Disposition']
        code["filename"] =  re.findall("filename=(.+)", dhead)[0]
    else:
        code["filename"] = os.path.basename(code["url"])

    return code

def get_modeldb_download_link_from_id (modeldb_id: int):
    
    return (str("http://modeldb.science/eavBinDown?o=" + str(modeldb_id)))
#------------------------------
