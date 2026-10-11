#!/usr/bin/env python3
"""
Dashboard Generator - builds one interactive HTML dashboard covering both
claude.ai chats (conversation_data.json) and Claude Code sessions
(claude_code_data.json). Either input may be missing; the page lets you
toggle each source on and off and recomputes every stat in the browser.
"""

import json
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SCRIPT_DIR, 'dashboard_template.html')

DEFAULT_CHAT_PATH = 'conversation_data.json'
DEFAULT_CODE_PATH = 'claude_code_data.json'
DEFAULT_OUTPUT_PATH = 'dashboard.html'


def load_json(path):
    if path and os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f)
    return None


def chat_records(data):
    """Flatten conversation_data.json into dashboard records."""
    for c in data.get('conversations', []):
        yield {
            'src': 'chat',
            'title': c.get('title') or 'Untitled conversation',
            'group': c.get('topic') or 'Uncategorized',
            'date': c.get('date'),
            'ts': c.get('timestamp'),
            'n': 1,
            # Older data files predate the prompts field; chats alternate turns
            'prompts': c.get('prompts', (c.get('messages', 0) + 1) // 2),
            'tok': c.get('estimated_tokens', 0),
            'cost': round(c.get('estimated_cost', 0), 5),
            'wh': round(c.get('estimated_energy_wh', 0), 4),
            'tier': None,
            'model': None,
        }


def code_records(data):
    """Flatten claude_code_data.json into dashboard records."""
    for c in data.get('conversations', []):
        tokens = c.get('tokens', {})
        is_subagent = c.get('is_subagent', False)
        yield {
            'src': 'code',
            'title': c.get('title') or 'Untitled session',
            'group': c.get('project') or 'Unknown project',
            'date': c.get('date'),
            'ts': c.get('timestamp'),
            # Subagent runs belong to a parent session; stats-cache days hold several
            'n': 0 if is_subagent else c.get('session_count', 1),
            'prompts': c.get('turns', 0),
            'tok': tokens.get('total', 0),
            'cr': tokens.get('cache_read', 0),
            'cost': round(c.get('cost_estimate', 0), 5),
            'wh': round(c.get('energy_wh', 0), 4),
            'tier': c.get('model_tier'),
            'model': c.get('primary_model'),
            'sub': is_subagent,
            'bf': c.get('is_backfill', False),
        }


def generate_dashboard(chat_path=DEFAULT_CHAT_PATH, code_path=DEFAULT_CODE_PATH,
                       output_path=DEFAULT_OUTPUT_PATH):
    """Generate the combined HTML dashboard from whichever data files exist."""
    chat = load_json(chat_path)
    code = load_json(code_path)
    if chat is None and code is None:
        raise FileNotFoundError(
            f"No data found at {chat_path} or {code_path}. Run "
            "claude_conversation_dashboard.py or claude_code_analyzer.py first.")

    records = []
    if chat is not None:
        records.extend(chat_records(chat))
    if code is not None:
        records.extend(code_records(code))

    chat_tier = 'default'
    if chat is not None:
        chat_tier = chat.get('summary', {}).get('energy', {}).get('model_tier', 'default')

    payload = {
        'meta': {
            'generated': datetime.now().strftime('%b %-d, %Y %H:%M'),
            'chat_tier': 'Sonnet-equivalent default' if chat_tier == 'default' else chat_tier,
        },
        'records': records,
    }

    with open(TEMPLATE_PATH, 'r') as f:
        template = f.read()
    # Escape "</" so titles containing "</script>" can't end the script block
    data_js = json.dumps(payload, separators=(',', ':')).replace('</', '<\\/')
    html = template.replace('/*__DATA__*/null', data_js, 1)

    with open(output_path, 'w') as f:
        f.write(html)

    sources = [name for name, d in (('chat', chat), ('code', code)) if d is not None]
    print(f"\nDashboard generated: {output_path} ({' + '.join(sources)}, {len(records):,} records)")
    print(f"Open in browser: file://{os.path.abspath(output_path)}")
    return output_path


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Build the combined Claude usage dashboard')
    parser.add_argument('--chat', default=DEFAULT_CHAT_PATH,
                        help=f'claude.ai data from claude_conversation_dashboard.py (default: {DEFAULT_CHAT_PATH})')
    parser.add_argument('--code', default=DEFAULT_CODE_PATH,
                        help=f'Claude Code data from claude_code_analyzer.py (default: {DEFAULT_CODE_PATH})')
    parser.add_argument('--output', default=DEFAULT_OUTPUT_PATH,
                        help=f'Output HTML file (default: {DEFAULT_OUTPUT_PATH})')
    args = parser.parse_args()

    generate_dashboard(args.chat, args.code, args.output)
