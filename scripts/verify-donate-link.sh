#!/bin/bash
# Verify donate link on dev and prod by checking the Navigation JS chunk.
set -e
DEV_INDEX=$(curl -sL "https://haqnow.click/" | grep -oE 'index-[a-zA-Z0-9_-]+\.js' | head -1)
PROD_INDEX=$(curl -sL "https://www.haqnow.com/" | grep -oE 'index-[a-zA-Z0-9_-]+\.js' | head -1)
DEV_NAV=$(curl -sL "https://haqnow.click/" | grep -oE 'Navigation-[a-zA-Z0-9_-]+\.js' | head -1)
[ -z "$DEV_NAV" ] && DEV_NAV=$(curl -sL "https://haqnow.click/assets/$DEV_INDEX" 2>/dev/null | grep -oE 'Navigation-[a-zA-Z0-9_-]+\.js' | head -1)
PROD_NAV=$(curl -sL "https://www.haqnow.com/" | grep -oE 'Navigation-[a-zA-Z0-9_-]+\.js' | head -1)
[ -z "$PROD_NAV" ] && PROD_NAV=$(curl -sL "https://www.haqnow.com/assets/$PROD_INDEX" 2>/dev/null | grep -oE 'Navigation-[a-zA-Z0-9_-]+\.js' | head -1)
echo "Dev Navigation chunk: $DEV_NAV"
echo "Prod Navigation chunk: $PROD_NAV"
DEV_ZEFFY=$(curl -sL "https://haqnow.click/assets/$DEV_NAV" 2>/dev/null | grep -c 'zeffy' || true)
DEV_OLD=$(curl -sL "https://haqnow.click/assets/$DEV_NAV" 2>/dev/null | grep -c 'nonviolence' || true)
PROD_ZEFFY=$(curl -sL "https://www.haqnow.com/assets/$PROD_NAV" 2>/dev/null | grep -c 'zeffy' || true)
PROD_OLD=$(curl -sL "https://www.haqnow.com/assets/$PROD_NAV" 2>/dev/null | grep -c 'nonviolence' || true)
echo ""
echo "=== DEV (haqnow.click) ==="
echo "  Zeffy URL present: $DEV_ZEFFY (expected ≥1)"
echo "  Old URL present:   $DEV_OLD (expected 0)"
echo ""
echo "=== PROD (haqnow.com) ==="
echo "  Zeffy URL present: $PROD_ZEFFY (expected ≥1)"
echo "  Old URL present:   $PROD_OLD (expected 0)"
echo ""
if [ "$DEV_ZEFFY" -ge 1 ] && [ "$DEV_OLD" -eq 0 ] && [ "$PROD_ZEFFY" -ge 1 ] && [ "$PROD_OLD" -eq 0 ]; then
  echo "✅ Donate link is correct on both environments."
  exit 0
else
  echo "❌ One or both environments still serve the old donate link. Force rollout:"
  echo "   export KUBECONFIG=\$(pwd)/k8s/.kubeconfig"
  echo "   kubectl rollout restart deployment/frontend -n haqnow-dev"
  echo "   kubectl rollout restart deployment/frontend -n haqnow"
  exit 1
fi
