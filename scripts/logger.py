import logging
import os
from datetime import datetime

class Logger:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not Logger._initialized:
            # Log dizinini oluştur
            log_dir = 'logs'
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # Tarih formatını belirle
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            # Logger'ı yapılandır
            self.logger = logging.getLogger('tubitak_logger')
            self.logger.setLevel(logging.DEBUG)
            
            # Handler'ları temizle (tekrarlanmayı önlemek için)
            if self.logger.handlers:
                self.logger.handlers.clear()
            
            # Genel log dosyası için handler
            general_handler = logging.FileHandler(
                os.path.join(log_dir, f'{current_date}.log'),
                encoding='utf-8'
            )
            general_handler.setLevel(logging.INFO)
            general_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            general_handler.setFormatter(general_formatter)
            
            # Hata log dosyası için handler
            error_handler = logging.FileHandler(
                os.path.join(log_dir, f'{current_date}_error.log'),
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s\n%(exc_info)s'
            )
            error_handler.setFormatter(error_formatter)
            
            # Handler'ları logger'a ekle
            self.logger.addHandler(general_handler)
            self.logger.addHandler(error_handler)
            
            Logger._initialized = True

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message, exc_info=None):
        if exc_info:
            self.logger.error(message, exc_info=exc_info)
        else:
            self.logger.error(message) 