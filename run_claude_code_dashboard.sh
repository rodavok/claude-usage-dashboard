#!/bin/bash
# Automated Claude Code Dashboard Generator with ntfy notification
# Run via cron: 0 8 * * * /path/to/run_claude_code_dashboard.sh

set -e

# Configuration - auto-detect project directory from script location
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
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

    # Rebuild the conversation dashboard from any claude.ai export zips in this
    # folder. The zips must be downloaded from the export manifest by hand (the
    # links sit behind a Cloudflare challenge), so this just picks up whatever
    # is present - it re-assembles only when the zips are newer than the merged
    # conversations.json. Failure here must not fail the run.
    if ls conversations-*.zip conversation_data.json conversations.json >/dev/null 2>&1; then
        if python3 claude_conversation_dashboard.py --clusters 10 --visualize >> "$LOG_FILE" 2>&1; then
            echo "$(date): Conversation dashboard generated" >> "$LOG_FILE"

            curl -s \
                -H "Title: Conversation Dashboard Updated" \
                -H "Priority: default" \
                -H "Tags: speech_balloon" \
                -d "Conversation dashboard generated successfully." \
                "https://ntfy.sh/$CLAUDE_DASH_NTFY_TOPIC" > /dev/null

            echo "$(date): Conversation notification sent" >> "$LOG_FILE"
        else
            echo "$(date): WARNING - conversation dashboard generation failed" >> "$LOG_FILE"
        fi
    else
        echo "$(date): No claude.ai export data found, skipping conversation dashboard" >> "$LOG_FILE"
    fi

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
