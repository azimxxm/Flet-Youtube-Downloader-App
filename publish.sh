#!/bin/bash

# YouTube Downloader - Production Build Script
# This script builds and packages the app for macOS distribution

set -e  # Exit on error

echo "🚀 YouTube Downloader - Production Build"
echo "========================================"
echo ""

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
flet pack launcher.py
echo "✅ Build complete"
echo ""

# Create DMG (optional - requires create-dmg)
# Uncomment if you want to create a DMG installer
# echo "📀 Creating DMG installer..."
# create-dmg \
#   --volname "YouTube Downloader" \
#   --window-pos 200 120 \
#   --window-size 800 400 \
#   --icon-size 100 \
#   --icon "launcher.app" 200 190 \
#   --hide-extension "launcher.app" \
#   --app-drop-link 600 185 \
#   "YouTube-Downloader.dmg" \
#   "dist/launcher.app"

# Show results
echo "✅ Production build completed!"
echo ""
echo "📁 Build artifacts:"
echo "   - Application: dist/launcher.app"
echo "   - Executable: dist/launcher"
echo ""
echo "📦 Distribution:"
echo "   1. Test the app: open dist/launcher.app"
echo "   2. Share: Compress launcher.app to .zip for distribution"
echo "   3. Users extract .zip and drag launcher.app to Applications"
echo ""
echo "🎉 Done! Ready for distribution."
