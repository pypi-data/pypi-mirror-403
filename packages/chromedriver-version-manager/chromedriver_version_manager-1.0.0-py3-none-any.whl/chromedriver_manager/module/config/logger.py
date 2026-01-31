import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional

from .settings import settings


DEFAULT_LOG_PATH = settings.Directories.LOGS_PATH.value

LIBRARY_LOGGER_NAME = 'chromedriver_manager'

class ColoredConsoleFormatter(logging.Formatter):
    """Formatador colorido exclusivo para o Console"""
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    # Formato mais limpo para console
    fmt = "[%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + fmt + reset,
        logging.INFO: grey + fmt + reset,
        logging.WARNING: yellow + fmt + reset,
        logging.ERROR: red + fmt + reset,
        logging.CRITICAL: bold_red + fmt + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)

class FileFormatter(logging.Formatter):
    """Formatador limpo e detalhado para Arquivos (sem cores)"""
    def __init__(self):
        # Formato ISO 8601 para data/hora é padrão na indústria
        fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
        super().__init__(fmt, datefmt="%Y-%m-%d %H:%M:%S")

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retorna o logger da biblioteca.
    Uso: logger = get_logger(__name__)
    """
    if name:
        # Cria um logger filho: chromedriver_manager.core.utils
        return logging.getLogger(f"{LIBRARY_LOGGER_NAME}.{name}")
    return logging.getLogger(LIBRARY_LOGGER_NAME)

def configure_library_logging(
    log_level: int = logging.INFO,
    log_file: Optional[str] = None,
    use_console: bool = True,
    max_bytes: int = 5 * 1024 * 1024, # 5MB
    backup_count: int = 3
):
    """
    Configura os handlers (Console e Arquivo) para a biblioteca.
    Deve ser chamado apenas UMA vez no início da execução da aplicação.
    """
    logger = logging.getLogger(LIBRARY_LOGGER_NAME)
    logger.setLevel(log_level)
    logger.propagate = False # Não propaga para o logger raiz do Python
    
    # Limpa handlers anteriores para evitar duplicação
    if logger.hasHandlers():
        logger.handlers.clear()

    # 1. Configuração do Console (Colorido)
    if use_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(ColoredConsoleFormatter())
        logger.addHandler(console_handler)

    # 2. Configuração do Arquivo (Rotação + Texto Limpo)
    if log_file or DEFAULT_LOG_PATH:
        try:
            # Define caminho do arquivo
            path = Path(log_file) if log_file else Path(DEFAULT_LOG_PATH) / "library.log"
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # RotatingFileHandler: rotaciona quando atinge max_bytes
            file_handler = RotatingFileHandler(
                path, 
                maxBytes=max_bytes, 
                backupCount=backup_count, 
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(FileFormatter())
            logger.addHandler(file_handler)
            
        except Exception as e:
            # Se falhar ao criar arquivo, avisa no console mas não crasha
            print(f"Failed to setup file logging: {e}")

    return logger

# --- Configuração Padrão para Bibliotecas ---
# Isso garante que se o usuário importar a lib e não configurar nada,
# não haverá erro de "No handler found".
logging.getLogger(LIBRARY_LOGGER_NAME).addHandler(logging.NullHandler())
