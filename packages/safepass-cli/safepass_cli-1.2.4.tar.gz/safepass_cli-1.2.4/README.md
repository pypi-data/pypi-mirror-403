# SafePass - Offline Password Manager

SafePass, şifrelerinizi güvenli bir şekilde yerel bilgisayarınızda saklayan offline bir şifre yöneticisidir.

## 🔐 Özellikler

- ✅ **Offline Çalışma**: Tüm veriler yerel bilgisayarınızda
- ✅ **Güçlü Şifreleme**: AES-256-GCM ile şifreleme
- ✅ **Ana Şifre**: Master password ile tüm verilerinizi koruyun
- ✅ **Şifre Üretici**: Güçlü şifreler otomatik oluşturun
- ✅ **Gerçek Zamanlı Şifre Doğrulama**: Kayıt sırasında canlı şifre gücü göstergesi
- ✅ **Güvenlik Analizi**: Şifrelerinizi otomatik değerlendirin
- ✅ **Dashboard**: Gerçek zamanlı güvenlik skoru ve istatistikler
- ✅ **Hiyerarşik Kategoriler**: 5 ana kategori ve 18 alt kategori ile şifrelerinizi organize edin
- ✅ **Şifre Geçmişi**: Eski şifrelerinizi görüntüleyin ve geri yükleyin
- ✅ **Import/Export**: JSON ve CSV formatlarında yedekleme ve geri yükleme
- ✅ **Akıllı İçe Aktarma**: Mevcut kartlardaki şifre değişikliklerini otomatik algılama
- ✅ **Oturum Timeout**: 1 saat inaktivite sonrası otomatik çıkış
- ✅ **Otomatik Güncelleme Kontrolü**: PyPI üzerinden yeni sürüm bildirimleri

## 📊 Güvenlik Analizi

SafePass, şifrelerinizi otomatik olarak analiz eder ve güvenlik seviyenizi değerlendirir.

### Şifre Gücü Kategorileri

Şifreler üç kategoriye ayrılır:
- **🛡️ Güçlü** (80+ puan): Uzun, çeşitli karakter içeren şifreler
- **⚠️ Orta** (50-79 puan): İyileştirilebilir şifreler
- **🔴 Zayıf** (<50 puan): Acilen değiştirilmesi gereken şifreler

### Şifre Puanlama Sistemi

Her şifre aşağıdaki kriterlere göre 100 üzerinden puanlanır:

**Uzunluk Puanı:**
- 16+ karakter → 40 puan
- 12-15 karakter → 30 puan
- 8-11 karakter → 20 puan
- 8'den az → 0 puan

