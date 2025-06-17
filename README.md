# TÜBİTAK Veri Çıkarma Projesi

Bu proje, TÜBİTAK için geliştirilmiş gelişmiş bir veri çıkarma ve işleme sistemidir. Sistem, belirli tarihlerdeki binary verileri okuyarak özellik çıkarma, veritabanına kaydetme ve işlem takibi gerçekleştirir.

## ✨ Özellikler

- 📊 **Binary veri okuma ve işleme** - Özel format veri dosyalarından bilgi çıkarma
- 🔬 **Gelişmiş özellik çıkarma** - Pressure ve temperature verilerinden istatistiksel özellikler
- 🗄️ **Çoklu veritabanı desteği** - SQLite (test) ve SQL Server (production) desteği
- 📝 **Detaylı loglama sistemi** - Tarihli log dosyaları ve hata takibi
- 🔄 **Progress takibi** - Kesintisiz işlem devam etme özelliği
- ⚡ **Toplu işlem** - Batch processing ile yüksek performans
- 🛡️ **Hata yönetimi** - Kapsamlı exception handling ve retry mekanizması
- 🔧 **SQLAlchemy entegrasyonu** - Modern ORM ve connection pooling

## 🚀 Kurulum

### Gereksinimler
- Python 3.8+
- SQL Server ODBC Driver 17 (production ortamı için)

### Adımlar

1. **Depoyu klonlayın:**
```bash
git clone <repository-url>
cd Tubitak_Data_Extraction
```

2. **Gerekli Python paketlerini yükleyin:**
```bash
pip install -r requirements.txt
```

3. **Veritabanı yapılandırması:**
   - `db.example.config` dosyasını `db.config` olarak kopyalayın
   - Yapılandırma ayarlarını düzenleyin:

```env
# Test ortamı için
IS_TEST=true

# Production ortamı için
IS_TEST=false
DB_SERVER=your_server
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
EXTRACTOR_VERSION=1
path=./data/
```

4. **Veri klasörü yapısını oluşturun:**
```
data/
├── 0/
│   ├── 2024-01-01/
│   └── 2024-01-02/
└── 1/
    ├── 2024-01-01/
    └── 2024-01-02/
```

## 💻 Kullanım

### Temel Komutlar

#### Tüm tarihleri işlemek için:
```bash
python app.py all
```
- Tüm station'ların tüm tarihlerini işler
- Progress dosyası ile kesintiden devam eder
- İşlenen dosyalar `progress.json`'da tutulur

#### Bugünün tarihini işlemek için:
```bash
python app.py
```
- Sadece bugünün tarihini işler
- Tüm station'lar için bugünün verisini alır

### 🔄 Progress Sistemi

Program `all` modunda çalışırken:
- Her başarıyla tamamlanan işlem `progress.json` dosyasına kaydedilir
- Program kesintiye uğrarsa, aynı komutla kaldığı yerden devam eder
- Daha önce işlenen dosyalar tekrar işlenmez

```json
{
  "completed": [
    "station_1_2024-01-01",
    "station_2_2024-01-01"
  ],
  "last_updated": "2024-01-02T10:30:45.123456"
}
```

### 📋 İşlem Akışı

1. **Station Profile Yükleme** - Veritabanından station bilgileri alınır
2. **Tarih Filtreleme** - İşlenecek tarihler belirlenir
3. **Veri Çıkarma** - Binary dosyalardan veri okunur
4. **Özellik Çıkarma** - İstatistiksel özellikler hesaplanır
5. **Veritabanı Kaydetme** - Veriler batch halinde kaydedilir
6. **Progress Güncelleme** - İşlem durumu güncellenir

**Not:** Program, station profillerini veritabanından otomatik olarak alır ve her station için uygun klasör yollarını kendisi belirler.

## 📁 Proje Yapısı

```
├── app.py                     # 🚀 Ana uygulama dosyası
├── db.config                  # ⚙️ Veritabanı yapılandırma dosyası
├── db.example.config          # 📝 Örnek yapılandırma dosyası
├── requirements.txt           # 📦 Python bağımlılıkları
├── progress.json              # 🔄 İşlem ilerleme dosyası (otomatik)
├── README.md                  # 📖 Proje dokümantasyonu
├── data/                      # 📊 Veri klasörü
│   ├── station_1/            # Station bazında klasörler
│   │   ├── 2024-01-01/       # Tarih bazında alt klasörler
│   │   └── 2024-01-02/
│   └── station_2/
├── logs/                      # 📝 Log dosyaları
│   ├── general_YYYY-MM-DD.log  # Genel işlem logları
│   └── error_YYYY-MM-DD.log    # Hata logları
└── scripts/                   # 🛠️ Yardımcı script'ler
    ├── db_connection.py       # 🔗 Veritabanı bağlantı yönetimi (SQLAlchemy)
    ├── db_functions.py        # 🗄️ SQL Server veritabanı fonksiyonları
    ├── db_functions_test.py   # 🧪 SQLite test veritabanı fonksiyonları
    ├── feature_extraction.py  # 🔬 Signal processing ve özellik çıkarma
    ├── logger.py              # 📋 Loglama sistemi
    └── read_bin.py            # 📥 Binary veri okuma işlemleri
```

