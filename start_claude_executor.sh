#!/bin/bash
# Start Claude Executor as a background service
# Usage: ./start_claude_executor.sh

cd "$(dirname "$0")"

echo "🚀 Starting Claude Executor..."

# Check if already running
if pgrep -f "python.*claude_executor.py" > /dev/null; then
    echo "⚠️  Executor is already running"
    echo "   PID: $(pgrep -f 'python.*claude_executor.py')"
    echo ""
    echo "To stop it, run: ./stop_claude_executor.sh"
    exit 1
fi

# Start executor in background
nohup python3 claude_executor.py > claude_executor_output.log 2>&1 &
PID=$!

echo "✅ Executor started"
echo "   PID: $PID"
echo "   Log: claude_executor.log"
echo "   Output: claude_executor_output.log"
echo ""
echo "To check status: tail -f claude_executor.log"
echo "To stop: ./stop_claude_executor.sh"
