from scripts.db_connection import execute_query
from scripts.read_bin import data_extraction
from scripts.feature_extraction import feature_extraction
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import sys
from scripts.logger import Logger
import pandas as pd
import json

# Logger'ı başlat
logger = Logger()

# .env dosyasını yükle
load_dotenv('db.config')

# Test ortamı kontrolü
is_test = os.getenv('IS_TEST', 'false').lower() == 'true'

if is_test:
    from scripts.db_functions_test import insert_new_features, format_data_with_id, init_test_db, insert_cycle_data
    # Test veritabanını başlat
    init_test_db()
    logger.info("Test veritabanı başlatıldı")
else:
    from scripts.db_functions import insert_new_features, format_data_with_id, insert_feature_values, get_station_profile

# Progress dosyası yönetimi
PROGRESS_FILE = "progress.json"

def load_progress():
    """İşlem ilerlemesini yükler"""
    try:
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            logger.info(f"İlerleme dosyası yüklendi: {len(progress.get('completed', []))} kayıt tamamlanmış")
            return progress
        else:
            with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                json.dump({"completed": [], "last_updated": None}, f, ensure_ascii=False, indent=2)
        return load_progress()
    except Exception as e:
        logger.error("İlerleme dosyası yüklenirken hata oluştu", e)
        return {"completed": [], "last_updated": None}

def save_progress(progress):
    """İşlem ilerlemesini kaydeder"""
    try:
        progress["last_updated"] = datetime.now().isoformat()
        with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)
        logger.debug("İlerleme dosyası güncellendi")
    except Exception as e:
        logger.error("İlerleme dosyası kaydedilirken hata oluştu", e)

def add_completed_record(progress, station_id, date):
    """Tamamlanan kaydı ilerlemete ekler"""
    record_key = f"{station_id}_{date}"
    if record_key not in progress["completed"]:
        progress["completed"].append(record_key)
        save_progress(progress)
        logger.info(f"Tamamlanan kayıt eklendi: {record_key}")

def is_already_processed(progress, station_id, date):
    """Kayıt daha önce işlenmiş mi kontrol eder"""
    record_key = f"{station_id}_{date}"
    return record_key in progress["completed"]

def get_all_dates(station_profile):
    """Station profile'ı veritabanından alır
    # get all dates from station folder path
        # path: ./station_id/
    """
    try:
        # get all dates from station folder path
        # path: ./station_id/
        dates = pd.DataFrame(columns=['station_id', 'date'])
        for _, station in station_profile.iterrows():
            station_folder_path = f"{os.getenv('path')}{str(station['ID'])}/"
            if os.path.exists(station_folder_path):
                dates = pd.concat([dates, pd.DataFrame([{'station_id': str(station['ID']), 'date': f} for f in os.listdir(station_folder_path) if os.path.isdir(os.path.join(station_folder_path, f))])], ignore_index=True)
            else:
                logger.warning(f"{station_folder_path} klasörü bulunamadı")
            logger.info(f"Station {station['ID']} için tarihler: {dates}")
        return dates
    except Exception as e:
        logger.error("Station profile'ı alırken hata oluştu", e)
        raise

if __name__ == "__main__":
    try:
        if len(sys.argv) == 2:
            if sys.argv[1] == "all":
                # Tüm tarihleri işle
                is_all_dates = True
                logger.info("Tüm tarihler işlenecek")
            else:
                # Belirli bir tarih işlenecek
                is_all_dates = False
                logger.info("Bugünün tarihi işlenecek")
        else:
            # Belirli bir tarih işlenecek
            is_all_dates = False
            logger.info("Bugünün tarihi işlenecek")
        
        # Progress dosyasını yükle (sadece all modunda)
        progress = None
        if is_all_dates:
            progress = load_progress()
            logger.info(f"İşlem devam modu aktif. Tamamlanan kayıt sayısı: {len(progress['completed'])}")
            
        station_profile = get_station_profile()
        logger.info(f"Station profile'ı veritabanından alındı")
        if is_all_dates:
            dates = get_all_dates(station_profile)
            # Daha önce işlenmemiş kayıtları filtrele
            if progress:
                original_count = len(dates)
                dates = dates[~dates.apply(lambda row: is_already_processed(progress, row['station_id'], row['date']), axis=1)]
                filtered_count = len(dates)
                logger.info(f"Filtreleme sonucu: {original_count} kayıttan {filtered_count} kayıt işlenecek ({original_count - filtered_count} kayıt daha önce işlenmiş)")
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            dates = pd.DataFrame(columns=['station_id', 'date'])
            dates = pd.concat([dates, pd.DataFrame([{'station_id': str(station['ID']), 'date': today} for _, station in station_profile.iterrows()])], ignore_index=True)
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            dates = pd.concat([dates, pd.DataFrame([{'station_id': str(station['ID']), 'date': yesterday} for _, station in station_profile.iterrows()])], ignore_index=True)

        for index, row in dates.iterrows():
            logger.info(f"{row['date']} tarihli veri işleme başlatıldı")
            
            print(f"{row['date']} dosyasından veri çekiliyor...")
            data = data_extraction(row['date'],row['station_id'])
            if len(data) == 0:
                logger.error(f"{row['date']} dosyasından veri çekilemedi")
                continue
            logger.info(f"{row['date']} dosyasından {len(data)} veri çekildi")
            print(f"{row['date']} dosyasından {len(data)} veri çekildi.")
        
            pressure_columns = ["Pressure1","Pressure2","Pressure3","Pressure4"]
            temp_columns = ["Temp1","Temp2","Temp3","Temp4"]
            features = feature_extraction(data, pressure_columns, temp_columns)
            logger.info(f"{row['date']} dosyasından özellikler çıkarıldı")
            print(f"{row['date']} dosyasından özellikler çıkarıldı.")
            
            features_list = list(features.keys())
            feature_list_db = insert_new_features(features_list)
            logger.info(f"Özellik listesi veritabanından alındı")
            print(f"Özellik listesi dbden alındı.")
            
            # Veriyi cycle_id, feature_id, feature_value formatına dönüştür
            data_with_id = format_data_with_id(features, feature_list_db)
            
            if is_test:
                insert_cycle_data(data_with_id, row['date'])
                logger.info(f"Veriler test veritabanına eklendi")
                print(f"Veriler test veritabanına eklendi.")
            else:
                insert_feature_values(data_with_id,row['station_id'],batch_size=1000)
                logger.info(f"Veriler MySQL veritabanına eklendi")
                print(f"Veriler eklendi.")
                
            logger.info(f"{row['date']} tarihli veri işleme başarıyla tamamlandı")
            
            # Progress dosyasını güncelle (sadece all modunda)
            if is_all_dates and progress is not None:
                add_completed_record(progress, row['station_id'], row['date'])
        
        
    except Exception as e:
        logger.error("Veri işleme sırasında hata oluştu", e)
        raise



