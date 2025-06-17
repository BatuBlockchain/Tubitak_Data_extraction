from scripts.db_connection import execute_query
import pandas as pd
import traceback
from scripts.logger import Logger
import os
# Logger'ı başlat
logger = Logger()
extractor_version = os.getenv('EXTRACTOR_VERSION')
if extractor_version is None:
    logger.error("EXTRACTOR_VERSION ortam değişkeni bulunamadı")
    raise Exception("EXTRACTOR_VERSION ortam değişkeni bulunamadı")

def insert_new_features(features_list: list):
    """Yeni özellikleri veritabanına ekler"""
    try:
        # check if the feature list is already in the database
        feature_list_db = execute_query(f"SELECT FEATURE_ID,FEATURE_NAME FROM FEATURES_LOOKUP", fetch=True)
        logger.info("Mevcut özellik listesi veritabanından alındı")

        # new features
        new_features = [feature for feature in features_list if feature not in feature_list_db['FEATURE_NAME'].values]
        
        # insert new features
        for feature in new_features:
            try:
                max_feature_id = execute_query("SELECT MAX(FEATURE_ID) as max_id FROM FEATURES_LOOKUP", fetch=True)['max_id'].iloc[0]
                new_feature_id = 1 if pd.isna(max_feature_id) else max_feature_id + 1
                execute_query(f"INSERT INTO FEATURES_LOOKUP (FEATURE_ID,FEATURE_NAME) VALUES (?,?)",(int(new_feature_id),feature))
                logger.debug(f"Yeni özellik eklendi: {feature}")
            except Exception as e:
                logger.error(f"Özellik eklenirken hata oluştu: {feature}", e)
                raise

        if len(new_features) > 0:
            logger.info(f"Yeni özellikler eklendi: {new_features}")
            feature_list_db = execute_query(f"SELECT FEATURE_ID,FEATURE_NAME FROM FEATURES_LOOKUP", fetch=True)
        
        return feature_list_db
    except Exception as e:
        logger.error("Özellik listesi işlenirken hata oluştu", e)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def format_data_with_id(features: pd.DataFrame, feature_list_db: pd.DataFrame):
    """Veriyi cycle_id, feature_id, feature_value formatına dönüştürür"""
    try:
        data_with_id = pd.DataFrame()
        for index, row in features.iterrows():
            for feature in features.columns:
                try:
                    feature_id = feature_list_db[feature_list_db['FEATURE_NAME'] == feature].FEATURE_ID.values[0]
                    data_with_id = pd.concat([data_with_id, pd.DataFrame({
                        'CYCLE_ID': [int(index)],
                        'FEATURE_ID': [int(feature_id)],
                        'FEATURE_VALUE': [float(row[feature])]
                    })], ignore_index=True)
                except IndexError as e:
                    logger.error(f"Özellik ID'si bulunamadı: {feature}", e)
                    raise
                except Exception as e:
                    logger.error(f"Veri formatlanırken hata oluştu: {feature}", e)
                    raise

        logger.info(f"{len(data_with_id)} satır veri formatlandı")
        return data_with_id
    except Exception as e:
        logger.error("Veri formatlanırken hata oluştu", e)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def insert_feature_values(data_with_id: pd.DataFrame, station_id: int, batch_size: int = 1000):
    """Özellik değerlerini veritabanına ekler veya günceller"""
    try:
        total_batches = (len(data_with_id) + batch_size - 1) // batch_size
        
        for i in range(0, len(data_with_id), batch_size):
            try:
                batch = data_with_id.iloc[i:i+batch_size]
                
                # Mevcut değerleri toplu olarak kontrol et
                cycle_ids = tuple(int(x) for x in batch['CYCLE_ID'].unique())
                feature_ids = tuple(int(x) for x in batch['FEATURE_ID'].unique())
                
                existing_values = execute_query(
                    """
                    SELECT ID, CYCLE_ID, FEATURE_ID, STATION_ID, FEATURE_VALUE, EXTRACTOR_VERSION
                    FROM EXTRACTED_FEATURES 
                    WHERE CYCLE_ID IN ({}) AND FEATURE_ID IN ({}) AND STATION_ID = ?
                    """.format(
                        ','.join(['?'] * len(cycle_ids)),
                        ','.join(['?'] * len(feature_ids))
                    ),
                    (*cycle_ids, *feature_ids, int(station_id)),
                    fetch=True
                )
                
                # Mevcut değerleri dictionary'ye dönüştür
                existing_dict = {
                    (int(row['CYCLE_ID']), int(row['FEATURE_ID']),int(row['STATION_ID'])): (row['ID'], row['FEATURE_VALUE'], row['EXTRACTOR_VERSION'])
                    for _, row in existing_values.iterrows()
                }
                
                # Eklenecek ve güncellenecek kayıtları ayır
                to_insert = []
                to_update = []
                
                for _, row in batch.iterrows():
                    key = (int(row['CYCLE_ID']), int(row['FEATURE_ID']),int(station_id))
                    if key not in existing_dict:
                        to_insert.append((
                            int(row['CYCLE_ID']),
                            int(row['FEATURE_ID']),
                            float(row['FEATURE_VALUE']),
                            int(station_id),
                            extractor_version
                        ))
                    else:
                        existing_id, existing_value, existing_version = existing_dict[key]
                        if existing_value != row['FEATURE_VALUE'] or existing_version != extractor_version:
                            to_update.append((
                                float(row['FEATURE_VALUE']),
                                extractor_version,
                                existing_id
                            ))
                
                # Toplu ekleme
                if to_insert:
                    execute_query(
                        """
                        INSERT INTO EXTRACTED_FEATURES (CYCLE_ID, FEATURE_ID, FEATURE_VALUE, STATION_ID, EXTRACTOR_VERSION)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        to_insert,
                        many=True
                    )
                    logger.debug(f"{len(to_insert)} yeni kayıt eklendi")
                
                # Toplu güncelleme
                if to_update:
                    execute_query(
                        """
                        UPDATE EXTRACTED_FEATURES 
                        SET FEATURE_VALUE = ?, EXTRACTOR_VERSION = ?
                        WHERE ID = ?
                        """,
                        to_update,
                        many=True
                    )
                    logger.debug(f"{len(to_update)} kayıt güncellendi")
                
                logger.debug(f"Batch {i//batch_size + 1}/{total_batches} işlendi")
            except Exception as e:
                logger.error(f"Batch {i//batch_size + 1}/{total_batches} işlenirken hata oluştu", e)
                raise

        logger.info(f"Toplam {len(data_with_id)} özellik değeri başarıyla işlendi")
        return True
    except Exception as e:
        logger.error("Özellik değerleri işlenirken hata oluştu", e)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
        
def get_station_profile():
    """Station profile'ı veritabanından alır
    RETURN:
        station_profile: pd.DataFrame
        station_profile.columns: ['NAME', 'ID', 'CREATED_AT']
    """
    try:
        station_profile = execute_query(f"SELECT NAME, ID, CREATED_AT FROM STATION_PROFILE", fetch=True)
        return station_profile
    except Exception as e:
        logger.error("Station profile'ı alırken hata oluştu", e)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise