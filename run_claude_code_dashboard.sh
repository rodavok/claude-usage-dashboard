#!/bin/bash
# Automated Claude Code Dashboard Generator with ntfy notification
# Run via cron: 0 8 * * * /home/rodavok/Projects/claude_dashboard/run_claude_code_dashboard.sh

set -e

# Configuration
PROJECT_DIR="/home/rodavok/Projects/claude_dashboard"
LOG_FILE="$PROJECT_DIR/cron.log"

# Environment variables (set in ~/.profile):
#   CLAUDE_DASH_NTFY_TOPIC - your ntfy notification topic

# Validate required variables
if [ -z "$CLAUDE_DASH_NTFY_TOPIC" ]; then
    echo "$(date): ERROR - CLAUDE_DASH_NTFY_TOPIC not set" >> "$LOG_FILE"
    exit 1
fi

# Activate venv if it exists
if [ -f "$PROJECT_DIR/venv/bin/activate" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

cd "$PROJECT_DIR"

echo "$(date): Starting dashboard generation..." >> "$LOG_FILE"

# Run the analyzer with visualization
if python3 claude_code_analyzer.py --visualize >> "$LOG_FILE" 2>&1; then
    echo "$(date): Dashboard generated successfully" >> "$LOG_FILE"

    # Export energy data for frozenwhispers widget
    python3 export_energy_widget.py >> "$LOG_FILE" 2>&1
    echo "$(date): Energy widget data exported" >> "$LOG_FILE"

    # Send notification via ntfy
    curl -s \
        -H "Title: Claude Code Dashboard Updated" \
        -H "Priority: default" \
        -H "Tags: chart_with_upwards_trend" \
        -d "Dashboard generated successfully." \
        "https://ntfy.sh/$CLAUDE_DASH_NTFY_TOPIC" > /dev/null

    echo "$(date): Notification sent" >> "$LOG_FILE"
else
    echo "$(date): Dashboard generation failed" >> "$LOG_FILE"

    # Send failure notification
    curl -s \
        -H "Title: Dashboard Generation Failed" \
        -H "Priority: high" \
        -H "Tags: warning" \
        -d "Check logs at $LOG_FILE" \
        "https://ntfy.sh/$CLAUDE_DASH_NTFY_TOPIC" > /dev/null
fi
