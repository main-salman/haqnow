#!/bin/bash
# Deploy using existing images (if they work) or trigger rebuild

set -e
cd "$(dirname "$0")/../.."
export KUBECONFIG="$(pwd)/k8s/.kubeconfig"

echo "🔄 Restarting pods to pull latest images..."
kubectl delete pods -n haqnow --all --wait=false
sleep 3
kubectl get pods -n haqnow -w
