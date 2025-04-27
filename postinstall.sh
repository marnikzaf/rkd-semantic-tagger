#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting post-installation script..."

# Ensure the script uses the Python version from the virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
  echo "Error: No active virtual environment detected."
  echo "Please activate your virtual environment and re-run this script."
  exit 1
fi

# Upgrade pip in the virtual environment
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Download spaCy models in the virtual environment
echo "Downloading spaCy models..."
python -m spacy download xx_ent_wiki_sm
python -m spacy download nl_core_news_sm
python -m spacy download fr_core_news_sm

echo "Post-installation script completed successfully."
