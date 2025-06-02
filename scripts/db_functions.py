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
        feature_list_db = execute_query(f"SELECT id,feature_name FROM feature_list", fetch=True)
        logger.info("Mevcut özellik listesi veritabanından alındı")

        # new features
        new_features = [feature for feature in features_list if feature not in feature_list_db['feature_name'].values]
        
        # insert new features
        for feature in new_features:
            try:
                execute_query(f"INSERT INTO feature_list (feature_name) VALUES ('{feature}')")
                logger.debug(f"Yeni özellik eklendi: {feature}")
            except Exception as e:
                logger.error(f"Özellik eklenirken hata oluştu: {feature}", e)
                raise

        if len(new_features) > 0:
            logger.info(f"Yeni özellikler eklendi: {new_features}")
            feature_list_db = execute_query(f"SELECT id,feature_name FROM feature_list", fetch=True)
        
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
                    feature_id = feature_list_db[feature_list_db['feature_name'] == feature].id.values[0]
                    data_with_id = data_with_id.append({
                        'cycle_id': features.index[index],
                        'feature_id': feature_id,
                        'feature_value': row[feature]
                    }, ignore_index=True)
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
                cycle_ids = tuple(batch['cycle_id'].unique())
                feature_ids = tuple(batch['feature_id'].unique())
                
                existing_values = execute_query(
                    """
                    SELECT id, cycle_id, feature_id, feature_value, extractor_version
                    FROM feature_values 
                    WHERE cycle_id IN ({}) AND feature_id IN ({}) AND station_id = ?
                    """.format(
                        ','.join(['?'] * len(cycle_ids)),
                        ','.join(['?'] * len(feature_ids))
                    ),
                    (*cycle_ids, *feature_ids, station_id),
                    fetch=True
                )
                
                # Mevcut değerleri dictionary'ye dönüştür
                existing_dict = {
                    (row['cycle_id'], row['feature_id']): (row['id'], row['feature_value'], row['extractor_version'])
                    for _, row in existing_values.iterrows()
                }
                
                # Eklenecek ve güncellenecek kayıtları ayır
                to_insert = []
                to_update = []
                
                for _, row in batch.iterrows():
                    key = (row['cycle_id'], row['feature_id'])
                    if key not in existing_dict:
                        to_insert.append((
                            row['cycle_id'],
                            row['feature_id'],
                            row['feature_value'],
                            station_id,
                            extractor_version
                        ))
                    else:
                        existing_id, existing_value, existing_version = existing_dict[key]
                        if existing_value != row['feature_value'] or existing_version != extractor_version:
                            to_update.append((
                                row['feature_value'],
                                extractor_version,
                                existing_id
                            ))
                
                # Toplu ekleme
                if to_insert:
                    execute_query(
                        """
                        INSERT INTO feature_values (cycle_id, feature_id, feature_value, station_id, extractor_version)
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
                        UPDATE feature_values 
                        SET feature_value = ?, extractor_version = ?
                        WHERE id = ?
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
        station_profile = execute_query(f"SELECT NAME, ID, CREATED_AT FROM station_profile", fetch=True)
        return station_profile
    except Exception as e:
        logger.error("Station profile'ı alırken hata oluştu", e)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise