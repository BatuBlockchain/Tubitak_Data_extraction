import os
import struct
import pandas as pd
import numpy as np
from collections import defaultdict
import traceback
from scripts.logger import Logger

# Logger'ı başlat
logger = Logger()

def data_extraction(data_folder_direction,main_folder_path='data'):
    merged_data = defaultdict(lambda: defaultdict(list))

    for root, dirs, files in os.walk(os.path.join(main_folder_path,data_folder_direction)):
        for file_name in files:
            if file_name.endswith(".bin"):
                # Construct the full file path
                file_path = os.path.join(root, file_name)

                try:
                    # Extract parts of the file name
                    base_part, rest_part = file_name.split(' ', 1)
                    id = base_part.split('_')[1]  # Extract '468' as ID part
                    column_name = rest_part.split('_')[-1].split('.')[0]  # Extract 'Temp1' as column name

                    # Read the binary file efficiently
                    with open(file_path, "rb") as file:
                        data = file.read()
                        values = list(struct.unpack(f'{len(data)//4}f', data))
                    
                    # Append values to the dictionary
                    merged_data[id][column_name] = values
                except (IndexError, struct.error) as e:
                    print(f"Error processing file {file_name}: {e}")

    # Convert merged data into a DataFrame
    merged_data_df = pd.DataFrame.from_dict(merged_data, orient='index')

    # Flatten nested lists and clean up
    for column in merged_data_df.columns:
        merged_data_df[column] = merged_data_df[column].apply(
            lambda y: np.array(y).flatten().tolist() if isinstance(y, list) else y
        )

    # Set index name for clarity
    merged_data_df.index.name = "id"

    # Sort by id
    merged_data_df.sort_index(inplace=True)
    
    return merged_data_df

def read_bin_file(file_path):
    """Binary dosyayı okur ve DataFrame'e dönüştürür"""
    try:
        logger.info(f"Binary dosya okunuyor: {file_path}")
        
        if not os.path.exists(file_path):
            error_msg = f"Dosya bulunamadı: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        with open(file_path, 'rb') as f:
            # Dosya boyutunu kontrol et
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                error_msg = f"Dosya boş: {file_path}"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # İlk 4 byte'ı oku (header)
            header = f.read(4)
            if len(header) < 4:
                error_msg = "Header okunamadı"
                logger.error(error_msg)
                raise ValueError(error_msg)
                
            # Header'ı integer'a çevir
            num_points = struct.unpack('I', header)[0]
            logger.debug(f"Okunacak veri sayısı: {num_points}")
            
            if num_points <= 0:
                error_msg = f"Geçersiz veri sayısı: {num_points}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            # Verileri oku
            data = []
            for _ in range(num_points):
                try:
                    point = struct.unpack('dd', f.read(16))  # Her nokta 2 double (16 byte)
                    data.append(point)
                except struct.error as e:
                    error_msg = f"Veri okuma hatası: {str(e)}"
                    logger.error(error_msg)
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise
            
            # DataFrame oluştur
            df = pd.DataFrame(data, columns=['time', 'value'])
            logger.info(f"Toplam {len(df)} satır veri okundu")
            
            return df
            
    except Exception as e:
        logger.error("Binary dosya okuma işlemi sırasında hata oluştu", e)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def read_multiple_bin_files(directory_path):
    """Bir dizindeki tüm binary dosyaları okur ve bir DataFrame listesi döndürür"""
    try:
        logger.info(f"Dizin okunuyor: {directory_path}")
        
        if not os.path.exists(directory_path):
            error_msg = f"Dizin bulunamadı: {directory_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
            
        if not os.path.isdir(directory_path):
            error_msg = f"Geçersiz dizin: {directory_path}"
            logger.error(error_msg)
            raise NotADirectoryError(error_msg)
        
        dataframes = []
        for filename in os.listdir(directory_path):
            if filename.endswith('.bin'):
                try:
                    file_path = os.path.join(directory_path, filename)
                    logger.debug(f"İşleniyor: {filename}")
                    df = read_bin_file(file_path)
                    dataframes.append(df)
                    logger.info(f"{filename} başarıyla okundu")
                except Exception as e:
                    logger.error(f"{filename} dosyası okunurken hata oluştu", e)
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    continue
        
        if not dataframes:
            error_msg = "Hiçbir binary dosya okunamadı"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        logger.info(f"Toplam {len(dataframes)} dosya başarıyla okundu")
        return dataframes
        
    except Exception as e:
        logger.error("Çoklu binary dosya okuma işlemi sırasında hata oluştu", e)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise