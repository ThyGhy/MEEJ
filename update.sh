#!/bin/bash
cd /app || exit
echo "Pulling latest changes from GitHub..."
git pull origin Release
echo "Update complete."