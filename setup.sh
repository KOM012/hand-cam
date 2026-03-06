#!/bin/bash
# setup.sh - Install system dependencies for Streamlit Cloud

# Exit on error, but with proper handling
set -e

# Create Streamlit config directory
mkdir -p ~/.streamlit

# Write Streamlit configuration
cat > ~/.streamlit/config.toml << EOF
[server]
headless = true
port = ${PORT:-8501}
enableCORS = true
enableXsrfProtection = true

[browser]
gatherUsageStats = false
EOF

echo "✅ Streamlit config created"

# Update package list (ignore errors)
echo "📦 Updating package list..."
apt-get update -qq || true

# Install system dependencies with retry logic
echo "📦 Installing system dependencies..."
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgomp1 || {
    echo "⚠️ Some packages failed to install, trying alternatives..."
    
    # Try alternative package names if the first attempt fails
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
        libgl1 \
        libglib2.0-0t64 \
        libsm6 \
        libxrender1 \
        libxext6 \
        libgomp1 || {
        echo "⚠️ Second attempt failed, installing minimal set..."
        
        # Install only the absolutely necessary packages
        DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
            libsm6 \
            libxrender1 \
            libxext6 \
            libgomp1 || true
    }
}

# Clean up to reduce image size
apt-get clean
rm -rf /var/lib/apt/lists/*

echo "✅ System dependencies installation completed"
echo "🚀 Starting FaceCard Scanner..."

# Run the Streamlit app
exec streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0