## 📊 Teknoloji Stack

### Backend
- **Python 3.8+** - Ana programlama dili
- **Pandas 2.2.1** - Veri analizi ve manipülasyonu
- **NumPy 1.26.4** - Numerik hesaplamalar
- **SciPy** - Signal processing (find_peaks)

### Veritabanı
- **SQLAlchemy 2.0.25** - ORM ve connection pooling
- **pyodbc 5.1.0** - SQL Server bağlantısı
- **SQLite** - Test ortamı için yerel veritabanı

### Yardımcı
- **python-dotenv** - Ortam değişkenleri yönetimi

## 📝 Loglama

Sistem iki farklı log dosyası oluşturur:

1. **`logs/general_YYYY-MM-DD.log`** - Genel işlem logları
   - Başarılı işlemler
   - İlerleme bilgileri
   - Sistem durumu

2. **`logs/error_YYYY-MM-DD.log`** - Hata logları
   - Exception detayları
   - Stack trace'ler
   - Hata zamanları

## 🗄️ Veritabanı Yapısı

### STATION_PROFILE Tablosu
```sql
- ID (INTEGER, PRIMARY KEY)
- NAME (VARCHAR, Station adı)
- CREATED_AT (DATETIME, Oluşturma tarihi)
```

### FEATURES_LOOKUP Tablosu
```sql
- FEATURE_ID (INTEGER, PRIMARY KEY)
- FEATURE_NAME (VARCHAR, UNIQUE, Özellik adı)
```

### EXTRACTED_FEATURES Tablosu
```sql
- ID (BIGINT, PRIMARY KEY)
- CYCLE_ID (INTEGER, Cycle numarası)
- FEATURE_ID (INTEGER, FOREIGN KEY → FEATURES_LOOKUP.FEATURE_ID)
- FEATURE_VALUE (FLOAT, Özellik değeri)
- STATION_ID (INTEGER, FOREIGN KEY → STATION_PROFILE.ID)
- EXTRACTOR_VERSION (VARCHAR, Extractor versiyonu)
```

### Çıkarılan Özellikler
- **Basit İstatistikler**: mean, std, min, max, median, q25, q75
- **Pressure Özellikleri**: 4 farklı pressure sensöründen
- **Temperature Özellikleri**: 4 farklı temperature sensöründen

## 🧪 Geliştirme ve Test

### Test Ortamı
Test ortamında geliştirme yapmak için:

1. **Test modunu aktifleştirin:**
```bash
# db.config dosyasında
IS_TEST=true
```

2. **Programı çalıştırın:**
```bash
python app.py
```

3. **Test veritabanı:**
   - Veriler `test.db` SQLite dosyasına kaydedilir
   - Otomatik tablo oluşturma
   - Hızlı test döngüsü

### Hata Ayıklama
- Log dosyalarını kontrol edin: `logs/error_YYYY-MM-DD.log`
- Exception tracking ile detaylı hata bilgileri
- Progress dosyası ile işlem durumu takibi

## 🔧 Sorun Giderme

### Sık Karşılaşılan Sorunlar

1. **Veritabanı Bağlantı Hatası**
   - `db.config` dosyasını kontrol edin
   - SQL Server ODBC Driver kurulu olduğundan emin olun
   - Test modunda çalıştırarak SQLite ile test edin

2. **Veri Dosyası Bulunamadı**
   - `path` değişkeninin doğru ayarlandığından emin olun
   - Klasör yapısının doğru olduğunu kontrol edin
   - Station ID'lerinin veritabanı ile eşleştiğini kontrol edin

3. **Progress Dosyası Sorunu**
   - `progress.json` dosyasını silin ve yeniden başlatın
   - Dosya izinlerini kontrol edin

### Performance İpuçları
- `batch_size` parametresini ihtiyacınıza göre ayarlayın (varsayılan: 1000)
- Büyük veri setleri için SQLAlchemy connection pooling kullanın


---

**Son Güncelleme:** 2025-06-17  
**Versiyon:** 1.0.1  
**Python Uyumluluğu:** 3.8+
