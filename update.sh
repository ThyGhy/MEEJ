#!/bin/bash

echo "Pulling latest changes from GitHub..."
cd /app
git pull
echo "Update complete."
echo "Done pulling. Restarting Flask app..."