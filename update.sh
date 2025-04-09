#!/bin/bash
cd /app
echo "Pulling latest changes from GitHub..."
git pull origin main
echo "Update complete."

echo "Done pulling. Restarting Flask app..."
touch app.py