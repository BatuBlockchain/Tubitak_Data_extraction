import sqlite3
from typing import List, Dict, Any
import pandas as pd
import traceback
from scripts.logger import Logger
from scripts.db_connection import execute_query

# Logger'ı başlat
logger = Logger()

def init_test_db():
    """Test veritabanını başlatır"""
    try:
        # feature_list tablosunu oluştur
        execute_query("""
            CREATE TABLE IF NOT EXISTS feature_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feature_name TEXT UNIQUE NOT NULL
            )
        """)
        logger.info("feature_list tablosu oluşturuldu")

        # feature_values tablosunu oluştur
        execute_query("""
            CREATE TABLE IF NOT EXISTS feature_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id INTEGER NOT NULL,
                feature_id INTEGER NOT NULL,
                feature_value REAL NOT NULL,
                UNIQUE(cycle_id, feature_id),
                FOREIGN KEY (feature_id) REFERENCES feature_list(id)
            )
        """)
        logger.info("feature_values tablosu oluşturuldu")

        # cycles tablosunu oluştur
        execute_query("""
            CREATE TABLE IF NOT EXISTS cycles (
                id INTEGER PRIMARY KEY,
                cycle_date TEXT NOT NULL
            )
        """)

        return True
    except Exception as e:
        logger.error("Test veritabanı başlatılırken hata oluştu", e)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def insert_new_features(features_list: List[str]) -> Dict[str, int]:
    """Yeni özellikleri veritabanına ekler ve feature_id'lerini döndürür"""
    try:
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        
        feature_ids = {}
        
        for feature in features_list:
            try:
                cursor.execute("INSERT INTO feature_list (feature_name) VALUES (?)", (feature,))
                feature_ids[feature] = cursor.lastrowid
                logger.debug(f"Yeni özellik eklendi: {feature}")
            except sqlite3.IntegrityError:
                # Özellik zaten varsa ID'sini al
                cursor.execute("SELECT id FROM feature_list WHERE feature_name = ?", (feature,))
                feature_ids[feature] = cursor.fetchone()[0]
                logger.debug(f"Mevcut özellik ID'si alındı: {feature}")
        
        conn.commit()
        conn.close()
        logger.info(f"{len(features_list)} özellik başarıyla işlendi")
        return feature_ids
    except Exception as e:
        logger.error("Özellikler eklenirken hata oluştu", e)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def format_data_with_id(features: Dict[str, List[float]], feature_ids: Dict[str, int]) -> List[Dict[str, Any]]:
    """Özellik verilerini veritabanı formatına dönüştürür"""
    try:
        formatted_data = []
        
        for index, row in features.iterrows():
            cycle_data = {
                'id': index,
                'features': []
            }
            
            for feature_name, values in features.items():
                if feature_name in feature_ids:
                    cycle_data['features'].append({
                        'feature_id': feature_ids[feature_name],
                        'feature_value': values[index]
                    })
            
            formatted_data.append(cycle_data)
        
        logger.info(f"{len(formatted_data)} döngü verisi formatlandı")
        return formatted_data
    except Exception as e:
        logger.error("Veri formatlanırken hata oluştu", e)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def insert_cycle_data(formatted_data: List[Dict[str, Any]], date: str):
    """Döngü verilerini veritabanına ekler"""
    try:
        conn = sqlite3.connect('test.db')
        cursor = conn.cursor()
        
        for cycle in formatted_data:
            try:
                # Cycle ID'nin var olup olmadığını kontrol et
                cursor.execute(
                    "SELECT id FROM cycles WHERE id = ?",
                    (cycle['id'],)
                )
                existing_cycle = cursor.fetchone()
                
                if existing_cycle:
                    logger.debug(f"Döngü {cycle['id']} zaten mevcut, atlanıyor")
                    continue
                
                # Cycle kaydını ekle
                cursor.execute(
                    "INSERT INTO cycles (cycle_date, id) VALUES (?, ?)",
                    (date, cycle['id'])
                )
                cycle_id = cycle['id']  # lastrowid yerine cycle['id'] kullan
                
                # Feature değerlerini ekle
                for feature in cycle['features']:
                    cursor.execute(
                        "INSERT INTO feature_values (cycle_id, feature_id, feature_value) VALUES (?, ?, ?)",
                        (cycle_id, feature['feature_id'], feature['feature_value'])
                    )
                
                logger.debug(f"Döngü {cycle['id']} başarıyla eklendi")
            except sqlite3.Error as e:
                logger.error(f"Döngü {cycle['id']} eklenirken hata oluştu", e)
                raise
        
        conn.commit()
        conn.close()
        logger.info(f"{len(formatted_data)} döngü verisi başarıyla işlendi")
    except Exception as e:
        logger.error("Döngü verileri eklenirken hata oluştu", e)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise 