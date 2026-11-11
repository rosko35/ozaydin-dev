# Yedekten geri dönme

Sunucu her gece 03:30'da (İstanbul saati) iki dosya hazırlar, `/srv/backups/` içine koyar:

- `ozaydin-YYYY-MM-DD.dump` → veritabanı (projeler, yazılar, mesajlar, kullanıcılar)
- `media-YYYY-MM-DD.tar.gz` → admin panelinden yüklenen görseller (`media/` klasörü)

Son 14 günün yedeği durur, daha eskisi kendiliğinden silinir.

## Yedekleri görmek

```bash
ls -lh /srv/backups/                     # hangi günlerin yedeği var
journalctl -u ozaydin-backup -n 30       # son yedeklemenin kaydı
systemctl list-timers ozaydin-backup     # bir sonraki yedek ne zaman
```

## Geri dönme

Aşağıda tarih olarak `2026-11-12` yazdım; kendi seçtiğin günle değiştir.

**1. Siteyi durdur** (geri yükleme sırasında kimse yazmasın):

```bash
sudo systemctl stop ozaydin-dev
```

**2. Veritabanını geri yükle:**

```bash
pg_restore --clean --if-exists --no-owner -d ozaydin /srv/backups/ozaydin-2026-11-12.dump
```

`--clean` önce mevcut tabloları siler, sonra yedektekileri kurar. Yani veritabanı tam olarak o geceki hâline döner;
o geceden sonra eklenen her şey gider.

Veritabanı tamamen silinmişse (ya da yeni bir sunucudaysan) önce boş bir veritabanı aç, sonra yükle:

```bash
sudo -u postgres createdb -O emre ozaydin
pg_restore --no-owner -d ozaydin /srv/backups/ozaydin-2026-11-12.dump
```

**3. Görselleri geri koy:**

```bash
cd /srv/ozaydin-dev
mv media media.eski                                   # şimdiki hâli kenara al (silme, emin olunca sil)
tar -xzf /srv/backups/media-2026-11-12.tar.gz -C /srv/ozaydin-dev
chmod -R u=rwX,go=rX media                            # Nginx (www-data) okuyabilsin
```

**4. Siteyi başlat ve bak:**

```bash
sudo systemctl start ozaydin-dev
systemctl status ozaydin-dev --no-pager
```

Tarayıcıda https://ozaydin.dev'i ve admin panelini aç. Her şey yerindeyse kenara aldığın klasörü sil:

```bash
rm -rf /srv/ozaydin-dev/media.eski
```

## Yedeğin bir kopyasını bilgisayarına almak

Yedekler şimdilik sadece sunucuda. Sunucunun diski bozulursa yedekler de gider; o yüzden ara sıra
(örneğin haftada bir) kendi bilgisayarına çek. Windows PowerShell'de, yedeklerin duracağı klasörde:

```powershell
scp ozaydin:/srv/backups/ozaydin-*.dump .
scp ozaydin:/srv/backups/media-*.tar.gz .
```

(`ozaydin`, SSH ayarındaki sunucu adı. Değilse `emre@SUNUCU_IP` yaz.)

Bilgisayardaki bir yedeği sunucuya geri göndermek için:

```powershell
scp .\ozaydin-2026-11-12.dump ozaydin:/srv/backups/
```

Sonra yukarıdaki adımlarla geri yükle. İleride bu kopyalama işi otomatik olarak başka bir depolama
alanına (ör. bir bulut deposu) taşınabilir.

## Elle yedek almak

Büyük bir değişiklikten önce:

```bash
sudo systemctl start ozaydin-backup        # ya da: /srv/ozaydin-dev/deploy/backup.sh
ls -lh /srv/backups/
```

Aynı gün ikinci kez alınan yedek, o günün dosyasının üzerine yazılır.
