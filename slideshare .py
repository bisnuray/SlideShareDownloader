"""
Author: Bisnu Ray
https://t.me/itsSmartDev
"""

import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
import os

# Function to load cookies from a file
def load_cookies(file_path):
    with open(file_path, 'r') as file:
        cookies_raw = json.load(file)
        if isinstance(cookies_raw, dict):
            return cookies_raw
        elif isinstance(cookies_raw, list):
            cookies = {}
            for cookie in cookies_raw:
                if 'name' in cookie and 'value' in cookie:
                    cookies[cookie['name']] = cookie['value']
            return cookies
        else:
            raise ValueError("Cookies are in an unsupported format.")

def download_file_from_slideshare(url):
    # Ensure the SlideShare Files directory exists
    if not os.path.exists("SlideShare Files"):
        os.makedirs("SlideShare Files")

    # Extract the base file name from the URL
    parsed_url = urlparse(url)
    base_file_name = parsed_url.path.split('/')[-1]

    # Load cookies
    cookies = load_cookies('slide.json')  # Ensure 'slide.json' is the correct path to your cookies file

    # First request to get the slideshow_id and downloadKey
    first_response = requests.get(url, cookies=cookies)
    slideshow_id, download_key = None, None
    if first_response.status_code == 200:
        soup = BeautifulSoup(first_response.content, 'html.parser')
        slideshow_id_tag = soup.find(attrs={"data-slideshow-id": True})
        if slideshow_id_tag:
            slideshow_id = slideshow_id_tag['data-slideshow-id']
        
        scripts = soup.find_all('script')
        for script in scripts:
            if 'downloadKey' in script.text:
                start = script.text.find('"downloadKey":') + 15
                end = script.text.find(',', start)
                download_key = script.text[start:end].strip('"')
                break

    # Additional request to get CSRF token
    csrf_token = None
    if slideshow_id and download_key:
        csrf_url = "https://www.slideshare.net/csrf_token"
        csrf_response = requests.get(csrf_url, cookies=cookies)
        if csrf_response.status_code == 200:
            csrf_data = json.loads(csrf_response.text)
            csrf_token = csrf_data.get("csrf_token")

    # Second request using the retrieved slideshow_id, downloadKey, and CSRF token
    if slideshow_id and download_key and csrf_token:
        second_url = f"https://www.slideshare.net/slideshow/download?download_key={download_key}&slideshow_id={slideshow_id}"
        headers = {
            'X-Csrf-Token': csrf_token
        }
        second_response = requests.post(second_url, cookies=cookies, headers=headers)
        if second_response.status_code == 200:
            download_data = json.loads(second_response.text)
            file_url = download_data.get("url")
            if file_url:
                file_url = unquote(file_url)
                file_response = requests.get(file_url, stream=True)
                if file_response.status_code == 200:
                    local_filename = f"SlideShare Files/{base_file_name}.pdf"
                    with open(local_filename, 'wb') as f:
                        for chunk in file_response.iter_content(chunk_size=1024):
                            if chunk:
                                f.write(chunk)
                    return local_filename
    return None

# Main script execution
if __name__ == '__main__':
    try:
        url = input("Enter the SlideShare URL: ")
        print("Starting download from SlideShare URL:", url)
        filename = download_file_from_slideshare(url)
        if filename:
            print(f"File downloaded successfully and saved as: {filename}")
        else:
            print("Failed to download the file.")
    except Exception as e:
        print(f"An error occurred: {e}")
