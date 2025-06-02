from scripts.db_connection import execute_query
from scripts.read_bin import data_extraction
from scripts.feature_extraction import feature_extraction
from datetime import datetime
import os
from dotenv import load_dotenv
import sys
from scripts.logger import Logger
import pandas as pd

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

def get_all_dates(station_profile):
    """Station profile'ı veritabanından alır
    # get all dates from station folder path
        # path: ./station_id/
    """
    try:
        # get all dates from station folder path
        # path: ./station_id/
        dates = pd.DataFrame(columns=['station_id', 'date'])
        for station in station_profile:
            station_folder_path = f"./{station['ID']}/"
            dates = pd.concat([dates, pd.DataFrame([{'station_id': station['ID'], 'date': f} for f in os.listdir(station_folder_path) if os.path.isdir(os.path.join(station_folder_path, f))])], ignore_index=True)
            logger.info(f"Station {station['ID']} için tarihler: {dates}")
        return dates
    except Exception as e:
        logger.error("Station profile'ı alırken hata oluştu", e)
        raise

if __name__ == "__main__":
    try:
        if len(sys.argv) == 1:
            # Tüm tarihleri işle
            is_all_dates = True
            logger.info("Tüm tarihler işlenecek")
        else:
            # Belirli bir tarih işlenecek
            is_all_dates = False
            logger.info("Bugünün tarihi işlenecek")
            
        station_profile = get_station_profile()
        logger.info(f"Station profile'ı veritabanından alındı")
        if is_all_dates:
            dates = get_all_dates(station_profile)
        else:
            today = datetime.now().strftime("%Y-%m-%d")
            dates = pd.DataFrame(columns=['station_id', 'date'])
            dates = pd.concat([dates, pd.DataFrame([{'station_id': station['ID'], 'date': today} for station in station_profile])], ignore_index=True)

        for index, row in dates.iterrows():
            logger.info(f"{row['date']} tarihli veri işleme başlatıldı")
            
            print(f"{row['date']} dosyasından veri çekiliyor...")
            data = data_extraction(row['date'])
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
        
    except Exception as e:
        logger.error("Veri işleme sırasında hata oluştu", e)
        raise



