#!/bin/bash
echo "Running update script at $(date)" >> /app/webhook.log
pwd >> /app/webhook.log
ls -la >> /app/webhook.log

cd /app
echo "Pulling latest changes from GitHub..."
git pull origin main
echo "Update complete."

echo "Done pulling. Restarting Flask app..."
touch app.py