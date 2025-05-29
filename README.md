# TÜBİTAK Veri Çıkarma Projesi

Bu proje, TÜBİTAK için geliştirilmiş bir veri çıkarma ve işleme sistemidir. Sistem, belirli bir tarihteki verileri işleyerek özellik çıkarma ve veritabanına kaydetme işlemlerini gerçekleştirir.

## Özellikler

- Veri okuma ve işleme
- Özellik çıkarma
- Test ve gerçek ortam desteği (SQLite ve MySQL)
- Detaylı loglama sistemi
- Hata yönetimi

## Kurulum

1. Gerekli Python paketlerini yükleyin:
```bash
pip install -r requirements.txt
```

2. Veritabanı yapılandırması:
   - `db.config` dosyasını düzenleyin
   - Test ortamı için `IS_TEST=true`
   - Gerçek ortam için `IS_TEST=false` ve MySQL bağlantı bilgilerini güncelleyin

## Kullanım

Programı çalıştırmak için:

```bash
python app.py date=YYYY-MM-DD main_folder_path=PATH
```

Örnek:
```bash
python app.py date=2024-03-20 main_folder_path=data
```

## Proje Yapısı

```
├── app.py                  # Ana uygulama dosyası
├── db.config              # Veritabanı yapılandırma dosyası
├── requirements.txt       # Bağımlılıklar
├── logs/                  # Log dosyaları
│   ├── general_YYYY-MM-DD.log
│   └── error_YYYY-MM-DD.log
└── scripts/
    ├── db_connection.py   # Veritabanı bağlantı yönetimi
    ├── db_functions.py    # MySQL veritabanı fonksiyonları
    ├── db_functions_test.py # SQLite test veritabanı fonksiyonları
    ├── feature_extraction.py # Özellik çıkarma işlemleri
    ├── logger.py          # Loglama sistemi
    └── read_bin.py        # Veri okuma işlemleri
```

## Loglama

Sistem iki farklı log dosyası oluşturur:

1. `logs/general_YYYY-MM-DD.log`: Genel işlem logları
2. `logs/error_YYYY-MM-DD.log`: Hata logları

## Veritabanı Yapısı

### Features Tablosu
- id (PRIMARY KEY)
- feature_name (UNIQUE)

### Cycles Tablosu
- id (PRIMARY KEY)
- cycle_date
- cycle_number

### Feature Values Tablosu
- id (PRIMARY KEY)
- cycle_id (FOREIGN KEY)
- feature_id (FOREIGN KEY)
- value

## Geliştirme

Test ortamında geliştirme yapmak için:
1. `db.config` dosyasında `IS_TEST=true` olarak ayarlayın
2. Programı çalıştırın
3. Veriler `test.db` SQLite dosyasına kaydedilecek

## Lisans

Bu proje TÜBİTAK için özel olarak geliştirilmiştir. # Tubitak_Data_extraction
