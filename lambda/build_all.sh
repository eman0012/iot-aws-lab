#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
FUNCTIONS=("users" "devices" "telemetry" "conditions" "alertlogs" "admin" "consumers")

echo "🔨 Building Lambda packages..."

# Clean previous builds
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Build shared layer
echo "📦 Building shared layer..."
mkdir -p "$BUILD_DIR/layer/python/shared"
cp "$SCRIPT_DIR/shared/"*.py "$BUILD_DIR/layer/python/shared/"

# Install dependencies
pip install \
    psycopg2-binary==2.9.9 \
    pika==1.3.2 \
    PyJWT==2.8.0 \
    bcrypt==4.1.2 \
    boto3==1.34.0 \
    -t "$BUILD_DIR/layer/python/" \
    --quiet --upgrade

# Create layer zip
cd "$BUILD_DIR/layer"
zip -r ../shared-layer.zip . -q
cd "$SCRIPT_DIR"
echo "✅ Shared layer built: build/shared-layer.zip"

# Build each function
for func in "${FUNCTIONS[@]}"; do
    echo "📦 Building $func function..."
    mkdir -p "$BUILD_DIR/$func"
    cp "$SCRIPT_DIR/$func/handler.py" "$BUILD_DIR/$func/"

    cd "$BUILD_DIR/$func"
    zip -r "../$func.zip" . -q
    cd "$SCRIPT_DIR"
    echo "✅ $func function built: build/$func.zip"
done

echo ""
echo "🎉 Build complete! Artifacts:"
ls -lh "$BUILD_DIR"/*.zip
