# Claude Conversations Dashboard

Analyze your Claude Code conversations to understand usage patterns, topics, and token consumption.

## Quick Start

```bash
# Basic analysis (keyword-based topic classification)
python3 claude_conversation_dashboard.py

# With visualization
python3 claude_conversation_dashboard.py --visualize

# Using Claude API for better topic classification
python3 claude_conversation_dashboard.py --llm --visualize

# Custom paths
python3 claude_conversation_dashboard.py \
  --path ~/.claude/conversations/conversations.json \
  --output my_data.json \
  --visualize
```

## Features

### Current Metrics
- **Conversations by topic** - % distribution pie chart
- **Messages per topic** - Total and average
- **Data size by topic** - Raw bytes and estimated tokens
- **Timeline visualization** - Topics over time
- **Cost estimation** - Approximate token usage per topic

### Visualizations
1. **Pie chart** - Topic distribution percentage
2. **Bar charts** - Messages and tokens by topic
3. **Timeline** - Daily conversation patterns by topic
4. **Detailed table** - Complete breakdown

## Additional Insights Available

Based on typical conversations.json structure, here are other interesting views:

### Conversation Patterns
- **Peak usage hours** - What time of day you use Claude most
- **Day of week patterns** - Weekday vs weekend usage
- **Conversation length distribution** - Short vs long conversations
- **Session duration** - How long conversations typically last

### Topic Analysis
- **Topic transitions** - What topics follow each other
- **Topic depth** - Average complexity by message count
- **Topic recency** - How topics trend over time
- **Cross-topic conversations** - Multi-topic sessions

### Efficiency Metrics
- **Questions vs follow-ups** - Conversation effectiveness
- **Token efficiency** - Tokens per resolved query
- **Retry patterns** - Where regeneration is common
- **Context window usage** - Long context utilization

### Content Analysis
- **Code vs prose ratio** - Type of assistance requested
- **Tool usage patterns** - Which Claude features used most
- **Language detection** - Programming languages used
- **File types** - Types of files discussed/created

### Cost & Usage
- **Projected monthly cost** - Based on usage patterns
- **Peak cost days** - Highest token consumption
- **Topic cost ranking** - Most expensive topics
- **Efficiency trends** - Cost per conversation over time

## Extending the Analysis

To add custom metrics, modify `claude_conversation_dashboard.py`:

```python
# In the analyze() method, add:
self.stats['custom_metric'] = your_calculation()

# In generate_report(), display:
print(f"Custom Metric: {self.stats['custom_metric']}")
```

To add visualizations, edit `dashboard_generator.py`:

```javascript
// Add new chart in HTML
<canvas id="customChart"></canvas>

// Add Chart.js code
new Chart(document.getElementById('customChart'), {
    // your chart config
});
```

## Dependencies

Optional:
- `anthropic` - For LLM-based topic classification
  ```bash
  pip install anthropic
  export ANTHROPIC_API_KEY=your_key
  ```

## Tips

1. **First run**: Use keyword classification (fast, free)
2. **Better accuracy**: Use `--llm` flag with API key
3. **Large datasets**: Run without `--visualize` first to check stats
4. **Custom topics**: Edit keyword lists in `classify_topic_keyword()`

## Output Files

- `conversation_data.json` - Processed data for visualization
- `dashboard.html` - Interactive dashboard (open in browser)

## Troubleshooting

**File not found error**:
```bash
ls -la ~/.claude/conversations/
# Check actual path and update --path flag
```

**Import errors**:
```bash
pip install anthropic  # If using --llm
```

**JSON parsing errors**:
- Check conversations.json format
- Script handles both dict and list formats
- May need to update field names in `extract_date()` and `count_messages()`

## Privacy Note

All analysis is local. The `--llm` flag sends conversation snippets (first 2000 chars) to Claude API for classification only.
