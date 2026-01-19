#!/usr/bin/env python3
"""
Claude Conversations Dashboard
Analyzes conversations.json to provide insights into Claude usage patterns
"""

import json
import os
from datetime import datetime
from collections import defaultdict, Counter
import re

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# Energy consumption estimates (Joules per token) by model tier
# Based on research from multiple sources - see ENERGY_ESTIMATES.md for details
# These are approximate server-side only values; actual consumption varies by:
# - Infrastructure efficiency (10-100x variance)
# - Batch size and GPU utilization
# - Context length (2x context = ~3x energy)
# - Quantization (FP8 ~30% less than FP16)
# Sources:
#   - https://muxup.com/2026q1/per-query-energy-consumption-of-llms
#   - https://arxiv.org/html/2512.03024v1 (TokenPowerBench)
#   - https://llm-tracker.info/_TOORG/Power-Usage-and-Energy-Efficiency
ENERGY_ESTIMATES = {
    # Model tier: (joules_per_token, wh_per_1k_tokens)
    'haiku': {
        'j_per_token': 0.75,      # 0.5-1.0 J range, using midpoint
        'wh_per_1k': 0.00021,     # 0.75 J * 1000 / 3600
        'description': 'Small, fast model - minimal energy footprint'
    },
    'sonnet': {
        'j_per_token': 3.0,       # 2-4 J range, similar to GPT-4o estimates
        'wh_per_1k': 0.00083,     # 3.0 J * 1000 / 3600
        'description': 'Mid-tier model - moderate energy consumption'
    },
    'opus': {
        'j_per_token': 11.5,      # 8-15 J range, based on ~4 Wh/query reports
        'wh_per_1k': 0.0032,      # 11.5 J * 1000 / 3600
        'description': 'Large model - highest energy per token'
    },
    # Default for unknown/mixed usage (weighted toward Sonnet as most common)
    'default': {
        'j_per_token': 3.0,
        'wh_per_1k': 0.00083,
        'description': 'Default estimate (Sonnet-equivalent)'
    }
}

# Data center PUE (Power Usage Effectiveness) multiplier
# Accounts for cooling, networking, and other overhead
# Good data centers: 1.1-1.2, Average: 1.4-1.6
DEFAULT_PUE = 1.4


