import pandas as pd
import numpy as np
from scipy.signal import find_peaks
import traceback
from scripts.logger import Logger

# Logger'ı başlat
logger = Logger()

def feature_extraction(data, pressure_columns, temp_columns):
    """Verilerden özellik çıkarır"""
    try:
        features = pd.DataFrame()
        
        pressure_feature_funcs = {
            "mean": lambda x: np.mean(x),
            "std": lambda x: np.std(x),
            "median": lambda x: np.median(x),
            "max_point": lambda x: np.max(x) if len(x) > 0 else np.nan,
            "max_point_derivative": lambda x: (
                (x[np.argmax(x) + 1] - x[np.argmax(x) - 1]) / 2
                if 0 < np.argmax(x) < len(x) - 1 else
                (x[np.argmax(x)] - x[np.argmax(x) - 1])
                if np.argmax(x) > 0 else
                (x[np.argmax(x) + 1] - x[np.argmax(x)])
                if np.argmax(x) < len(x) - 1 else np.nan),
            "max_point_time": lambda x: np.argmax(x),
            "derivative_of_first_peak": lambda x: (np.gradient(x)[find_peaks(x)[0][0]] if len(find_peaks(x)[0]) > 0 else np.nan),
            "derivative_of_first_peak_time": lambda x: (find_peaks(x)[0][0] if len(find_peaks(x)[0]) > 0 else np.nan),
            "derivative_of_second_peak": lambda x: (np.gradient(x)[find_peaks(x)[0][1]] if len(find_peaks(x)[0]) > 1 else np.nan),
            "derivative_of_second_peak_time": lambda x: (find_peaks(x)[0][1] if len(find_peaks(x)[0]) > 1 else np.nan),
            "area_under_curve": lambda x: np.trapz(x),
            "slope_angle_of_first_localmax": lambda x: (np.degrees(np.arctan(np.gradient(x)[find_peaks(x)[0][0]])) if len(find_peaks(x)[0]) > 0 else np.nan),
            "slope_angle_of_first_localmax_time": lambda x: (find_peaks(x)[0][0] if len(find_peaks(x)[0]) > 0 else np.nan),
            "slope_angle_of_first_localmin": lambda x: (np.degrees(np.arctan(np.gradient(x)[find_peaks(-np.array(x))[0][0]])) if len(find_peaks(-np.array(x))[0]) > 0 else np.nan),
            "slope_angle_of_first_localmin_time": lambda x: (find_peaks(-np.array(x))[0][0] if len(find_peaks(-np.array(x))[0]) > 0 else np.nan),
            "first_local_max_point": lambda x: (x[find_peaks(x)[0][0]] if len(find_peaks(x)[0]) > 0 else np.nan),
            "first_local_max_point_time": lambda x: (find_peaks(x)[0][0] if len(find_peaks(x)[0]) > 0 else np.nan),
            "first_local_min_point": lambda x: (x[find_peaks(-np.array(x))[0][0]] if len(find_peaks(-np.array(x))[0]) > 0 else np.nan),
            "first_local_min_point_time": lambda x: (find_peaks(-np.array(x))[0][0] if len(find_peaks(-np.array(x))[0]) > 0 else np.nan),
            "global_max_point": lambda x: np.max(x) if len(x) > 0 else np.nan,
            "global_max_point_time": lambda x: np.argmax(x) if len(x) > 0 else np.nan,
            "global_min_point": lambda x: np.min(x) if len(x) > 0 else np.nan,
            "global_min_point_time": lambda x: np.argmin(x) if len(x) > 0 else np.nan
        }
        
        temp_feature_funcs = {
            "min_temp": lambda x: np.min(x),
            "min_temp_time": lambda x: np.argmin(x),
            "max_temp": lambda x: np.max(x),
            "max_temp_time": lambda x: np.argmax(x),
            "cooling_rate": lambda x: ((np.max(x) - x[-1]) / max(1, (len(x) - np.argmax(x)))),
            "cooling_rate_after_first_localmax": lambda x: ((x[find_peaks(x)[0][0]] - x[-1]) / max(1, (len(x) - find_peaks(x)[0][0]))if len(find_peaks(x)[0]) > 0 else np.nan),
            "derivative_of_temp_rising": lambda x: np.max(np.gradient(x))
        }
        
        other_feature_funcs = {
            "first_point": lambda x: x[0] if len(x) > 0 else np.nan,
            "last_point": lambda x: x[-1] if len(x) > 0 else np.nan,
            "slope_angle_of_globalmax": lambda x: (np.degrees(np.arctan(np.gradient(x)[np.argmax(np.gradient(x))])) if len(x) > 1 else np.nan),
            "slope_angle_of_globalmax_time": lambda x: (find_peaks(x)[0][np.argmax(np.gradient(x)[find_peaks(x)[0]])] if len(find_peaks(x)[0]) > 0 else np.nan),
            "slope_angle_to_last_point": lambda x: (np.degrees(np.arctan((x[-1] - x[-2]) / 1)) if len(x) > 1 else np.nan),
            "slope_angle_to_last_point_time": lambda x: (len(x) - 2 if len(x) > 1 else np.nan),
            "slope_angle_of_globalmin": lambda x: (np.degrees(np.arctan(np.gradient(x)[np.argmin(np.gradient(x))])) if len(x) > 1 else np.nan),
            "slope_angle_of_globalmin_time": lambda x: (find_peaks(np.array(-x))[0][np.argmin(np.gradient(x)[find_peaks(np.array(-x))[0]])] if len(find_peaks(np.array(-x))[0]) > 0 else np.nan)
        }

        logger.info("Özellik çıkarma başlatıldı")
        logger.debug(f"Basınç sütunları: {pressure_columns}")
        logger.debug(f"Sıcaklık sütunları: {temp_columns}")

        # Tüm özellikleri ve sütunları birleştirerek tek seferde işle
        feature_columns = [(pressure_feature_funcs, pressure_columns), (temp_feature_funcs, temp_columns)]
        
        # Tüm özellikleri ve sütunları birleştirerek tek seferde işle
        all_features = {}
        for feature_funcs, columns in feature_columns:
            for feature in feature_funcs:
                for col in columns:
                    try:
                        all_features[col + "_" + feature] = data[col].apply(feature_funcs[feature])
                        logger.debug(f"Özellik çıkarıldı: {col}_{feature}")
                    except Exception as e:
                        logger.error(f"Özellik çıkarılırken hata oluştu: {col}_{feature}", e)
                        logger.error(f"Traceback: {traceback.format_exc()}")
                        raise
        
        # Tüm özellikleri tek seferde birleştir
        features = pd.concat(all_features, axis=1)
        logger.info(f"Toplam {len(features.columns)} özellik başarıyla çıkarıldı")
        return features
    except Exception as e:
        logger.error("Özellik çıkarma işlemi sırasında hata oluştu", e)
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


