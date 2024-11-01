import requests
import urllib.request
import re


#------------------------------
### Github models
#------------------------------

def is_github_page (url_link: str) -> bool:
    if url_link.startswith("https://github.com/"):
        return True
    return False

def is_github_release_page (url_link: str) -> bool:
    
    if "releases/tag/" in url_link:
        return True
    return False

def get_github_download_link_from_homepage (github_homepage_url: str) -> str:

    code = {"url": None, "filepath": None, "path": None}
    # Get zip from master branch, also works for main
    code["url"] = github_homepage_url + "/archive/refs/heads/master.zip"
    # Test zip url
    # return zip direct link on success
    # return None on failure
    response = requests.get(code["url"], stream=True)
    if not response.ok:
        code["url"] = None

    response = urllib.request.urlopen(code["url"])
    if "Content-Disposition" in response.headers.keys():
        dhead = response.headers['Content-Disposition']
        code["filepath"] = re.findall("filename=(.+)", dhead)[0]
    else:
        code["filepath"] = code["url"].split("/")[-1]

    return code


def get_github_download_link_from_release_page (github_release_url: str) -> str:
    
    zip_url = None
    code = {"url": None, "filepath": None, "path": None}

    # Check if url is link to release page
    if is_github_release_page(github_release_url):
        
        # Get zip URL from release page
        code["url"] = github_release_url.replace("/releases/tag/", "/archive/refs/tags/") + ".zip"
        code["filepath"] = code["url"].split("/")[-1]
        
        # Test zip url
        # return zip direct link on success
        # return None on failure
        response = requests.get(code["url"], stream=True)
        if not response.ok:
            code["url"] = None

    return code

#------------------------------
