#!/bin/bash

# Script to increment version number in package.json
# Usage: ./update-version.sh [major|minor|patch]
# Default: patch (increment third number)

PACKAGE_JSON="frontend/package.json"

if [ ! -f "$PACKAGE_JSON" ]; then
    echo "Error: $PACKAGE_JSON not found!"
    exit 1
fi

# Get current version (first match only)
CURRENT_VERSION=$(grep -m1 '"version"' "$PACKAGE_JSON" | sed 's/.*"version": "\([^"]*\)".*/\1/')
echo "Current version: $CURRENT_VERSION"

# Parse version numbers
IFS='.' read -r major minor patch <<< "$CURRENT_VERSION"

# Determine what to increment
case ${1:-patch} in
    major)
        major=$((major + 1))
        minor=1
        patch=0
        ;;
    minor)
        minor=$((minor + 1))
        patch=0
        ;;
    patch)
        # Handle the 1.100 -> 2.1 transition
        if [ "$patch" -ge 100 ]; then
            major=$((major + 1))
            minor=1
            patch=0
        else
            patch=$((patch + 1))
        fi
        ;;
    *)
        echo "Usage: $0 [major|minor|patch]"
        exit 1
        ;;
esac

NEW_VERSION="$major.$minor.$patch"
echo "New version: $NEW_VERSION"

# Update package.json
sed -i.bak "s/\"version\": \"$CURRENT_VERSION\"/\"version\": \"$NEW_VERSION\"/" $PACKAGE_JSON

echo "Version updated in $PACKAGE_JSON"
echo "Backup saved as $PACKAGE_JSON.bak"

# Show the change
echo ""
echo "Change made:"
diff $PACKAGE_JSON.bak $PACKAGE_JSON | grep version

echo ""
echo "To deploy this version:"
echo "1. git add -A && git commit -m 'Update version to $NEW_VERSION'"
echo "2. git push origin main"
echo "3. Deploy frontend to server" 