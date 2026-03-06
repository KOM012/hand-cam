#!/bin/bash
# setup.sh - Install system dependencies for Streamlit Cloud

mkdir -p ~/.streamlit

echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml

# Install system dependencies
apt-get update
apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxrender1 libxext6 libgomp1