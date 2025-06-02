from scripts.db_connection import execute_query
from scripts.read_bin import data_extraction
from scripts.feature_extraction import feature_extraction
from datetime import datetime
import os
from dotenv import load_dotenv
import sys
from scripts.logger import Logger

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
    from scripts.db_functions import insert_new_features, format_data_with_id, insert_feature_values

if __name__ == "__main__":
    try:
        # Komut satırı argümanlarını kontrol et
        if len(sys.argv) < 3:
            error_msg = "Tarih ve ana klasör yolu argümanları zorunludur. Kullanım: python app.py date=YYYY-MM-DD main_folder_path=PATH"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # date= formatındaki argümanı kontrol et
        date_arg = sys.argv[1]
        if not date_arg.startswith("date="):
            error_msg = "Tarih argümanı 'date=' formatında olmalıdır. Örnek: date=2024-03-20"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Tarih değerini ayıkla
        date = date_arg.split("=")[1]
        
        # Ana klasör yolunu kontrol et
        main_folder_path_arg = sys.argv[2]
        if not main_folder_path_arg.startswith("main_folder_path="):
            error_msg = "Ana klasör yolu argümanı 'main_folder_path=' formatında olmalıdır. Örnek: main_folder_path=data"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        main_folder_path = main_folder_path_arg.split("=")[1]
        
        logger.info(f"{date} tarihli veri işleme başlatıldı")
        logger.info(f"Ana klasör yolu: {main_folder_path}")
        
        print(f"{date} dosyasından veri çekiliyor...")
        data = data_extraction(date, main_folder_path=main_folder_path)
        logger.info(f"{date} dosyasından {len(data)} veri çekildi")
        print(f"{date} dosyasından {len(data)} veri çekildi.")
        
        pressure_columns = ["Pressure1","Pressure2","Pressure3","Pressure4"]
        temp_columns = ["Temp1","Temp2","Temp3","Temp4"]
        features = feature_extraction(data, pressure_columns, temp_columns)
        logger.info(f"{date} dosyasından özellikler çıkarıldı")
        print(f"{date} dosyasından özellikler çıkarıldı.")
        
        features_list = list(features.keys())
        feature_list_db = insert_new_features(features_list)
        logger.info(f"Özellik listesi veritabanından alındı")
        print(f"Özellik listesi dbden alındı.")
        
        # Veriyi cycle_id, feature_id, feature_value formatına dönüştür
        data_with_id = format_data_with_id(features, feature_list_db)
        
        if is_test:
            insert_cycle_data(data_with_id, date)
            logger.info(f"Veriler test veritabanına eklendi")
            print(f"Veriler test veritabanına eklendi.")
        else:
            insert_feature_values(data_with_id,batch_size=1000)
            logger.info(f"Veriler MySQL veritabanına eklendi")
            print(f"Veriler eklendi.")
            
        logger.info(f"{date} tarihli veri işleme başarıyla tamamlandı")
        
    except Exception as e:
        logger.error("Veri işleme sırasında hata oluştu", e)
        raise






