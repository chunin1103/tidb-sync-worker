#!/bin/bash
# Stop Claude Executor
# Usage: ./stop_claude_executor.sh

echo "🛑 Stopping Claude Executor..."

PID=$(pgrep -f "python.*claude_executor.py")

if [ -z "$PID" ]; then
    echo "⚠️  Executor is not running"
    exit 0
fi

kill $PID

echo "✅ Executor stopped (PID: $PID)"
