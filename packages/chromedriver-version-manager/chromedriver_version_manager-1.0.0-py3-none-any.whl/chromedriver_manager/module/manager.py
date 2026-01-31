import shutil
import json
import os
from datetime import datetime
from pathlib import Path

from .core.utils import (
    settings,
    get_version,
    fetch_data_from_api,
    find_matching_driver_version,
    find_download_link,
    download_file,
    get_chrome_driver_path,
    random_generator,
    Commands
)
from .config.logger import (
    logging,
    get_logger,
    configure_library_logging,
)


# configure_library_logging(
#     log_level=logging.DEBUG,
#     use_console=True
#     # log_file="meu_log_customizado.log" # Opcional
# )


logger = get_logger(__name__)

class ChromeDriverManager:
    driver_path: str = None
    extract_path: str = None
    CACHE_FILE_NAME = settings.Directories.DATA_PATH.value / "drivers_cache.json"
    TEMP_FOLDER = settings.Directories.DOWNLOAD_PATH.value
    
    def __init__(self):
        pass

    def delete_temp(self): 
        shutil.rmtree(self.TEMP_FOLDER, ignore_errors=True)
        self.TEMP_FOLDER.mkdir(parents=True, exist_ok=True)

    def _get_cache_file_path(self) -> Path:
        return self.TEMP_FOLDER / self.CACHE_FILE_NAME

    def _load_cache(self):
        cache_file = self._get_cache_file_path()
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_cache(self, chrome_version: str, driver_path: str):
        cache_data = {
            "chrome_version": chrome_version,
            "driver_path": str(driver_path),
            "timestamp": datetime.now().isoformat()
        }
        with open(self._get_cache_file_path(), 'w') as f:
            json.dump(cache_data, f, indent=4)

    def get_driver_path(self) -> str:
        chrome_version = get_version(Commands.GET_CHROME_VERSION)
        logger.info(f"Chrome version detected: {chrome_version}")
        
        cache = self._load_cache()
        cached_version = cache.get("chrome_version")
        cached_path = cache.get("driver_path")

        if cached_version == chrome_version and cached_path and os.path.exists(cached_path):
            logger.info(f"Driver cached found for Chrome {chrome_version} at: {cached_path}")
            self.driver_path = cached_path
            return cached_path

        logger.info("No valid cache found. Downloading new driver...")

        # driver_version = get_version(Commands.GET_DRIVER_VERSION)
        
        data = fetch_data_from_api()

        downloader_info = find_matching_driver_version(chrome_version, data)
        logger.debug(f"Matching driver version info: {downloader_info}")

        download_link = find_download_link(downloader_info)
        logger.debug(f"Download link: {download_link}")
        
        downloaded_file_path = download_file(
            download_link,
            self.TEMP_FOLDER
        )
        logger.debug(f"Downloaded file path: {downloaded_file_path}")
        
        folder_name = f"zipContent-{datetime.now().strftime('%d%m%Y%H%M%S%f')}-{random_generator()}"
        
        self.extract_path = self.TEMP_FOLDER / folder_name
        
        driver_path = get_chrome_driver_path(
            downloaded_file_path,
            extract_to=self.extract_path,
        )
        
        logger.info(f"New ChromeDriver path: {driver_path}")
        
        self.driver_path = driver_path
        
        self._save_cache(chrome_version, driver_path)
        
        return driver_path
