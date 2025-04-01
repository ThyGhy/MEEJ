#!/bin/bash

cd /mnt/StoragePool/Github/MEEJ  # Change this if your path differs

echo "===== $(date) =====" >> update.log
echo "Pulling latest code..." >> update.log
git pull origin main >> update.log 2>&1

echo "Rebuilding containers..." >> update.log
docker compose down >> update.log 2>&1
docker compose up -d --build >> update.log 2>&1

echo "Update complete." >> update.log
