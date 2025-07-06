#!/bin/bash

# =================================
# FOI Archive - Stop Local Development
# =================================

echo "🛑 Stopping FOI Archive Local Development..."

# Kill any running uvicorn processes
pkill -f "uvicorn main:app" 2>/dev/null || true

# Deactivate virtual environment if active
if [[ "$VIRTUAL_ENV" != "" ]]; then
    deactivate 2>/dev/null || true
fi

echo "✅ Local development stopped"
echo "💡 Database and uploads are preserved for next run" 