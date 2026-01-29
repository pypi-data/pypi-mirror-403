#!/bin/bash
# PyPI Publishing Script for pybob-sdk

set -e

echo "🚀 Publishing pybob-sdk to PyPI"
echo ""

# Check if version is provided
if [ -z "$1" ]; then
    echo "Usage: ./scripts/publish.sh <version>"
    echo "Example: ./scripts/publish.sh 0.1.1"
    exit 1
fi

VERSION=$1

# Update version in pyproject.toml
echo "📝 Updating version to $VERSION..."
sed -i '' "s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info

# Build the package
echo "📦 Building package..."
uv build

# Check if build was successful
if [ ! -d "dist" ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "✅ Build successful!"
echo ""
echo "📋 Files to be published:"
ls -lh dist/

echo ""
read -p "Do you want to publish to PyPI? (y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Publishing to PyPI..."
    uv publish
    
    echo ""
    echo "✅ Published successfully!"
    echo "🔗 View at: https://pypi.org/project/pybob-sdk/$VERSION/"
else
    echo "⏭️  Skipped publishing. You can publish manually with:"
    echo "   uv publish"
fi
