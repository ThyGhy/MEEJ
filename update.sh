#!/bin/bash
cd /mnt/StoragePool/Github/MEEJ || exit 1
echo "Pulling latest changes from GitHub..."
git pull origin Release
echo "Update complete."