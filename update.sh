#!/bin/bash
cd /mnt/StoragePool/Github/MEEJ || exit 1
echo "Pulling latest changes from GitHub..."
git pull origin main
echo "Update complete."

echo "Done pulling. Restarting Flask app..."
touch app.py