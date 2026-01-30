#!/bin/bash
# build_and_publish.sh - Clean, build, and upload your package to PyPI
# Usage: ./build_and_publish.sh

set -e  # Exit if any command fails

# --------------------------
# 0️⃣ Load environment variables from .env
# --------------------------
if [ -f .env ]; then
    echo "🔑 Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
fi

# --------------------------
# 1️⃣ Check if TWINE_USERNAME and TWINE_PASSWORD are set
# --------------------------
if [[ -z "$TWINE_USERNAME" || -z "$TWINE_PASSWORD" ]]; then
    echo "❌ ERROR: TWINE_USERNAME or TWINE_PASSWORD not set"
    echo "Set them in your environment or in a .env file"
    exit 1
fi

# --------------------------
# 2️⃣ Clean old builds
# --------------------------
echo "🧹 Cleaning old builds..."
rm -rf dist/ build/ *.egg-info

# --------------------------
# 3️⃣ Build the package
# --------------------------
echo "🏗️ Building distribution..."
python -m build

echo "✅ Build complete!"
ls -lh dist/

# --------------------------
# 4️⃣ Upload to PyPI
# --------------------------
echo "🚀 Uploading to PyPI..."
twine upload dist/*

echo "🎉 Package uploaded successfully!"
