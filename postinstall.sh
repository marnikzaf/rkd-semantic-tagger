#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting post-installation script..."

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip

# Fix permissions for site-packages directory
echo "Fixing permissions for site-packages directory..."
chmod -R u+w /Library/Frameworks/Python.framework/Versions/3.13/lib/python3.13/site-packages/

# Download spaCy models
echo "Downloading spaCy models..."
python3 -m spacy download xx_ent_wiki_sm
python3 -m spacy download nl_core_news_sm
python3 -m spacy download fr_core_news_sm

echo "Post-installation script completed successfully."
