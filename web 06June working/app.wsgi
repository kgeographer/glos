# app.wsgi
import sys
import os
from app import app as application  # Import the Flask instance from app.py

# Ensure the path to your app is in the sys.path
sys.path.insert(0, "/Users/karlg/repos/_glos/web")

# Set environment variables if needed
os.environ['FLASK_ENV'] = 'development'