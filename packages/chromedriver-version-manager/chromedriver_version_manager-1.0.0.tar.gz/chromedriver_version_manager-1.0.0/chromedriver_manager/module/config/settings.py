import platform
import shutil
from pathlib import Path
from enum import Enum
import re


MAIN_PATH = Path(__file__).parent.parent.parent

def get_architecture_suffix(architecture: str) -> str:
    match = re.search(r'(\d+)', architecture)
    if match:
        return match.group(1)
    raise ValueError(f"Não foi possível determinar o sufixo de arquitetura para '{architecture}'.")

class Settings:
    
    class Directories(Enum):
        LOGS_PATH = MAIN_PATH / "logs"
        DOWNLOAD_PATH = MAIN_PATH / "download"
        DATA_PATH = MAIN_PATH / "data"

    for dir in Directories:
        dir.value.mkdir(parents=True, exist_ok=True)

    SYSTEM = platform.system()
    ARCHITECTURE = get_architecture_suffix(platform.machine())
    VERSION = platform.version()
    
    if SYSTEM == "Windows":
        PLATFORM = "win"
        PLATFORM_ARCH = f"{PLATFORM}{ARCHITECTURE}"
        EXECUTABLE_NAME = "chromedriver.exe"
    elif SYSTEM == "Linux":
        PLATFORM = "linux"
        PLATFORM_ARCH = f"{PLATFORM}{ARCHITECTURE}"
        EXECUTABLE_NAME = "chromedriver"
    # elif SYSTEM == "Darwin":
    #     PLATFORM = "mac"
    #     PLATFORM_ARCH = f"{PLATFORM}-{ARCHITECTURE}"
    else:
        raise ValueError(f"Sistema operacional '{SYSTEM}' não suportado.")
    

settings = Settings()
