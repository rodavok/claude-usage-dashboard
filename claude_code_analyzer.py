#!/usr/bin/env python3
"""
Claude Code Project Analyzer
Analyzes Claude Code usage per-project from ~/.claude/projects/
Focuses on token consumption and energy estimates using actual usage data.
"""

import json
import os
from datetime import datetime
from collections import defaultdict
from pathlib import Path


# Energy consumption estimates (Joules per token) by model tier
# Based on research - see ENERGY_ESTIMATES.md for details
ENERGY_ESTIMATES = {
    'haiku': {'j_per_token': 0.75, 'wh_per_1k': 0.00021},
    'sonnet': {'j_per_token': 3.0, 'wh_per_1k': 0.00083},
    'opus': {'j_per_token': 11.5, 'wh_per_1k': 0.0032},
    'default': {'j_per_token': 3.0, 'wh_per_1k': 0.00083}
}

DEFAULT_PUE = 1.4  # Data center overhead multiplier


def get_model_tier(model_name):
    """Extract model tier from model name string."""
    if not model_name:
        return 'default'
    model_lower = model_name.lower()
    if 'haiku' in model_lower:
        return 'haiku'
    elif 'opus' in model_lower:
        return 'opus'
    elif 'sonnet' in model_lower:
        return 'sonnet'
    return 'default'


def estimate_energy(tokens, model_tier='default', include_pue=True):
    """Estimate energy consumption in watt-hours."""
    estimates = ENERGY_ESTIMATES.get(model_tier, ENERGY_ESTIMATES['default'])
    j_per_token = estimates['j_per_token']
    joules = tokens * j_per_token
    wh = joules / 3600
    if include_pue:
        wh *= DEFAULT_PUE
    return wh


