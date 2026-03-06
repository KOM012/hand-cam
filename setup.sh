#!/bin/bash
# setup.sh - Complete setup script for Streamlit Cloud

set -e  # Exit on error

echo "🚀 Starting FaceCard Scanner setup..."

# Create Streamlit config directory
mkdir -p ~/.streamlit

# Write Streamlit configuration
cat > ~/.streamlit/config.toml << EOF
[server]
headless = true
port = \${PORT:-8501}
enableCORS = true
enableXsrfProtection = true
maxUploadSize = 5

[theme]
primaryColor = "#667eea"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[browser]
gatherUsageStats = false
EOF

echo "✅ Streamlit config created"

# Update package list
echo "📦 Updating package list..."
apt-get update -qq

# Install system dependencies
echo "📦 Installing system dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    pkg-config \
    build-essential \
    python3-dev \
    libavcodec-dev \
    libavformat-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavcodec-extra \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgomp1

# Clean up to reduce image size
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "✅ System dependencies installed"

# Print Python version for debugging
python --version
pip --version

echo "✅ Setup complete! Starting application..."