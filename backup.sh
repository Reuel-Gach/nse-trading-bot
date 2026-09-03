#!/bin/bash
BACKUP_DIR="/home/reuel/Documents/nse-trading-bot/backups"
mkdir -p $BACKUP_DIR
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Backup SQLite database and historical CSV
cp /home/reuel/Documents/nse-trading-bot/web_dashboard/db.sqlite3 "$BACKUP_DIR/db_$TIMESTAMP.sqlite3"
cp /home/reuel/Documents/nse-trading-bot/data/nse_historical_data.csv "$BACKUP_DIR/nse_data_$TIMESTAMP.csv"

# Keep only the last 7 days of backups
find $BACKUP_DIR -type f -mtime +7 -exec rm {} \;
echo "✅ Backup completed at $TIMESTAMP"
