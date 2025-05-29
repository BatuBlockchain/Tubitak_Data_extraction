from scripts.db_connection import execute_query
import pandas as pd
import traceback
from scripts.logger import Logger

# Logger'ı başlat
logger = Logger()

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

def insert_feature_values(data_with_id: pd.DataFrame,batch_size: int = 1000):
    """Özellik değerlerini veritabanına ekler veya günceller"""
    try:
        total_batches = (len(data_with_id) + batch_size - 1) // batch_size
        
        for i in range(0, len(data_with_id), batch_size):
            try:
                batch = data_with_id.iloc[i:i+batch_size]
                
                # Her bir satır için kontrol ve güncelleme yap
                for _, row in batch.iterrows():
                    # Mevcut değeri kontrol et
                    existing_value = execute_query(
                        """
                        SELECT id, feature_value 
                        FROM feature_values 
                        WHERE cycle_id = ? AND feature_id = ?
                        """,
                        (row['cycle_id'], row['feature_id']),
                        fetch=True
                    )
                    
                    if existing_value.empty:
                        # Yeni kayıt ekle
                        execute_query(
                            """
                            INSERT INTO feature_values (cycle_id, feature_id, feature_value)
                            VALUES (?, ?, ?)
                            """,
                            (row['cycle_id'], row['feature_id'], row['feature_value'])
                        )
                        logger.debug(f"Yeni kayıt eklendi: cycle_id={row['cycle_id']}, feature_id={row['feature_id']}")
                    elif existing_value['feature_value'].iloc[0] != row['feature_value']:
                        # Değer farklıysa güncelle
                        execute_query(
                            """
                            UPDATE feature_values 
                            SET feature_value = ? 
                            WHERE id = ?
                            """,
                            (row['feature_value'], existing_value['id'].iloc[0])
                        )
                        logger.debug(f"Kayıt güncellendi: id={existing_value['id'].iloc[0]}")
                    else:
                        # Değer aynıysa işlem yapma
                        logger.debug(f"Değer aynı, güncelleme yapılmadı: cycle_id={row['cycle_id']}, feature_id={row['feature_id']}")
                
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