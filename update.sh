#!/bin/bash

# Move to the actual Git repo directory on the host
cd /mnt/StoragePool/Github/MEEJ || exit 1

echo "Pulling latest changes from GitHub..."
git pull origin main

echo "Rebuilding and restarting containers..."
docker compose build --no-cache
docker compose up -d

echo "Update complete."