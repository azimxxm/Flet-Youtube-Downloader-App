#!/bin/bash

# YouTube Downloader - Production Build Script
# This script builds and packages the app for macOS distribution

set -e  # Exit on error

echo "🚀 YouTube Downloader - Production Build"
echo "========================================"
echo ""

# Check for FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ FFmpeg could not be found. Please install it first (brew install ffmpeg)."
    exit 1
fi
echo "✅ FFmpeg found"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist build *.spec __pycache__
echo "✅ Cleanup complete"
echo ""

# Install/update dependencies
echo "📦 Checking dependencies..."
python3 -m pip install --upgrade pip --break-system-packages
python3 -m pip install -r requirements.txt --break-system-packages
python3 -m pip install pyinstaller --break-system-packages
echo "✅ Dependencies ready"
echo ""

# Build the app
echo "🔨 Building macOS application..."
flet pack launcher.py \
    --name "YouTube Downloader" \
    --product-name "YouTube Downloader" \
    --copyright "Copyright (c) 2024" \
    --icon "assets/icon.png"

echo "✅ Build complete"
echo ""

# Create PKG installer
echo "📦 Creating PKG installer..."
pkgbuild --component "dist/YouTube Downloader.app" \
         --install-location "/Applications" \
         "dist/YouTube Downloader.pkg"

echo "✅ PKG creation complete"
echo ""

# Show results
echo "✅ Production build completed!"
echo ""
echo "📁 Build artifacts:"
echo "   - Application: dist/YouTube Downloader.app"
echo "   - Installer:   dist/YouTube Downloader.pkg"
echo ""
echo "📦 Distribution:"
echo "   1. Share 'dist/YouTube Downloader.pkg'"
echo "   2. Users can simply double-click to install"
echo ""
echo "🎉 Done! Ready for distribution."
