import logging
import os
from config import Config

def setup_logger(name, log_level=logging.INFO):
    """Настройка логгера с указанным именем"""
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Создаем директорию для логов, если ее нет
    log_dir = os.path.join(os.path.dirname(Config.DB_PATH), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Форматирование
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Файловый обработчик
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f'{name}.log')
    )
    file_handler.setFormatter(formatter)
    
    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
