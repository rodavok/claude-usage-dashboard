#!/bin/bash
# Automated Claude Code Dashboard Generator with ntfy notification
# Run via cron: 0 8 * * * /home/rodavok/Projects/claude_dashboard/run_claude_code_dashboard.sh

set -e

# Configuration
PROJECT_DIR="/home/rodavok/Projects/claude_dashboard"
NTFY_TOPIC="your-secret-topic-here"  # Change this to your own secret topic
DASHBOARD_FILE="$PROJECT_DIR/claude_code_dashboard.html"
LOG_FILE="$PROJECT_DIR/cron.log"

# Activate venv if it exists
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

cd "$PROJECT_DIR"

echo "$(date): Starting dashboard generation..." >> "$LOG_FILE"

# Run the analyzer with visualization
if python3 claude_code_analyzer.py --visualize >> "$LOG_FILE" 2>&1; then
    echo "$(date): Dashboard generated successfully" >> "$LOG_FILE"

    # Send notification via ntfy
    curl -s \
        -H "Title: Claude Code Dashboard Updated" \
        -H "Priority: default" \
        -H "Tags: chart_with_upwards_trend" \
        -d "Dashboard refreshed at $(date '+%Y-%m-%d %H:%M'). Open to view your usage stats." \
        "https://ntfy.sh/$NTFY_TOPIC" > /dev/null

    echo "$(date): Notification sent" >> "$LOG_FILE"
else
    echo "$(date): Dashboard generation failed" >> "$LOG_FILE"

    # Send failure notification
    curl -s \
        -H "Title: Dashboard Generation Failed" \
        -H "Priority: high" \
        -H "Tags: warning" \
        -d "Check logs at $LOG_FILE" \
        "https://ntfy.sh/$NTFY_TOPIC" > /dev/null
fi