class ClaudeCodeAnalyzer:
    def __init__(self, projects_dir='~/Projects', claude_projects_dir='~/.claude/projects'):
        self.projects_dir = Path(os.path.expanduser(projects_dir))
        self.claude_projects_dir = Path(os.path.expanduser(claude_projects_dir))
        self.projects = {}  # project_name -> project data
        self.conversations = []  # all conversations with metadata

    def path_to_claude_dir_name(self, path):
        """Convert a path to Claude's directory naming convention."""
        # Claude replaces slashes and underscores with dashes
        return str(path).replace('/', '-').replace('_', '-')

    def find_projects_with_claude_code(self):
        """Find projects in ~/Projects that have Claude Code data."""
        projects_found = []

        if not self.claude_projects_dir.exists():
            print(f"Claude projects directory not found: {self.claude_projects_dir}")
            return projects_found

        # Get all claude project directories
        claude_dirs = {d.name: d for d in self.claude_projects_dir.iterdir() if d.is_dir()}

        # Check each project in ~/Projects
        if self.projects_dir.exists():
            for project_path in self.projects_dir.iterdir():
                if project_path.is_dir():
                    # Convert project path to claude dir name format
                    claude_dir_name = self.path_to_claude_dir_name(project_path)

                    if claude_dir_name in claude_dirs:
                        projects_found.append({
                            'name': project_path.name,
                            'path': project_path,
                            'claude_dir': claude_dirs[claude_dir_name]
                        })

        return projects_found

    def parse_jsonl_file(self, jsonl_path):
        """Parse a JSONL file and extract message data."""
        messages = []
        try:
            with open(jsonl_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            obj = json.loads(line)
                            messages.append(obj)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"Error reading {jsonl_path}: {e}")
        return messages

    def extract_conversation_data(self, messages, session_id, project_name):
        """Extract token usage and metadata from conversation messages."""
        total_input_tokens = 0
        total_output_tokens = 0
        total_cache_read_tokens = 0
        total_cache_creation_tokens = 0

        user_messages = []
        assistant_messages = []
        timestamps = []
        models_used = set()
        summary = None
        first_user_prompt = None

        for msg in messages:
            msg_type = msg.get('type', '')
            timestamp = msg.get('timestamp')

            if timestamp:
                try:
                    timestamps.append(datetime.fromisoformat(timestamp.replace('Z', '+00:00')))
                except:
                    pass

            # Extract summary if available
            if msg_type == 'summary':
                summary = msg.get('summary', '')

            # Extract user message content
            if msg_type == 'user':
                user_msg = msg.get('message', {})
                content = user_msg.get('content', '')
                if isinstance(content, str) and content.strip():
                    user_messages.append(content)
                    if first_user_prompt is None:
                        first_user_prompt = content[:200]

            # Extract assistant message with usage data
            if msg_type == 'assistant':
                assistant_msg = msg.get('message', {})
                model = assistant_msg.get('model', '')
                if model:
                    models_used.add(model)

                usage = assistant_msg.get('usage', {})
                if usage:
                    total_input_tokens += usage.get('input_tokens', 0)
                    total_output_tokens += usage.get('output_tokens', 0)
                    total_cache_read_tokens += usage.get('cache_read_input_tokens', 0)
                    total_cache_creation_tokens += usage.get('cache_creation_input_tokens', 0)

                # Also count content
                content = assistant_msg.get('content', [])
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get('type') == 'text':
                            assistant_messages.append(block.get('text', ''))

        # Determine primary model
        primary_model = None
        for model in models_used:
            if 'opus' in model.lower():
                primary_model = model
                break
            elif 'sonnet' in model.lower() and primary_model is None:
                primary_model = model
            elif primary_model is None:
                primary_model = model

        model_tier = get_model_tier(primary_model)

        # Calculate totals
        total_tokens = total_input_tokens + total_output_tokens

        # Determine date range
        start_date = min(timestamps) if timestamps else None
        end_date = max(timestamps) if timestamps else None

        # Create title from summary or first user prompt
        title = summary or first_user_prompt or "Untitled Session"
        if len(title) > 100:
            title = title[:97] + "..."

        return {
            'session_id': session_id,
            'project': project_name,
            'title': title,
            'summary': summary,
            'first_prompt': first_user_prompt,
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'date': start_date.strftime('%Y-%m-%d') if start_date else None,
            'user_message_count': len(user_messages),
            'assistant_message_count': len(assistant_messages),
            'total_turns': len(user_messages),
            'models_used': list(models_used),
            'primary_model': primary_model,
            'model_tier': model_tier,
            'tokens': {
                'input': total_input_tokens,
                'output': total_output_tokens,
                'cache_read': total_cache_read_tokens,
                'cache_creation': total_cache_creation_tokens,
                'total': total_tokens
            },
            'energy_wh': estimate_energy(total_tokens, model_tier),
            'cost_estimate': self.estimate_cost(total_input_tokens, total_output_tokens, model_tier)
        }

    def estimate_cost(self, input_tokens, output_tokens, model_tier):
        """Estimate cost based on model tier and token counts."""
        # Pricing per 1M tokens (approximate as of 2025)
        pricing = {
            'haiku': {'input': 0.25, 'output': 1.25},
            'sonnet': {'input': 3.0, 'output': 15.0},
            'opus': {'input': 15.0, 'output': 75.0},
            'default': {'input': 3.0, 'output': 15.0}
        }
        rates = pricing.get(model_tier, pricing['default'])
        cost = (input_tokens / 1_000_000) * rates['input'] + (output_tokens / 1_000_000) * rates['output']
        return cost

    def analyze_project(self, project_info):
        """Analyze all conversations for a single project."""
        project_name = project_info['name']
        claude_dir = project_info['claude_dir']

        conversations = []

        # Find all JSONL files (main conversations, not subagents)
        for jsonl_file in claude_dir.glob('*.jsonl'):
            session_id = jsonl_file.stem
            messages = self.parse_jsonl_file(jsonl_file)

            if messages:
                conv_data = self.extract_conversation_data(messages, session_id, project_name)
                if conv_data['tokens']['total'] > 0:  # Only include if has token data
                    conversations.append(conv_data)

        # Also check for subagent conversations
        for subdir in claude_dir.iterdir():
            if subdir.is_dir():
                subagents_dir = subdir / 'subagents'
                if subagents_dir.exists():
                    for jsonl_file in subagents_dir.glob('*.jsonl'):
                        session_id = f"{subdir.name}/subagent/{jsonl_file.stem}"
                        messages = self.parse_jsonl_file(jsonl_file)
                        if messages:
                            conv_data = self.extract_conversation_data(messages, session_id, project_name)
                            conv_data['is_subagent'] = True
                            if conv_data['tokens']['total'] > 0:
                                conversations.append(conv_data)

        return conversations

    def analyze(self):
        """Run full analysis across all projects."""
        print("Scanning for projects with Claude Code usage...")
        projects_found = self.find_projects_with_claude_code()

        if not projects_found:
            print("No projects with Claude Code data found.")
            return None

        print(f"Found {len(projects_found)} projects with Claude Code data:")
        for p in projects_found:
            print(f"  - {p['name']}")

        print("\nAnalyzing conversations...")

        for project_info in projects_found:
            project_name = project_info['name']
            conversations = self.analyze_project(project_info)

            # Aggregate project stats
            total_input = sum(c['tokens']['input'] for c in conversations)
            total_output = sum(c['tokens']['output'] for c in conversations)
            total_cache_read = sum(c['tokens']['cache_read'] for c in conversations)
            total_cache_creation = sum(c['tokens']['cache_creation'] for c in conversations)
            total_tokens = sum(c['tokens']['total'] for c in conversations)
            total_energy = sum(c['energy_wh'] for c in conversations)
            total_cost = sum(c['cost_estimate'] for c in conversations)

            # Get date range
            dates = [c['date'] for c in conversations if c['date']]

            self.projects[project_name] = {
                'name': project_name,
                'path': str(project_info['path']),
                'conversation_count': len(conversations),
                'total_turns': sum(c['total_turns'] for c in conversations),
                'tokens': {
                    'input': total_input,
                    'output': total_output,
                    'cache_read': total_cache_read,
                    'cache_creation': total_cache_creation,
                    'total': total_tokens
                },
                'energy_wh': total_energy,
                'cost_estimate': total_cost,
                'first_date': min(dates) if dates else None,
                'last_date': max(dates) if dates else None,
                'conversations': conversations
            }

            self.conversations.extend(conversations)

            print(f"  {project_name}: {len(conversations)} sessions, {total_tokens:,} tokens")

        print(f"\nTotal: {len(self.conversations)} conversations across {len(self.projects)} projects")
        return self.projects

    def generate_report(self):
        """Print a text summary report."""
        if not self.projects:
            print("No data to report. Run analyze() first.")
            return

        total_tokens = sum(p['tokens']['total'] for p in self.projects.values())
        total_energy = sum(p['energy_wh'] for p in self.projects.values())
        total_cost = sum(p['cost_estimate'] for p in self.projects.values())
        total_convs = sum(p['conversation_count'] for p in self.projects.values())

        print("\n" + "=" * 70)
        print("CLAUDE CODE USAGE DASHBOARD")
        print("=" * 70)

        print(f"\nTotal Projects: {len(self.projects)}")
        print(f"Total Sessions: {total_convs}")
        print(f"Total Tokens: {total_tokens:,}")
        print(f"Estimated Energy: {total_energy:.2f} Wh ({total_energy / 12:.2f} phone charges)")
        print(f"Estimated Cost: ${total_cost:.2f}")

        print("\n" + "-" * 70)
        print("BY PROJECT (sorted by token usage)")
        print("-" * 70)

        sorted_projects = sorted(
            self.projects.values(),
            key=lambda x: x['tokens']['total'],
            reverse=True
        )

        for proj in sorted_projects:
            pct = (proj['tokens']['total'] / total_tokens * 100) if total_tokens > 0 else 0
            print(f"\n{proj['name']}:")
            print(f"  Sessions: {proj['conversation_count']}")
            print(f"  Total Tokens: {proj['tokens']['total']:,} ({pct:.1f}%)")
            print(f"    - Input: {proj['tokens']['input']:,}")
            print(f"    - Output: {proj['tokens']['output']:,}")
            print(f"    - Cache Read: {proj['tokens']['cache_read']:,}")
            print(f"  Energy: {proj['energy_wh']:.2f} Wh")
            print(f"  Cost: ${proj['cost_estimate']:.2f}")
            if proj['first_date'] and proj['last_date']:
                print(f"  Date Range: {proj['first_date']} to {proj['last_date']}")

    def get_top_token_conversations(self, n=10):
        """Get the conversations that consumed the most tokens."""
        sorted_convs = sorted(
            self.conversations,
            key=lambda x: x['tokens']['total'],
            reverse=True
        )
        return sorted_convs[:n]

    def save_json_data(self, output_path='claude_code_data.json'):
        """Save processed data as JSON for visualization."""
        if not self.projects:
            print("No data to save. Run analyze() first.")
            return None

        total_input = sum(p['tokens']['input'] for p in self.projects.values())
        total_output = sum(p['tokens']['output'] for p in self.projects.values())
        total_cache_read = sum(p['tokens']['cache_read'] for p in self.projects.values())
        total_cache_creation = sum(p['tokens']['cache_creation'] for p in self.projects.values())
        total_tokens = sum(p['tokens']['total'] for p in self.projects.values())
        total_energy = sum(p['energy_wh'] for p in self.projects.values())
        total_cost = sum(p['cost_estimate'] for p in self.projects.values())

        output_data = {
            'summary': {
                'total_projects': len(self.projects),
                'total_conversations': len(self.conversations),
                'total_turns': sum(p['total_turns'] for p in self.projects.values()),
                'tokens': {
                    'input': total_input,
                    'output': total_output,
                    'cache_read': total_cache_read,
                    'cache_creation': total_cache_creation,
                    'total': total_tokens
                },
                'energy_wh': total_energy,
                'energy_kwh': total_energy / 1000,
                'phone_charges_equiv': total_energy / 12,
                'cost_estimate': total_cost
            },
            'by_project': {},
            'conversations': [],
            'top_consumers': []
        }

        # Process projects
        for name, proj in self.projects.items():
            output_data['by_project'][name] = {
                'conversation_count': proj['conversation_count'],
                'total_turns': proj['total_turns'],
                'tokens': proj['tokens'],
                'energy_wh': proj['energy_wh'],
                'cost_estimate': proj['cost_estimate'],
                'percentage': (proj['tokens']['total'] / total_tokens * 100) if total_tokens > 0 else 0,
                'first_date': proj['first_date'],
                'last_date': proj['last_date']
            }

        # Add all conversations (sorted by date, most recent first)
        for conv in self.conversations:
            output_data['conversations'].append({
                'project': conv['project'],
                'title': conv['title'],
                'date': conv['date'],
                'turns': conv['total_turns'],
                'model_tier': conv['model_tier'],
                'primary_model': conv['primary_model'],
                'tokens': conv['tokens'],
                'energy_wh': conv['energy_wh'],
                'cost_estimate': conv['cost_estimate'],
                'is_subagent': conv.get('is_subagent', False)
            })

        output_data['conversations'].sort(
            key=lambda x: x['date'] or '1970-01-01',
            reverse=True
        )

        # Top token consumers
        top_convs = self.get_top_token_conversations(20)
        for conv in top_convs:
            output_data['top_consumers'].append({
                'project': conv['project'],
                'title': conv['title'],
                'date': conv['date'],
                'total_tokens': conv['tokens']['total'],
                'input_tokens': conv['tokens']['input'],
                'output_tokens': conv['tokens']['output'],
                'model_tier': conv['model_tier'],
                'energy_wh': conv['energy_wh'],
                'cost_estimate': conv['cost_estimate']
            })

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\nData saved to: {output_path}")
        return output_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Analyze Claude Code usage per project')
    parser.add_argument('--projects-dir', default='~/Projects',
                       help='Directory containing your projects (default: ~/Projects)')
    parser.add_argument('--output', default='claude_code_data.json',
                       help='Output JSON file for visualization')
    parser.add_argument('--visualize', action='store_true',
                       help='Generate HTML dashboard')

    args = parser.parse_args()

    try:
        analyzer = ClaudeCodeAnalyzer(projects_dir=args.projects_dir)
        analyzer.analyze()
        analyzer.generate_report()

        # Save JSON data
        data_path = analyzer.save_json_data(args.output)

        if args.visualize and data_path:
            from claude_code_dashboard import generate_claude_code_dashboard
            generate_claude_code_dashboard(data_path)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
