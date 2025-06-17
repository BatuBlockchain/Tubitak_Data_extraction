import os
import pyodbc
import sqlite3
from dotenv import load_dotenv
import pandas as pd
import time
from typing import Optional, Any
import traceback
from scripts.logger import Logger
from sqlalchemy import create_engine, text
import urllib.parse

# Logger'ı başlat
logger = Logger()

# .env dosyasını yükle
load_dotenv('db.config')

class DatabaseError(Exception):
    """Veritabanı işlemleri için özel hata sınıfı"""
    def __init__(self, message: str, error_code: Optional[int] = None, details: Optional[Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details
        super().__init__(self.message)

    def __str__(self) -> str:
        error_info = f"Mesaj: {self.message}"
        if self.error_code:
            error_info += f"\nHata Kodu: {self.error_code}"
        if self.details:
            error_info += f"\nDetaylar: {self.details}"
        return error_info

class ConnectionError(DatabaseError):
    """Bağlantı hataları için özel hata sınıfı"""
    def __init__(self, message: str, error_code: Optional[int] = None, details: Optional[Any] = None):
        super().__init__(message, error_code, details)
        self.error_type = "Bağlantı Hatası"

    def __str__(self) -> str:
        return f"{self.error_type}\n{super().__str__()}"

class QueryError(DatabaseError):
    """Sorgu hataları için özel hata sınıfı"""
    def __init__(self, message: str, query: Optional[str] = None, params: Optional[Any] = None, error_code: Optional[int] = None):
        super().__init__(message, error_code)
        self.query = query
        self.params = params
        self.error_type = "Sorgu Hatası"

    def __str__(self) -> str:
        error_info = f"{self.error_type}\n{super().__str__()}"
        if self.query:
            error_info += f"\nSorgu: {self.query}"
        if self.params:
            error_info += f"\nParametreler: {self.params}"
        return error_info

def handle_database_error(error: pyodbc.Error) -> tuple[str, Optional[int], Optional[Any]]:
    """
    Veritabanı hatalarını işler ve uygun hata mesajını döndürür
    
    Returns:
        tuple: (hata_mesajı, hata_kodu, detaylar)
    """
    try:
        error_message = str(error)
        error_code = getattr(error, 'code', None)
        details = getattr(error, 'args', None)
        
        # Bağlantı hataları
        if "timeout" in error_message.lower():
            return "Veritabanı bağlantısı zaman aşımına uğradı", error_code, details
        elif "connection" in error_message.lower():
            return "Veritabanına bağlanılamadı", error_code, details
        elif "authentication" in error_message.lower():
            return "Kimlik doğrulama hatası", error_code, details
        elif "server not found" in error_message.lower():
            return "Veritabanı sunucusu bulunamadı", error_code, details
        
        # Sorgu hataları
        elif "syntax" in error_message.lower():
            return "SQL sözdizimi hatası", error_code, details
        elif "invalid column" in error_message.lower():
            return "Geçersiz sütun adı", error_code, details
        elif "table" in error_message.lower() and "not found" in error_message.lower():
            return "Tablo bulunamadı", error_code, details
        elif "duplicate" in error_message.lower():
            return "Yinelenen kayıt hatası", error_code, details
        elif "constraint" in error_message.lower():
            return "Kısıtlama ihlali hatası", error_code, details
        
        # Genel hatalar
        else:
            return f"Veritabanı hatası: {error_message}", error_code, details
    except Exception as e:
        logger.error("Hata işleme sırasında beklenmeyen bir hata oluştu", e)
        logger.error(f"Traceback: {traceback.format_exc()}")
        return "Beklenmeyen bir hata oluştu", None, str(e)

def execute_query(query: str, params: Optional[Any] = None, fetch: bool = False, many: bool = False, max_retries: int = 3, retry_delay: int = 1):
    """
    SQL sorgusunu çalıştırır, bağlantı hatası durumunda yeniden dener
    
    Args:
        query (str): SQL sorgusu
        params (tuple/list, optional): Sorgu parametreleri
        fetch (bool): True ise sonuçları döndürür, False ise sadece sorguyu çalıştırır
        many (bool): True ise çoklu kayıt işlemi (executemany kullanır)
        max_retries (int): Maksimum yeniden deneme sayısı
        retry_delay (int): Yeniden denemeler arasındaki bekleme süresi (saniye)
    
    Returns:
        DataFrame/None: fetch=True ise sorgu sonuçlarını DataFrame olarak döndürür
    
    Raises:
        ConnectionError: Bağlantı hataları durumunda
        QueryError: Sorgu hataları durumunda
    """
    is_test = os.getenv('IS_TEST', 'false').lower() == 'true'
    
    if is_test:
        try:
            conn = sqlite3.connect('test.db')
            if fetch:
                df = pd.read_sql_query(query, conn, params=params)
                conn.close()
                return df
            else:
                cursor = conn.cursor()
                if params:
                    if many:
                        cursor.executemany(query, params)
                    else:
                        cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
                cursor.close()
                conn.close()
                return True
        except sqlite3.Error as e:
            logger.error("SQLite sorgusu çalıştırılırken hata oluştu", e)
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise DatabaseError(f"SQLite hatası: {str(e)}")
    else:
        retry_count = 0
        last_error = None

        while retry_count < max_retries:
            try:
                connection_string = (
                    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                    f"SERVER={os.getenv('DB_SERVER')};"
                    f"DATABASE={os.getenv('DB_NAME')};"
                    f"UID={os.getenv('DB_USER')};"
                    f"PWD={os.getenv('DB_PASSWORD')}"
                )
                engine = create_engine(f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(connection_string)}")
                
                if fetch:
                    # Fetch işlemi için pandas ile SQLAlchemy engine kullan
                    if params:
                        # Parametreleri dictionary formatına çevir
                        if isinstance(params, (tuple, list)):
                            # ? placeholder'larını :param1, :param2 şeklinde değiştir
                            param_dict = {}
                            modified_query = query
                            for i, param in enumerate(params):
                                param_name = f"param{i+1}"
                                param_dict[param_name] = param
                                modified_query = modified_query.replace('?', f':{param_name}', 1)
                            df = pd.read_sql(text(modified_query), engine, params=param_dict)
                        else:
                            df = pd.read_sql(text(query), engine, params=params)
                    else:
                        df = pd.read_sql(text(query), engine)
                    return df
                else:
                    # Insert/Update işlemleri için SQLAlchemy connection kullan
                    with engine.connect() as conn:
                        if params:
                            if many:
                                # Çoklu kayıt işlemi
                                for param_set in params:
                                    if isinstance(param_set, (tuple, list)):
                                        # ? placeholder'larını :param1, :param2 şeklinde değiştir
                                        param_dict = {}
                                        modified_query = query
                                        for i, param in enumerate(param_set):
                                            param_name = f"param{i+1}"
                                            param_dict[param_name] = param
                                            modified_query = modified_query.replace('?', f':{param_name}', 1)
                                        conn.execute(text(modified_query), param_dict)
                                    else:
                                        conn.execute(text(query), param_set)
                            else:
                                # Tek kayıt işlemi
                                if isinstance(params, (tuple, list)):
                                    # ? placeholder'larını :param1, :param2 şeklinde değiştir
                                    param_dict = {}
                                    modified_query = query
                                    for i, param in enumerate(params):
                                        param_name = f"param{i+1}"
                                        param_dict[param_name] = param
                                        modified_query = modified_query.replace('?', f':{param_name}', 1)
                                    conn.execute(text(modified_query), param_dict)
                                else:
                                    conn.execute(text(query), params)
                        else:
                            conn.execute(text(query))
                        conn.commit()
                    return True
                    
            except pyodbc.Error as e:
                error_message, error_code, details = handle_database_error(e)
                retry_count += 1
                
                if any(err in error_message.lower() for err in ["timeout", "connection", "authentication", "server not found"]):
                    if retry_count < max_retries:
                        logger.warning(f"Bağlantı hatası (Deneme {retry_count}/{max_retries}): {error_message}")
                        logger.warning(f"{retry_delay} saniye sonra yeniden deneniyor...")
                        time.sleep(retry_delay)
                    else:
                        logger.error(f"Maksimum deneme sayısına ulaşıldı. Son hata: {error_message}")
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        raise ConnectionError(error_message, error_code, details)
                else:
                    logger.error(f"Sorgu hatası: {error_message}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise QueryError(error_message, query, params, error_code)
                    
            except Exception as e:
                logger.error("Beklenmeyen bir hata oluştu", e)
                logger.error(f"Traceback: {traceback.format_exc()}")
                raise DatabaseError(f"Beklenmeyen bir hata oluştu: {str(e)}")
