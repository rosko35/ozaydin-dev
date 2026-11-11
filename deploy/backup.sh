#!/usr/bin/env bash
# Gece yedeği: veritabanı + yüklenen dosyalar (media/). 14 günden eski yedekler silinir.
# Her gece 03:30'da systemd çalıştırır (deploy/ozaydin-backup.timer). Elle: /srv/ozaydin-dev/deploy/backup.sh
# Kayıtlar: journalctl -u ozaydin-backup
# Geri dönmek için: deploy/restore.md
set -euo pipefail

DB_NAME="${DB_NAME:-ozaydin}"
SITE_DIR="${SITE_DIR:-/srv/ozaydin-dev}"
BACKUP_DIR="${BACKUP_DIR:-/srv/backups}"
KEEP_DAYS="${KEEP_DAYS:-14}"
DAY="$(date +%F)"

log() { echo "[$(date '+%F %T')] $*"; }
trap 'log "HATA: yedekleme yarıda kaldı (satır $LINENO)"' ERR

umask 077  # yedekleri sadece emre okuyabilsin
mkdir -p "$BACKUP_DIR"

log "Veritabanı yedekleniyor: $DB_NAME"
DB_FILE="$BACKUP_DIR/ozaydin-$DAY.dump"
pg_dump -Fc "$DB_NAME" > "$DB_FILE.part"
mv "$DB_FILE.part" "$DB_FILE"
log "Tamam: $DB_FILE ($(du -h "$DB_FILE" | cut -f1))"

log "Yüklenen dosyalar yedekleniyor: $SITE_DIR/media"
MEDIA_FILE="$BACKUP_DIR/media-$DAY.tar.gz"
if [ -d "$SITE_DIR/media" ]; then
    # og/ klasörü atlanır: paylaşım görselleri istenince yeniden üretilir
    tar -czf "$MEDIA_FILE.part" -C "$SITE_DIR" --exclude=media/og media
    mv "$MEDIA_FILE.part" "$MEDIA_FILE"
    log "Tamam: $MEDIA_FILE ($(du -h "$MEDIA_FILE" | cut -f1))"
else
    log "media/ klasörü yok, atlandı"
fi

log "$KEEP_DAYS günden eski yedekler siliniyor"
find "$BACKUP_DIR" -maxdepth 1 -type f \( -name 'ozaydin-*.dump' -o -name 'media-*.tar.gz' -o -name '*.part' \) \
    -mtime +"$((KEEP_DAYS - 1))" -print -delete

log "Yedekleme bitti. Klasörde: $(find "$BACKUP_DIR" -maxdepth 1 -type f | wc -l) dosya, $(du -sh "$BACKUP_DIR" | cut -f1)"
