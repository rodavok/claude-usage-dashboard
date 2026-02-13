#!/usr/bin/env python3
"""
Export energy data for the frozenwhispers Jekyll widget.
Reads from claude_dashboard output and writes simplified JSON to _data/.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
DEFAULT_INPUT = SCRIPT_DIR / "conversation_data.json"
DEFAULT_OUTPUT = Path.home() / "Projects" / "frozenwhispers" / "_data" / "claude_energy.json"

# Energy equivalence constants (from ENERGY_ESTIMATES.md)
WH_PER_PHONE_CHARGE = 12
WH_PER_LED_HOUR = 10
WH_PER_COROLLA_MILE = 1053  # 33,700 Wh/gal / 32 mpg
WH_PER_FLIGHT_MILE = 320    # passenger-mile


def export_energy_data(input_path=None, output_path=None):
    """Export energy data to Jekyll-friendly JSON format."""
    input_path = Path(input_path or DEFAULT_INPUT)
    output_path = Path(output_path or DEFAULT_OUTPUT)

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        print("Run the dashboard analyzer first:")
        print("  python3 claude_conversation_dashboard.py --model sonnet")
        sys.exit(1)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(input_path, 'r') as f:
        data = json.load(f)

    summary = data.get('summary', {})
    energy = summary.get('energy', {})
    by_topic = data.get('by_topic', {})

    total_wh = energy.get('total_wh', 0)

    # Build simplified output for widget
    widget_data = {
        'total_wh': total_wh,
        'total_kwh': energy.get('total_kwh', 0),
        'total_tokens': summary.get('total_estimated_tokens', 0),
        'conversations': summary.get('total_conversations', 0),
        'messages': summary.get('total_messages', 0),
        'model_tier': energy.get('model_tier', 'default'),

        # Pre-calculated equivalents
        'equivalent_phone_charges': total_wh / WH_PER_PHONE_CHARGE,
        'equivalent_led_bulb_hours': total_wh / WH_PER_LED_HOUR,
        'equiv_corolla_miles': total_wh / WH_PER_COROLLA_MILE,
        'equiv_flight_miles': total_wh / WH_PER_FLIGHT_MILE,

        # Energy by topic (for chart)
        'by_topic': {
            topic: stats.get('estimated_energy_wh', 0)
            for topic, stats in by_topic.items()
        },

        'generated_at': datetime.now().isoformat()
    }

    with open(output_path, 'w') as f:
        json.dump(widget_data, f, indent=2)

    print(f"Exported energy data to: {output_path}")
    print(f"  Total: {total_wh:.2f} Wh ({widget_data['equivalent_phone_charges']:.1f} phone charges)")
    print(f"  Topics: {len(by_topic)}")

    return output_path


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Export energy data for Jekyll widget')
    parser.add_argument('--input', '-i', help='Input JSON from dashboard analyzer')
    parser.add_argument('--output', '-o', help='Output path for Jekyll _data/')
    args = parser.parse_args()

    export_energy_data(args.input, args.output)
