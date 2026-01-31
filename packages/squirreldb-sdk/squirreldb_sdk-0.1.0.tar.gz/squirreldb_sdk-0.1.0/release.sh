#!/bin/bash
set -e

cd "$(dirname "$0")"

if [ -z "$1" ]; then
  echo "Usage: ./release.sh <version>"
  echo "Example: ./release.sh 0.1.0"
  exit 1
fi

VERSION=$1

if [[ ! $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Error: Version must be in format 0.0.0"
  exit 1
fi

echo "Releasing squirreldb-sdk v${VERSION}..."

# Update version in pyproject.toml
sed -i '' "s/^version = \".*\"/version = \"${VERSION}\"/" pyproject.toml

# Install build dependencies
echo "Installing build dependencies..."
pip install --quiet build twine pytest

echo "Running tests..."
python -m pytest tests/ -q

echo "Building..."
rm -rf dist/ build/ *.egg-info
python -m build

echo "Publishing to PyPI..."
python -m twine upload dist/*

echo "Creating git tag..."
git add pyproject.toml
git commit -m "Release v${VERSION}"
git tag "v${VERSION}"
git push origin "v${VERSION}"

echo "Released squirreldb-sdk@${VERSION}"
echo ""
echo "Users can install with:"
echo "  pip install squirreldb-sdk"
