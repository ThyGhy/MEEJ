#!/usr/bin/env bash

echo "Running update script at $(date)"
cd /mnt/StoragePool/Github/MEEJ

echo "Resetting local changes..."
git reset --hard HEAD

echo "Pulling latest changes from GitHub..."
git pull

echo "Update complete."

echo "Rebuilding and restarting Docker container..."
docker compose down
docker compose up -d --build

DISCORD_WEBHOOK="https://discord.com/api/webhooks/1359989680170336478/YYBesd3VltAnFh-ffAnLWZvlFeizISvrOgq2BIe7A_dhStzRmwo9ERaKDruSnmQpbILD"

curl -H "Content-Type: application/json" \
     -X POST \
     -d "{\"content\": \"Update complete on $(hostname) at $(date)\"}" \
     $DISCORD_WEBHOOK