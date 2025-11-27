#!/bin/bash

echo "Attempting to install CPU-only dependencies from environment-docker.yml..."

# Use the absolute path for reliability
/opt/conda/bin/mamba env update --file /app/environment-docker.yml

# Check the exit status of the mamba command
if [ $? -eq 0 ]; then
    echo "SUCCESS: Conda environment and dependencies installed successfully."
else
    echo "ERROR: Conda/Mamba installation failed. Check environment-docker.yml and channels."
    exit 1
fi