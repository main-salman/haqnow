#!/bin/bash
# Alternative deploy script using envsubst for variable substitution

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Set defaults
export REGISTRY="${REGISTRY:-docker.io}"
export DOCKER_USER="${DOCKER_USER:-haqnow}"

# Check if envsubst is available
if ! command -v envsubst &> /dev/null; then
    echo "⚠️  envsubst not found. Installing via Homebrew..."
    if command -v brew &> /dev/null; then
        brew install gettext
        brew link --force gettext
    else
        echo "❌ Please install gettext package: brew install gettext"
        exit 1
    fi
fi

echo "🚀 Deploying with registry: ${REGISTRY}"
echo "🚀 Using docker user: ${DOCKER_USER}"
echo ""

# Apply manifests with variable substitution
for manifest in k8s/manifests/*.yaml; do
    if [ -f "$manifest" ]; then
        echo "Applying $(basename $manifest)..."
        envsubst < "$manifest" | kubectl apply -f -
    fi
done

echo ""
echo "✅ Deployment complete!"
