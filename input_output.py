import os
import re
import traceback
import urllib.request
from urllib.parse import urlparse, unquote
import warnings
from fairgraph.openminds.core import DatasetVersion

#------------------------------
### Input/Ouput handling
#------------------------------

file_default_value = {"url": None, "path": None, "filename": None, "hash": None}

# Get data from EBRAINS Dataset version
def get_url_from_ebrains_dataset (dataset_id, client):
    to_return = None
    try: 
        dataset = DatasetVersion.from_id(dataset_id, client)
        to_return = dataset.repository.resolve(client).iri.value
    except Exception as e:
        warnings.warn("Output data are not DatasetVersion ... Continue")
        to_return = None
    return to_return

# Get data from direct URL
def get_from_url (dataset_url):
    to_return = file_default_value
    try:
        # Test the url
        response = urllib.request.urlopen(dataset_url)
        if response.status == 200:
            to_return["url"] = dataset_url
        else:
            to_return = None
        url_parsed = urlparse(to_return["url"])
        to_return["filename"] = os.path.basename(unquote(url_parsed.path))
        
    except Exception as e:
        to_return = None
    return to_return

#------------------------------
