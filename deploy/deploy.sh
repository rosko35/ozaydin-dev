#!/usr/bin/env bash
# Güncelleme: GitHub'daki son hâli sunucuya alır ve siteyi yeniden başlatır.
# Kullanım (sunucuda): /srv/ozaydin-dev/deploy/deploy.sh
set -euo pipefail
cd /srv/ozaydin-dev

echo "1/6 Kod çekiliyor"
git pull --ff-only

echo "2/6 Paketler"
"$HOME/.local/bin/uv" pip install -q -r requirements.txt

set -a; . /etc/ozaydin-dev.env; set +a

echo "3/6 Veritabanı"
.venv/bin/python manage.py migrate --noinput

echo "4/6 Statik dosyalar"
.venv/bin/python manage.py collectstatic --noinput -v 0

echo "5/6 Yüklenen dosyalar klasörü"
# media/: admin'den yüklenen görseller ve paylaşım kartları (media/og/). Nginx (www-data) okuyabilmeli.
mkdir -p media/og
chmod 755 media
chmod -R u+rwX,go+rX media

echo "6/6 Yeniden başlatılıyor"
sudo systemctl restart ozaydin-dev

# Sunucu ayar dosyaları depoda değiştiyse hatırlat (bunları kopyalamak elle yapılır)
warn() { echo; echo "UYARI: $1"; shift; for cmd in "$@"; do echo "    $cmd"; done; }
if ! cmp -s deploy/nginx-ozaydin-dev.https.conf /etc/nginx/sites-available/ozaydin-dev; then
    warn "Nginx ayarı depodakinden farklı. Depodakini kullanmak için:" \
        "sudo cp deploy/nginx-ozaydin-dev.https.conf /etc/nginx/sites-available/ozaydin-dev" \
        "sudo nginx -t && sudo systemctl reload nginx"
fi
for unit in ozaydin-dev.service ozaydin-backup.service ozaydin-backup.timer; do
    if ! cmp -s "deploy/$unit" "/etc/systemd/system/$unit"; then
        warn "$unit depodakinden farklı (ya da kurulu değil):" \
            "sudo cp deploy/$unit /etc/systemd/system/ && sudo systemctl daemon-reload"
    fi
done

echo
echo "Tamam: https://ozaydin.dev"
