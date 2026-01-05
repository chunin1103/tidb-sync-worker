#!/bin/bash
#
# Git Commit Overwrite Detector
# ==============================
# Checks if recent commits have overwritten each other's changes
# Usage: bash check_git_overwrites.sh
#

echo "==================================================================="
echo "Git Commit Overwrite Detector for OneDrive Repositories"
echo "==================================================================="
echo ""

cd "$(dirname "$0")"

echo "1. Checking last 10 commits..."
echo "-------------------------------------------------------------------"
git log --oneline --graph -10
echo ""

echo "2. Checking for recent changes to sync_worker.py..."
echo "-------------------------------------------------------------------"
git log --oneline -5 -- sync_worker.py
echo ""

echo "3. Comparing last 2 commits on sync_worker.py..."
echo "-------------------------------------------------------------------"
CHANGES=$(git diff HEAD~2 HEAD -- sync_worker.py | wc -l)
if [ "$CHANGES" -gt 0 ]; then
    echo "✓ Changes detected between last 2 commits ($CHANGES lines changed)"
    echo ""
    echo "Recent change summary:"
    git diff HEAD~2 HEAD --stat -- sync_worker.py
else
    echo "✓ No changes between last 2 commits (this is normal if no edits were made)"
fi
echo ""

echo "4. Checking for potential overwrites..."
echo "-------------------------------------------------------------------"
# Check if any functions/sections were added then removed
ADDED_REMOVED=$(git log --all --pretty=format:"%h %s" -10 -- sync_worker.py | grep -i "fix\|add\|update" | wc -l)

if [ "$ADDED_REMOVED" -gt 3 ]; then
    echo "⚠️  WARNING: Multiple fix/add/update commits detected in last 10 commits"
    echo "⚠️  This could indicate overwrites. Review the git log above carefully."
    echo ""
    echo "To investigate, run:"
    echo "  git log -p -10 -- sync_worker.py  # See full diff history"
    echo "  git diff <commit1> <commit2> -- sync_worker.py"
else
    echo "✓ No obvious overwrite pattern detected"
fi
echo ""

echo "5. OneDrive Sync Status..."
echo "-------------------------------------------------------------------"
if command -v OneDrive.exe &> /dev/null; then
    echo "OneDrive is installed"
else
    echo "OneDrive status unknown (command not available in Git Bash)"
fi
echo ""

echo "==================================================================="
echo "RECOMMENDATIONS:"
echo "==================================================================="
echo "1. ALWAYS run 'git pull' before making changes"
echo "2. Wait 5 seconds after pulling for OneDrive to sync"
echo "3. After committing, verify with: git log --oneline -3"
echo "4. Run this script weekly to detect issues early"
echo "==================================================================="
