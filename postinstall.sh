#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting post-installation script..."

# Use the Python executable available in the environment
PYTHON_EXEC=$(which python3)

echo "Using Python executable: $PYTHON_EXEC"

# Upgrade pip
echo "Upgrading pip..."
$PYTHON_EXEC -m pip install --upgrade pip

# Download spaCy models
echo "Downloading spaCy models..."
$PYTHON_EXEC -m spacy download xx_ent_wiki_sm --user
$PYTHON_EXEC -m spacy download nl_core_news_sm --user
$PYTHON_EXEC -m spacy download fr_core_news_sm --user

echo "Post-installation script completed successfully."
