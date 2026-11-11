#!/usr/bin/env bash
# Güncelleme: GitHub'daki son hâli sunucuya alır ve siteyi yeniden başlatır.
# Kullanım (sunucuda): /srv/ozaydin-dev/deploy/deploy.sh
set -euo pipefail
cd /srv/ozaydin-dev

echo "1/5 Kod çekiliyor"
git pull --ff-only

echo "2/5 Paketler"
"$HOME/.local/bin/uv" pip install -q -r requirements.txt

set -a; . /etc/ozaydin-dev.env; set +a

echo "3/5 Veritabanı"
.venv/bin/python manage.py migrate --noinput

echo "4/5 Statik dosyalar"
.venv/bin/python manage.py collectstatic --noinput -v 0

echo "5/5 Yeniden başlatılıyor"
sudo systemctl restart ozaydin-dev

echo "Tamam: https://ozaydin.dev"
