#!/bin/bash

# Agent Garden - Smart Startup Script
# Automatically handles port conflicts and starts the server

# Configuration
PORT=${PORT:-5001}
MAX_PORT=$((PORT + 10))

echo "🌱 Starting Agent Garden..."

# Function to check if port is available
check_port() {
    lsof -ti:$1 >/dev/null 2>&1
    return $?
}

# Function to find available port
find_port() {
    local current_port=$PORT
    while [ $current_port -le $MAX_PORT ]; do
        if ! check_port $current_port; then
            echo $current_port
            return 0
        fi
        current_port=$((current_port + 1))
    done
    return 1
}

# Check if default port is in use
if check_port $PORT; then
    echo "⚠️  Port $PORT is already in use"

    # Ask user preference
    read -p "Do you want to (k)ill existing process or (f)ind new port? [k/f]: " choice

    case "$choice" in
        k|K)
            echo "🔄 Killing process on port $PORT..."
            lsof -ti:$PORT | xargs kill -9 2>/dev/null
            sleep 1
            SELECTED_PORT=$PORT
            ;;
        f|F)
            echo "🔍 Finding available port..."
            SELECTED_PORT=$(find_port)
            if [ -z "$SELECTED_PORT" ]; then
                echo "❌ No available ports found between $PORT and $MAX_PORT"
                exit 1
            fi
            echo "✅ Found available port: $SELECTED_PORT"
            ;;
        *)
            echo "❌ Invalid choice. Exiting."
            exit 1
            ;;
    esac
else
    SELECTED_PORT=$PORT
fi

# Export port for Flask
export PORT=$SELECTED_PORT

# Start Flask server
echo "🚀 Starting server on port $SELECTED_PORT..."
echo "📡 Access at: http://localhost:$SELECTED_PORT"
echo "⏸️  Press Ctrl+C to stop"
echo ""

python app.py
