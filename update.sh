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