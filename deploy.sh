#!/bin/bash

echo "Pulling latest changes from GitHub..."
git pull origin main

echo "Restarting Apache to apply changes..."
sudo systemctl restart apache2

echo "Deployment complete."