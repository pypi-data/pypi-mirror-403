import shutil

from .core.utils import (
    settings,
    get_version,
    fetch_data_from_api,
    find_matching_driver_version,
    find_download_link,
    download_file,
    get_chrome_driver_path,
    Commands
)

def get_driver_path() -> str:

    chrome_version = get_version(Commands.GET_CHROME_VERSION)
    print(f"Chrome version: {chrome_version}")
    
    driver_version = get_version(Commands.GET_DRIVER_VERSION)
    print(f"Driver version: {driver_version}")
    
    data = fetch_data_from_api()

    downloader_info = find_matching_driver_version(chrome_version, data)
    print(f"Matching driver version info: {downloader_info}")

    download_link = find_download_link(downloader_info)
    print(f"Download link: {download_link}")
    
    temp_folder = settings.Directories.TEMP_PATH.value

    shutil.rmtree(temp_folder, ignore_errors=True)
    temp_folder.mkdir(parents=True, exist_ok=True)

    downloaded_file_path = download_file(
        download_link,
        temp_folder
    )
    print(f"Downloaded file path: {downloaded_file_path}")
    
    driver_path = get_chrome_driver_path(
        downloaded_file_path,
        extract_to=temp_folder / "zipContent",
    )
    
    print(f"ChromeDriver path: {driver_path}")
    
    return driver_path