**Karakter Çeşitliliği** (her biri +15 puan):
- ✓ Küçük harf (a-z)
- ✓ Büyük harf (A-Z)
- ✓ Rakam (0-9)
- ✓ Sembol (!@#$%...)

**Örnek Hesaplamalar:**
```
"password"         → 20 + 15 = 35 puan  (Zayıf)
"Password123"      → 30 + 45 = 75 puan  (Orta)
"P@ssw0rd!2024"    → 30 + 60 = 90 puan  (Güçlü)
"MyS3cur3P@ss!"    → 30 + 60 = 90 puan  (Güçlü)
"C0mpl3x!P@ssW0rd" → 40 + 60 = 100 puan (Güçlü)
```

### Güvenlik Skoru

Dashboard'daki güvenlik skoru, tüm şifrelerinizi değerlendirerek hesaplanır:

```
Hesaplama Formülü:
- Güçlü şifre: 100 puan
- Orta şifre: 60 puan
- Zayıf şifre: 20 puan

Baz Skor = (Güçlü×100 + Orta×60 + Zayıf×20) / Toplam Şifre Sayısı

Cezalar:
- Her zayıf şifre için: -5 puan
- Her tekrarlanan şifre grubu için: -10 puan
```

**Tekrar Eden Şifreler:**
Birden fazla hesap için aynı şifreyi kullanmak büyük güvenlik riski oluşturur. Bir hesap ele geçirildiğinde diğer hesaplarınız da tehlikeye girer.

Dashboard'da "Tekrar Eden Şifreler" bölümünde hangi şifrelerin tekrarlandığını görebilirsiniz.

**Skor Yorumlama:**
- 90-100: Mükemmel güvenlik 🏆
- 75-89: İyi güvenlik ✅
- 50-74: Orta güvenlik ⚠️
- 0-49: Zayıf güvenlik 🚨

### Dashboard İstatistikleri

Ana sayfada şu bilgileri görebilirsiniz:
- 📊 Toplam şifre sayısı
- 🛡️ Güçlü şifre sayısı
- ⚠️ Orta şifre sayısı
- 🔴 Zayıf şifre sayısı
- 🔒 Genel güvenlik skoru (0-100)
- 📋 Son eklenen şifreler

## 📁 Kategori Sistemi

SafePass, şifrelerinizi organize etmek için hiyerarşik kategori sistemi sunar:

### Ana Kategoriler ve Alt Kategoriler

| Ana Kategori | Alt Kategoriler |
|--------------|-----------------|
| 📁 **Genel** | E-Posta, Sosyal Medya, Alışveriş, Forumlar & Üyelikler |
| 💰 **Finans** | Bankacılık, Kredi Kartları, Kripto Paralar, Faturalar |
| 💼 **İş & Geliştirici** | Şirket Hesapları, Sunucular & SSH, Veritabanları, Git & Repolar, API & Lisanslar |
| 🌐 **Sistem & Ağ** | Wi-Fi Şifreleri, Cihaz Pinleri, Modem Arayüzleri, Yazılım Lisansları |
| 👤 **Kişisel** | E-Devlet & Resmi Kurum, Sağlık, Notlar & Güvenli Dosyalar |

Şifrelerim sayfasında kategoriye göre filtreleme yapabilirsiniz.

## 🕒 Şifre Geçmişi

SafePass, şifrelerinizin geçmiş versiyonlarını saklar:

- Her şifre değişikliğinde eski şifre geçmişe eklenir
- Şifre kartlarındaki 🕒 ikonuna tıklayarak geçmişi görüntüleyin
- Eski bir şifreyi tek tıkla geri yükleyin
- Değişiklik tarihleri ile birlikte görüntüleme

## 💾 Import / Export

Verilerinizi yedekleyin ve geri yükleyin:

### Dışa Aktarma (Export)
- **JSON Formatı**: Tüm şifrelerinizi JSON dosyası olarak indirin
- İçe/Dışa Aktar > Json Veri Yönetimi sayfasından erişin

### İçe Aktarma (Import)

**JSON İçe Aktarma:**
- Daha önce SafePass'ten dışa aktarılan JSON dosyalarını yükleyin
- **Akıllı Güncelleme**: Mevcut kartlardaki şifre değişiklikleri otomatik algılanır
- Eski şifre geçmişe kaydedilir, yeni şifre güncellenir
- Yeni kartlar otomatik olarak eklenir

**CSV İçe Aktarma:**
- Diğer şifre yönetim uygulamalarınızdaki şifrelerinizi SafePass'e taşıyın
- **İki Format Desteği:**
  - **KeePass Formatı**: `Group,Subcategory,Title,Username,Password,URL`
  - **SafePass Formatı**: `title,username,password,website,category,subcategory`
- Aynı akıllı güncelleme sistemi CSV için de geçerlidir

**Akıllı İçe Aktarma Özellikleri:**
- Aynı kullanıcı adı, başlık, URL ve kategoriye sahip kartlar tespit edilir
- Şifre farklıysa: Eski şifre geçmişe kaydedilir, yeni şifre güncellenir
- Şifre aynıysa: Atlanır, çift kayıt oluşmaz
- Farklı bilgilere sahip kartlar: Yeni kart olarak eklenir

⚠️ **Güvenlik Notu**: Dışa aktarılan dosyalar şifrelerinizi düz metin olarak içerir. Güvenli bir yerde saklayın!

## 📦 Kurulum

```bash
pip install safepass-cli
```

## 🚀 Kullanım

### İlk Kurulum

Kurulumdan sonra SafePass otomatik olarak varsayılan port olan **2025**'te başlar.

### Komutlar

```bash
# Veritabanını manuel başlat (opsiyonel - start komutu otomatik yapar)
safepass init

# Web sunucusunu başlat (varsayılan port: 2025)
safepass start

# Uygulamayı güncelle
safepass-cli update

# Çalışan sunucuyu durdur
safepass stop

# Tüm verileri sıfırla (GERİ ALINAMAZ!)
safepass reset

# Tüm kullanıcı verilerini ve veritabanını kaldır
safepass clean

# Yardım
safepass --help
```

### Tarayıcıdan Erişim

```
http://localhost:2025
```

## 🎨 Kullanıcı Arayüzü Özellikleri

### Kayıt & Giriş

- **Gerçek Zamanlı Şifre Doğrulama**: Kayıt sırasında şifrenizin gücünü anlık görün
- **Şifre Gereksinimleri Göstergesi**: 
  - ✅ En az 8 karakter
  - ✅ Büyük harf (A-Z)
  - ✅ Küçük harf (a-z)
  - ✅ Rakam (0-9)
  - ✨ Sembol (!@#$%) - isteğe bağlı
- **Şifre Görünürlük Kontrolü**: Göz ikonu ile şifreleri göster/gizle
- **Ana Şifre Uyarısı**: Şifrenizi unutma riskine karşı bilgilendirme

### Bildirimler

- **Toast Bildirimleri**: Sağ üst köşede modern bildirimler
- **Hata Yönetimi**: Detaylı ve kullanıcı dostu hata mesajları
- **Güncelleme Kontrolü**: PyPI üzerinden otomatik sürüm kontrolü

### Şifrelerim Sayfası

- **Hızlı Eylemler**: Şifre kopyalama, düzenleme, silme, geçmiş görüntüleme
- **Kategori Filtreleme**: Ana ve alt kategorilere göre filtreleme
- **Arama**: Anlık şifre arama

### Yardımcı Butonlar

Sağ alt köşede sabit butonlar:
- **ℹ️ Nasıl Çalışır**: SafePass hakkında detaylı bilgi (sadece kayıt sayfasında)
- **🔔 Güncelleme**: Yeni sürüm mevcut olduğunda görünür
- **❤️ Geliştirici**: Geliştirici bilgileri ve iletişim

## 🗑️ Kaldırma

### Veritabanını Temizle (Şifreleri Sil)

```bash
# Tüm şifrelerinizi ve veritabanını sil
safepass clean
```

⚠️ **Uyarı:** Bu komut tüm şifrelerinizi kalıcı olarak siler!

### Uygulamayı Tamamen Kaldır

```bash
# 1. Önce veritabanını temizle (opsiyonel)
safepass clean

# 2. Uygulamayı kaldır
pip uninstall safepass-cli
```

**Not:** `pip uninstall` sadece uygulamayı kaldırır, verilerinizi silmez. Verilerinizi de silmek için önce `safepass clean` komutunu çalıştırın.

## 🔄 Güncelleme

SafePass, PyPI üzerinden yeni sürümleri otomatik kontrol eder. Yeni bir sürüm mevcut olduğunda:

1. Sağ alt köşede 🔔 güncelleme butonu görünür
2. Butona tıklayarak güncelleme talimatlarını görün
3. Terminalde `safepass-cli update` komutunu çalıştırın
4. Uygulamayı yeniden başlatın

**Manuel Güncelleme:**
```bash
safepass-cli update
# veya
pip install --upgrade safepass-cli
```

## 🎯 Teknolojiler

**Backend:**
- Django 5.1.x
- SQLite
- Python 3.8+

**Frontend:**
- Modern CSS (Glassmorphism, Gradient tasarımlar, animasyonlar)
- Vanilla JavaScript
- Responsive Design

**Güvenlik:**
- AES-256-GCM şifreleme
- PBKDF2 anahtar türetme
- CSRF koruması

## 🔒 Güvenlik

- Tüm şifreler AES-256-GCM ile şifrelenir
- Ana şifre asla saklanmaz
- Veriler `~/.safepass/` dizininde saklanır
- Offline çalışır, internet bağlantısı gerektirmez (güncelleme kontrolü hariç)
- CSRF token koruması
- Session timeout (1 saat inaktivite)

## ⚙️ Yapılandırma

### Varsayılan Ayarlar

- **Port**: 2025
- **Session Timeout**: 1 saat
- **Veritabanı**: `~/.safepass/db.sqlite3`
- **Otomatik Güncelleme Kontrolü**: Aktif

## ⚠️ Önemli Notlar

- **Ana şifrenizi unutmayın!** Unutursanız verileriniz kurtarılamaz.
- Düzenli olarak verilerinizi yedekleyin (Profil > Import/Export > JSON İndir)
- Güçlü ve benzersiz bir ana şifre kullanın
- Ana şifrenizi güvenli bir yerde saklayın
- Uygulamayı güncel tutun (`safepass-cli update`)

## 📱 Tarayıcı Desteği

SafePass modern tarayıcılarda sorunsuz çalışır:
- ✅ Chrome/Edge (önerilen)
- ✅ Firefox
- ✅ Safari
- ✅ Opera

## 🐛 Sorun Giderme

### Veritabanı Hatası
```bash
# Veritabanını sıfırla (VERİLER SİLİNİR!)
safepass clean
```

### Güncelleme Sorunu
```bash
# Manuel güncelleme
pip install --upgrade safepass-cli --force-reinstall
```

## 👨‍💻 Geliştirici

**Baran Celal Tonyalı**

- 🌐 Website: [barancelaltonyali.com](https://barancelaltonyali.com/)
- 💼 LinkedIn: [linkedin.com/in/baran-celal-tonyali](https://www.linkedin.com/in/baran-celal-tonyali/)
- 📦 PyPI: [pypi.org/project/safepass-cli](https://pypi.org/project/safepass-cli/)
- 💻 GitHub: [github.com/Barancll/safepass-cli](https://github.com/Barancll/safepass-cli)

## 📄 Lisans

MIT License - Detaylar için LICENSE dosyasına bakın.

**SafePass v1.2.3** - Made with ❤️ by Baran Celal Tonyalı