class ConversationAnalyzer:
    def __init__(self, conversations_path):
        self.conversations_path = os.path.expanduser(conversations_path)
        self.conversations = self.load_conversations()
        self.topics = defaultdict(list)
        self.stats = {
            'by_topic': defaultdict(lambda: {
                'count': 0, 
                'messages': 0, 
                'total_size': 0,
                'dates': [],
                'conversations': []
            }),
            'by_date': defaultdict(lambda: defaultdict(int)),
            'total_conversations': 0,
            'total_messages': 0
        }
        
    def load_conversations(self):
        """Load conversations from JSON file"""
        if not os.path.exists(self.conversations_path):
            raise FileNotFoundError(f"Conversations file not found: {self.conversations_path}")
        
        with open(self.conversations_path, 'r') as f:
            data = json.load(f)
        
        # Handle both dict and list formats
        if isinstance(data, dict):
            return list(data.values())
        return data
    
    def classify_topic_llm(self, conversation):
        """Classify topic using Claude API (if available)"""
        if not HAS_ANTHROPIC:
            return self.classify_topic_keyword(conversation)
        
        # Extract conversation text
        text = str(conversation)[:2000]  # Limit for classification
        
        try:
            client = anthropic.Anthropic()
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=50,
                messages=[{
                    "role": "user",
                    "content": f"""Classify this conversation into ONE topic category. Reply with ONLY the category name, nothing else.

Categories: Coding/Development, Data Analysis, Writing, Research, Learning, Creative, Business, Technical Documentation, System Administration, General Q&A

Conversation: {text}"""
                }]
            )
            return message.content[0].text.strip()
        except Exception as e:
            print(f"LLM classification failed: {e}, falling back to keywords")
            return self.classify_topic_keyword(conversation)

    def extract_text(self, conversation):
        """Extract text content from a conversation for clustering"""
        text = ""
        if isinstance(conversation, dict):
            for field in ['messages', 'chat_messages', 'content', 'history', 'chat']:
                if field in conversation:
                    if isinstance(conversation[field], list):
                        text = " ".join([str(m) for m in conversation[field]])
                    else:
                        text = str(conversation[field])
                    break
            if not text:
                for value in conversation.values():
                    if isinstance(value, str):
                        text += " " + value
        else:
            text = str(conversation)
        return text

    def _clean_text_for_clustering(self, text):
        """Remove dates, timestamps, and other noise from text for better clustering"""
        # Remove ISO dates and timestamps
        text = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[.\d]*Z?', ' ', text)
        text = re.sub(r'\d{4}-\d{2}-\d{2}', ' ', text)
        # Remove Unix timestamps (10+ digit numbers)
        text = re.sub(r'\b\d{10,}\b', ' ', text)
        # Remove UUIDs
        text = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', ' ', text, flags=re.IGNORECASE)
        # Remove file paths
        text = re.sub(r'(/[a-zA-Z0-9_.-]+)+', ' ', text)
        # Remove standalone numbers and short alphanumeric tokens
        text = re.sub(r'\b\d+\b', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def classify_topics_clustering(self, n_clusters=15):
        """Classify all conversations using TF-IDF + K-means clustering"""
        if not HAS_SKLEARN:
            print("sklearn not installed. Install with: pip install scikit-learn")
            return None

        print(f"Extracting text from {len(self.conversations)} conversations...")
        texts = [self._clean_text_for_clustering(self.extract_text(conv)) for conv in self.conversations]

        # Filter out empty texts
        valid_indices = [i for i, t in enumerate(texts) if t.strip()]
        valid_texts = [texts[i] for i in valid_indices]

        if len(valid_texts) < n_clusters:
            n_clusters = max(2, len(valid_texts) // 2)
            print(f"Reduced clusters to {n_clusters} (not enough conversations)")

        print(f"Vectorizing with TF-IDF...")
        # Custom stop words including common JSON/code noise and filler words
        extra_stops = {'true', 'false', 'null', 'none', 'type', 'content', 'role',
                       'user', 'assistant', 'message', 'text', 'id', 'name', 'value',
                       'like', 'just', 'actually', 'really', 'thing', 'things', 'want',
                       'need', 'know', 'think', 'make', 'sure', 'going', 'also', 'well'}
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=list(extra_stops) + list(TfidfVectorizer(stop_words='english').get_stop_words()),
            min_df=2,
            max_df=0.8,
            ngram_range=(1, 2),
            token_pattern=r'\b[a-zA-Z]{3,}\b'  # Only words with 3+ letters
        )

        try:
            tfidf_matrix = vectorizer.fit_transform(valid_texts)
        except ValueError as e:
            print(f"TF-IDF failed: {e}. Falling back to keyword classification.")
            return None

        print(f"Clustering into {n_clusters} groups...")
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(tfidf_matrix)

        # Get top terms for each cluster to create labels
        feature_names = vectorizer.get_feature_names_out()
        cluster_names = {}

        for cluster_id in range(n_clusters):
            # Get centroid and find top terms
            centroid = kmeans.cluster_centers_[cluster_id]
            top_indices = centroid.argsort()[-5:][::-1]
            top_terms = [feature_names[i] for i in top_indices]
            # Use top 2-3 terms as cluster name
            cluster_names[cluster_id] = " / ".join(top_terms[:5]).title()

        # Map back to all conversations (including empty ones)
        result = {}
        cluster_idx = 0
        for i in range(len(self.conversations)):
            if i in valid_indices:
                label = cluster_labels[cluster_idx]
                result[i] = cluster_names[label]
                cluster_idx += 1
            else:
                result[i] = "Uncategorized"

        print(f"Clustering complete. Found {n_clusters} topic groups:")
        for name in sorted(set(cluster_names.values())):
            print(f"  - {name}")

        return result

    def extract_date(self, conversation):
        """Extract date from conversation"""
        if isinstance(conversation, dict):
            # Common date field names
            for field in ['created_at', 'timestamp', 'date', 'created', 'time']:
                if field in conversation:
                    date_val = conversation[field]
                    try:
                        # Handle Unix timestamp
                        if isinstance(date_val, (int, float)):
                            return datetime.fromtimestamp(date_val)
                        # Handle ISO string
                        return datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                    except:
                        pass
        return None
    
    def calculate_size(self, conversation):
        """Calculate conversation size in bytes"""
        return len(json.dumps(conversation))
    
    def count_messages(self, conversation):
        """Count messages in conversation"""
        if isinstance(conversation, dict):
            for field in ['messages', 'chat_messages', 'history', 'content']:
                if field in conversation and isinstance(conversation[field], list):
                    return len(conversation[field])
        return 1  # Default if structure unclear
    
    def analyze(self, use_llm=False, n_clusters=15):
        """Run full analysis

        Args:
            use_llm: Use Claude API for classification
            n_clusters: Use TF-IDF + K-means clustering with this many clusters
        """
        print(f"Analyzing {len(self.conversations)} conversations...")

        # Pre-compute cluster labels if using clustering mode
        cluster_topics = None
        if n_clusters is not None:
            cluster_topics = self.classify_topics_clustering(n_clusters)
            print(cluster_topics)
            if cluster_topics is None:
                print("Clustering failed, using keyword classification instead.")

        for i, conv in enumerate(self.conversations):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(self.conversations)}", end='\r')

            # Classify topic
            if use_llm:
                topic = self.classify_topic_llm(conv)
            else:
                topic = cluster_topics[i]

            # Extract metrics
            date = self.extract_date(conv)
            size = self.calculate_size(conv)
            msg_count = self.count_messages(conv)

            # Update stats
            self.stats['by_topic'][topic]['count'] += 1
            self.stats['by_topic'][topic]['messages'] += msg_count
            self.stats['by_topic'][topic]['total_size'] += size
            self.stats['by_topic'][topic]['conversations'].append(conv)

            if date:
                self.stats['by_topic'][topic]['dates'].append(date)
                date_str = date.strftime('%Y-%m-%d')
                self.stats['by_date'][date_str][topic] += 1

            self.stats['total_conversations'] += 1
            self.stats['total_messages'] += msg_count

        print(f"\nAnalysis complete!")
        return self.stats
    
    def estimate_tokens(self, text_size):
        """Rough token estimation (1 token ≈ 4 characters)"""
        return text_size // 4

    def estimate_cost(self, tokens, input_rate=3.0, output_rate=15.0):
        """Estimate cost in USD based on token count.

        Uses Sonnet rates by default:
        - Input: $3/1M tokens
        - Output: $15/1M tokens

        Assumes ~30% input, 70% output based on typical conversation patterns.
        """
        blended_rate = 0.3 * input_rate + 0.7 * output_rate  # ~$11.4/1M
        return (tokens / 1_000_000) * blended_rate

    def estimate_energy(self, tokens, model='default', include_pue=True):
        """Estimate energy consumption in watt-hours based on token count.

        Args:
            tokens: Number of tokens
            model: Model tier ('haiku', 'sonnet', 'opus', or 'default')
            include_pue: Whether to include data center overhead (PUE multiplier)

        Returns:
            dict with energy metrics:
                - wh: Watt-hours consumed
                - kwh: Kilowatt-hours consumed
                - j: Joules consumed
                - equivalent_phone_charges: Energy in terms of phone charges (~12 Wh each)
                - equivalent_led_bulb_hours: Hours a 10W LED bulb could run
        """
        estimates = ENERGY_ESTIMATES.get(model, ENERGY_ESTIMATES['default'])
        j_per_token = estimates['j_per_token']

        # Calculate base energy
        joules = tokens * j_per_token
        wh = joules / 3600

        # Apply PUE if requested (accounts for cooling, etc.)
        if include_pue:
            wh *= DEFAULT_PUE
            joules *= DEFAULT_PUE

        kwh = wh / 1000

        return {
            'wh': wh,
            'kwh': kwh,
            'joules': joules,
            'equivalent_phone_charges': wh / 12,  # ~12 Wh per phone charge
            'equivalent_led_bulb_hours': wh / 10,  # 10W LED bulb
            'model_tier': model,
            'pue_applied': include_pue
        }
    
    def generate_report(self):
        """Generate text report"""
        print("\n" + "="*70)
        print("CLAUDE CONVERSATIONS DASHBOARD")
        print("="*70)
        
        print(f"\nTotal Conversations: {self.stats['total_conversations']}")
        print(f"Total Messages: {self.stats['total_messages']}")
        
        print("\n" + "-"*70)
        print("BY TOPIC")
        print("-"*70)
        
        sorted_topics = sorted(
            self.stats['by_topic'].items(),
            key=lambda x: x[1]['count'],
            reverse=True
        )
        
        for topic, data in sorted_topics:
            pct = (data['count'] / self.stats['total_conversations'] * 100)
            avg_msgs = data['messages'] / data['count'] if data['count'] > 0 else 0
            est_tokens = self.estimate_tokens(data['total_size'])
            
            print(f"\n{topic}:")
            print(f"  Conversations: {data['count']} ({pct:.1f}%)")
            print(f"  Total Messages: {data['messages']}")
            print(f"  Avg Messages/Conv: {avg_msgs:.1f}")
            print(f"  Total Size: {data['total_size']:,} bytes")
            print(f"  Estimated Tokens: {est_tokens:,}")
            
            if data['dates']:
                earliest = min(data['dates'])
                latest = max(data['dates'])
                print(f"  Date Range: {earliest.strftime('%Y-%m-%d')} to {latest.strftime('%Y-%m-%d')}")
        
        print("\n" + "-"*70)
        print("TIMELINE SUMMARY")
        print("-"*70)
        
        if self.stats['by_date']:
            sorted_dates = sorted(self.stats['by_date'].items())
            print(f"\nFirst conversation: {sorted_dates[0][0]}")
            print(f"Last conversation: {sorted_dates[-1][0]}")
            print(f"Active days: {len(sorted_dates)}")
            
            # Busiest day
            busiest = max(sorted_dates, key=lambda x: sum(x[1].values()))
            print(f"Busiest day: {busiest[0]} ({sum(busiest[1].values())} conversations)")
    
    def extract_title(self, conversation):
        """Extract a title or summary from a conversation"""
        if isinstance(conversation, dict):
            # Check for explicit title/name fields
            for field in ['title', 'name', 'subject', 'summary']:
                if field in conversation and conversation[field]:
                    return str(conversation[field])[:100]

            # Try to get first user message as title
            for msg_field in ['messages', 'chat_messages']:
                if msg_field in conversation and isinstance(conversation[msg_field], list):
                    for msg in conversation[msg_field]:
                        if isinstance(msg, dict):
                            role = msg.get('role', msg.get('type', ''))
                            if role in ['user', 'human']:
                                content = msg.get('content', msg.get('text', ''))
                                if isinstance(content, str) and content.strip():
                                    # Take first line or first 100 chars
                                    first_line = content.strip().split('\n')[0]
                                    return first_line[:100] + ('...' if len(first_line) > 100 else '')
                                elif isinstance(content, list):
                                    # Handle content blocks
                                    for block in content:
                                        if isinstance(block, dict) and block.get('type') == 'text':
                                            text = block.get('text', '')
                                            first_line = text.strip().split('\n')[0]
                                            return first_line[:100] + ('...' if len(first_line) > 100 else '')

        return "Untitled Conversation"

    def save_json_data(self, output_path, model_tier='default'):
        """Save processed data as JSON for visualization

        Args:
            output_path: Path to save JSON file
            model_tier: Model tier for energy estimates ('haiku', 'sonnet', 'opus', 'default')
        """
        # Calculate totals for summary
        total_tokens = sum(
            self.estimate_tokens(data['total_size'])
            for data in self.stats['by_topic'].values()
        )
        total_cost = self.estimate_cost(total_tokens)
        total_energy = self.estimate_energy(total_tokens, model=model_tier)

        output_data = {
            'summary': {
                'total_conversations': self.stats['total_conversations'],
                'total_messages': self.stats['total_messages'],
                'total_estimated_tokens': total_tokens,
                'total_estimated_cost': total_cost,
                'energy': {
                    'total_wh': total_energy['wh'],
                    'total_kwh': total_energy['kwh'],
                    'equivalent_phone_charges': total_energy['equivalent_phone_charges'],
                    'equivalent_led_bulb_hours': total_energy['equivalent_led_bulb_hours'],
                    'model_tier': model_tier,
                    'pue_applied': total_energy['pue_applied'],
                    'estimates_config': ENERGY_ESTIMATES[model_tier]
                }
            },
            'by_topic': {},
            'timeline': [],
            'conversations': []
        }

        # Process topic data
        for topic, data in self.stats['by_topic'].items():
            topic_tokens = self.estimate_tokens(data['total_size'])
            topic_energy = self.estimate_energy(topic_tokens, model=model_tier)
            output_data['by_topic'][topic] = {
                'count': data['count'],
                'messages': data['messages'],
                'size': data['total_size'],
                'estimated_tokens': topic_tokens,
                'estimated_cost': self.estimate_cost(topic_tokens),
                'estimated_energy_wh': topic_energy['wh'],
                'percentage': (data['count'] / self.stats['total_conversations'] * 100)
            }

            # Add individual conversations with metadata
            for conv in data['conversations']:
                conv_date = self.extract_date(conv)
                conv_size = self.calculate_size(conv)
                conv_tokens = self.estimate_tokens(conv_size)
                conv_energy = self.estimate_energy(conv_tokens, model=model_tier)
                output_data['conversations'].append({
                    'title': self.extract_title(conv),
                    'topic': topic,
                    'date': conv_date.strftime('%Y-%m-%d') if conv_date else None,
                    'messages': self.count_messages(conv),
                    'size': conv_size,
                    'estimated_tokens': conv_tokens,
                    'estimated_cost': self.estimate_cost(conv_tokens),
                    'estimated_energy_wh': conv_energy['wh']
                })

        # Sort conversations by date (most recent first)
        output_data['conversations'].sort(
            key=lambda x: x['date'] or '1970-01-01',
            reverse=True
        )

        # Process timeline data
        for date_str, topics in sorted(self.stats['by_date'].items()):
            output_data['timeline'].append({
                'date': date_str,
                'topics': dict(topics),
                'total': sum(topics.values())
            })

        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\nData saved to: {output_path}")
        return output_path


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Claude conversations')
    parser.add_argument('--path', default='~/.claude/conversations/conversations.json',
                       help='Path to conversations.json')
    parser.add_argument('--output', default='conversation_data.json',
                       help='Output JSON file for visualization')
    parser.add_argument('--llm', action='store_true',
                       help='Use Claude API for topic classification (requires anthropic package)')
    parser.add_argument('--clusters', type=int, default=15,
                       help='Use NLP clustering with N groups (requires scikit-learn). Overrides --llm.')
    parser.add_argument('--visualize', action='store_true',
                       help='Generate HTML dashboard')
    parser.add_argument('--model', choices=['haiku', 'sonnet', 'opus', 'default'], default='default',
                       help='Model tier for energy estimates (default: default/sonnet-equivalent)')

    args = parser.parse_args()

    try:
        analyzer = ConversationAnalyzer(args.path)
        analyzer.analyze(use_llm=args.llm, n_clusters=args.clusters)
        analyzer.generate_report()

        # Save data for visualization (with energy estimates for specified model tier)
        data_path = analyzer.save_json_data(args.output, model_tier=args.model)
        
        if args.visualize:
            from dashboard_generator import generate_dashboard
            generate_dashboard(data_path)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
