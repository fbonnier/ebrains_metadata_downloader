import re
import traceback


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
        print (str("".join(traceback.format_exception(etype=type(e), value=e, tb=e.__traceback__))))
        
    return get_modeldb_download_link_from_id (int(modeldb_id))

def get_modeldb_download_link_from_id (modeldb_id: int):
    
    return (str("http://modeldb.science/eavBinDown?o=" + str(modeldb_id)))
#------------------------------
