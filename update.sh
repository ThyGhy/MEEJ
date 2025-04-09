#!/usr/bin/env bash

echo "Running update script at $(date)"
cd /app

echo "Resetting local changes..."
git reset --hard HEAD

echo "Pulling latest changes from GitHub..."
git pull

echo "Update complete."
echo "Done pulling. Restarting Flask app..."