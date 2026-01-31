import re
import os
import subprocess
import zipfile
import random
import string
import requests
from urllib.parse import urlparse

from chromedriver_manager.module.config.settings import settings

class Commands:
    GET_CHROME_VERSION = 'google-chrome --version'
    GET_DRIVER_VERSION = "chromedriver --version"
    
    if settings.SYSTEM == "Windows":
        GET_CHROME_VERSION = 'reg query "HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon" /v version'

def random_generator(size: int=10, chars=string.ascii_lowercase + string.digits) -> str:
    return ''.join(random.choice(chars) for _ in range(size))

def get_version(command):
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', result.stdout + result.stderr)
    return match.group(1) if match else "N/A"

def fetch_data_from_api() -> list:
    url = 'https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json'
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for HTTP errors
    data = response.json()
    return data.get('versions', [])

def download_file(url: str, dest_path: str) -> str:
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for HTTP errors
    filename = os.path.basename(urlparse(url).path)
    file_path = os.path.join(dest_path, filename)
    with open(file_path, 'wb') as file:
        file.write(response.content)
    return file_path

def find_matching_driver_version(chrome_version: str, data: list) -> dict:
    for item in data:
        version = item.get('version')
        if version.startswith(chrome_version.split('.')[0]):
            return item
    raise ValueError("No matching driver version found.")

def find_download_link(downloader_info: dict) -> str:
    downloads = downloader_info.get('downloads', {}).get('chromedriver', [])
    for download in downloads:
        if download.get('platform') == settings.PLATFORM_ARCH:
            return download.get('url')
    raise ValueError(f"No download link found for platform: {settings.PLATFORM_ARCH}")

def unzip_file(zip_path: str, extract_to: str = "zipContent", delete_zip_after: bool = True):
    if not os.path.exists(zip_path):
        print(f"Erro: O arquivo '{zip_path}' não foi encontrado.")
        return

    print(f"Iniciando extração de: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    caminho_absoluto = os.path.abspath(extract_to)
    print(f"Extração concluída. Arquivos extraídos para: {caminho_absoluto}")

    if delete_zip_after:
        os.remove(zip_path)
    
    return caminho_absoluto

def get_chrome_driver_path(zip_path: str, extract_to: str = "zipContent", delete_zip_after: bool = True) -> str:
    extract_path = unzip_file(zip_path, extract_to, delete_zip_after)
    driver_path = os.path.join(
        extract_path,
        extract_to,
        f'chromedriver-{settings.PLATFORM_ARCH}',
        settings.EXECUTABLE_NAME
        )
    if not os.path.exists(driver_path):
        raise FileNotFoundError(f"O ChromeDriver não foi encontrado em: {driver_path}")
    return driver_path
