# 12 Kasım güncellemesi: sunucuda yapılacaklar

Bu dalda gelenler: SEO (paylaşım görselleri, sitemap.xml, robots.txt, yapılandırılmış veri), ikonlar,
gece yedeklemesi ve yeni HTTPS'li Nginx ayarı. Komutları sırayla, sunucuda çalıştır.
Her satırın yanındaki `#` sonrası açıklama; onu yazmana gerek yok.

## 0. Bağlan ve hazırlan

```bash
ssh ozaydin                                         # sunucuya bağlan
cd /srv/ozaydin-dev                                 # site klasörüne geç
git rev-parse HEAD > ~/onceki-surum.txt             # şu anki sürümü not et (geri dönmek gerekirse)
pg_dump -Fc ozaydin > ~/once-12-kasim.dump          # güncellemeden önce veritabanının yedeği
sudo cp /etc/nginx/sites-available/ozaydin-dev ~/nginx-ozaydin-dev.yedek   # şu anki Nginx ayarının yedeği
```

## 1. Kodu al

12 Kasım'da GitHub'daki geçmiş yeniden yazıldı (bütün commit'ler Emre adına). Bu yüzden sunucudaki kopya
bir kereye mahsus `git pull` ile değil, şu iki komutla güncellenir:

```bash
git fetch origin                                    # GitHub'daki yeni geçmişi indir
git reset --hard origin/main                        # sunucudaki kodu GitHub'daki main ile birebir aynı yap
```

Sonraki güncellemelerde yine `deploy/deploy.sh` (ya da `git pull`) yeterli.

## 2. Paketler, veritabanı, statik dosyalar

```bash
set -a; . /etc/ozaydin-dev.env; set +a              # sunucu ayarlarını (veritabanı adı vb.) bu terminale yükle
~/.local/bin/uv pip install -r requirements.txt     # yeni/değişen Python paketlerini kur
.venv/bin/python manage.py migrate                  # veritabanı tablolarını güncelle
.venv/bin/python manage.py collectstatic --noinput  # CSS, JS, ikonları staticfiles/ klasörüne topla
mkdir -p media/og && chmod 755 media                # paylaşım görselleri için klasör; Nginx okuyabilsin
```

## 3. Yeni Nginx ayarı

Önce sertifikanın www'yu da kapsadığını kontrol et:

```bash
sudo certbot certificates                           # "Domains:" satırında ozaydin.dev ve www.ozaydin.dev olmalı
```

İkisi de varsa devam et. Sadece `ozaydin.dev` yazıyorsa önce sertifikayı genişlet:
`sudo certbot --nginx --expand -d ozaydin.dev -d www.ozaydin.dev`

```bash
sudo cp deploy/nginx-ozaydin-dev.https.conf /etc/nginx/sites-available/ozaydin-dev   # yeni ayarı yerine koy
sudo nginx -t                                       # ayarda yazım hatası var mı, kontrol et ("test is successful" görmelisin)
sudo systemctl reload nginx                         # Nginx'i kesinti olmadan yeni ayarla çalıştır
```

**Certbot'un ayarları kaybolmaz:** Certbot daha önce sunucudaki dosyaya sertifika satırlarını eklemişti.
Yeni dosyada aynı satırlar (`ssl_certificate`, `ssl_certificate_key`, `options-ssl-nginx.conf`,
`ssl-dhparams.pem`) zaten yazılı; sertifikalar `/etc/letsencrypt/` altında durduğu için dosyayı değiştirmek
onlara dokunmaz. Otomatik yenileme de aynen çalışır (`sudo certbot renew --dry-run` ile denenebilir).

`nginx -t` hata verirse `reload` yapma; eski ayarı geri koy:
`sudo cp ~/nginx-ozaydin-dev.yedek /etc/nginx/sites-available/ozaydin-dev`

## 4. Siteyi yeniden başlat

```bash
sudo systemctl restart ozaydin-dev                  # Django'yu yeni kodla başlat
systemctl status ozaydin-dev --no-pager             # "active (running)" yazmalı
```

## 5. Gece yedeğini kur

```bash
sudo mkdir -p /srv/backups                          # yedeklerin duracağı klasör
sudo chown emre:emre /srv/backups                   # klasör senin olsun (yedeği emre kullanıcısı alıyor)
chmod +x deploy/backup.sh                           # betik çalıştırılabilir olsun (git zaten öyle getirmeli)
sudo cp deploy/ozaydin-backup.service deploy/ozaydin-backup.timer /etc/systemd/system/   # zamanlayıcıyı kopyala
sudo systemctl daemon-reload                        # systemd yeni dosyaları görsün
sudo systemctl enable --now ozaydin-backup.timer    # her gece 03:30'da çalışsın, açılışta da etkin olsun
sudo systemctl start ozaydin-backup                 # bir kez hemen çalıştırıp dene
journalctl -u ozaydin-backup -n 20 --no-pager       # kaydında "Yedekleme bitti" yazmalı
ls -lh /srv/backups/                                # bugünün .dump ve .tar.gz dosyası burada olmalı
systemctl list-timers ozaydin-backup                # bir sonraki çalışma zamanı
```

Yedekten geri dönme ve yedekleri bilgisayarına çekme: `deploy/restore.md`.

## 6. Kontrol

```bash
curl -sI https://ozaydin.dev | head -20             # 200 ve "content-security-policy" başlığı görünmeli
curl -sI https://www.ozaydin.dev | grep -i location # https://ozaydin.dev/ adresine 301 yönlendirmeli
curl -sI http://ozaydin.dev | grep -i location      # https://ozaydin.dev/ adresine 301 yönlendirmeli
curl -s https://ozaydin.dev/robots.txt              # "Sitemap: https://ozaydin.dev/sitemap.xml" satırı
curl -s https://ozaydin.dev/sitemap.xml | head -5   # adres listesi
curl -sI https://ozaydin.dev/og/home-tr.png         # 200, content-type: image/png
curl -sI https://ozaydin.dev/favicon.ico            # 200
```

Tarayıcıda:

- Siteyi aç, sayfalar arasında gez, iletişim formunu dene ve admin paneline gir. Geliştirici araçlarında
  (F12 → Console) kırmızı "Content Security Policy" hatası olmamalı.
- Paylaşım görselini dene: https://www.opengraph.xyz/ adresine `https://ozaydin.dev/projeler/` yapıştır.
- Google Search Console'da Site Haritaları bölümüne `sitemap.xml` ekle.
- Lighthouse'u gizli pencerede çalıştır (eklentiler sonucu bozmasın).

## Bir şey ters giderse: geri alma

Sadece Nginx sorunluysa (site açılmıyor, yönlendirme döngüsü vb.):

```bash
sudo cp ~/nginx-ozaydin-dev.yedek /etc/nginx/sites-available/ozaydin-dev   # eski Nginx ayarını geri koy
sudo nginx -t && sudo systemctl reload nginx
```

Sayfa açılıyor ama bir şey çalışmıyorsa ve Console'da CSP hatası varsa, yeni ayarda kalabilirsin:
`/etc/nginx/sites-available/ozaydin-dev` dosyasında `Content-Security-Policy` ile başlayan `add_header` satırının
başına `#` koy, `sudo nginx -t && sudo systemctl reload nginx`. Sonra bana hatayı gönder.

Kodu tamamen eski hâline döndürmek için:

```bash
cd /srv/ozaydin-dev
git checkout main                                   # gece-gelistirme dalına geçtiysen
git reset --hard "$(cat ~/onceki-surum.txt)"        # kodu güncellemeden önceki sürüme döndür
set -a; . /etc/ozaydin-dev.env; set +a
pg_restore --clean --if-exists --no-owner -d ozaydin ~/once-12-kasim.dump   # veritabanını güncelleme öncesine döndür
~/.local/bin/uv pip install -r requirements.txt
.venv/bin/python manage.py collectstatic --noinput
sudo cp ~/nginx-ozaydin-dev.yedek /etc/nginx/sites-available/ozaydin-dev
sudo nginx -t && sudo systemctl reload nginx
sudo systemctl restart ozaydin-dev
```

Dikkat: veritabanını geri yüklemek, güncellemeden sonra eklediğin içeriği (yazı, proje, mesaj) siler.
Sadece yeni kod veritabanıyla uyumsuzluk çıkardıysa yap.

Yedekleme zamanlayıcısı eski sürümle de sorunsuz çalışır; kapatmak istersen:
`sudo systemctl disable --now ozaydin-backup.timer`
