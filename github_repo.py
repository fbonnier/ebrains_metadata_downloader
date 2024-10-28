import requests

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

    # Get zip from master branch, also works for main
    zip_url = github_homepage_url + "/archive/refs/heads/master.zip"

    # Test zip url
    # return zip direct link on success
    # return None on failure
    response = requests.get(zip_url, stream=True)
    if not response.ok:
        zip_url = None

    return zip_url


def get_github_download_link_from_release_page (github_release_url: str) -> str:
    
    zip_url = None

    # Check if url is link to release page
    if is_github_release_page(github_release_url):
        
        # Get zip URL from release page
        zip_url = github_release_url.replace("/releases/tag/", "/archive/refs/tags/")
        zip_url = zip_url + ".zip"
        
        # Test zip url
        # return zip direct link on success
        # return None on failure
        response = requests.get(zip_url, stream=True)
        if not response.ok:
            zip_url = None

    return zip_url

#------------------------------
