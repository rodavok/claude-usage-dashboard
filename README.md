# Claude Dashboard

Analyze your [Claude Code](https://claude.ai/code) usage with interactive dashboards showing topics, token consumption, and energy estimates.

## Scripts Overview

| Script | Purpose | Data Source |
|--------|---------|-------------|
| `claude_conversation_dashboard.py` | Analyze conversations by topic | claude.ai export zips in this folder |
| `import_export.py` | Unpack claude.ai export zips into flat JSON | `conversations-*.zip`, `projects-*.zip`, `light_metadata-*.zip` |
| `claude_code_analyzer.py` | Analyze per-project usage with energy estimates | `~/.claude/projects/` |
| `dashboard_generator.py` | Build the combined `dashboard.html` | JSON from both analyzers |

## Installation

```bash
git clone https://github.com/yourusername/claude_dashboard.git
cd claude_dashboard

# Optional dependencies (for better topic classification)
pip install -r requirements.txt
```

## Conversation Dashboard

Analyzes your claude.ai conversations by topic distribution, message counts, and token usage.

### Getting your data

Request a data export from claude.ai (Settings -> Privacy -> Export data). The email
links to a `manifest-*.json` listing four zips:

| Zip | Contents |
|-----|----------|
| `conversations-000.zip`, `conversations-001.zip`, ... | `conversations.json`, split into parts |
| `projects-000.zip` | `projects/<uuid>.json`, one file per project |
| `light_metadata-000.zip` | `users.json`, `login_history.json` |

Download each zip from its manifest link **in your browser** - the URLs sit behind a
Cloudflare challenge and are single-use, so a script cannot fetch them - then drop all
four in this folder. The dashboard unpacks and merges them automatically, re-assembling
whenever the zips are newer than the merged `conversations.json`.

```bash
# NLP clustering for dynamic topic discovery (recommended)
python3 claude_conversation_dashboard.py --clusters 10 --visualize

# Using Claude API for topic classification
python3 claude_conversation_dashboard.py --llm --visualize

# Unpack the zips without analyzing
python3 import_export.py

# Download the zips from the newest manifest-*.json via your browser, then unpack
# (links expire 24h after the export is created; older zips go to previous_exports/)
python3 import_export.py --fetch

# Custom paths (--path takes an export directory or a conversations.json)
python3 claude_conversation_dashboard.py \
  --path ~/Downloads/claude-export \
  --output my_data.json \
  --visualize
```

Topic clustering needs `scikit-learn` (`pip install -r requirements.txt`); without it
the conversation dashboard exits with an error rather than falling back.

**Output:** `conversation_data.json`, plus `dashboard.html` with `--visualize`

## Claude Code Analyzer

Analyzes per-project token usage with energy consumption estimates. Reads from `~/.claude/projects/`.

```bash
# Basic analysis
python3 claude_code_analyzer.py

# With visualization
python3 claude_code_analyzer.py --visualize

# Custom projects directory
python3 claude_code_analyzer.py --projects-dir ~/Projects --visualize

# Include a .claude folder copied from another computer
python3 claude_code_analyzer.py --extra-claude-dir /path/to/old/.claude --visualize
```

**Other computers:** Claude Code keeps session logs locally and doesn't sync them. Copy each machine's `~/.claude` into `claude folders/<any name>/` here and it's picked up automatically. Sessions are grouped by the `~/Projects/<name>` folder they ran in, so different usernames or paths on each machine don't matter, and duplicate sessions are only counted once. The folder is gitignored. Delete the copied `.credentials.json` files, since they hold login tokens.

**Deleted transcripts:** Claude Code deletes transcripts after `cleanupPeriodDays` (default 30). If a `.claude` folder has a `stats-cache.json`, the days it covers before that folder's earliest surviving transcript are added as daily totals under "Unattributed (stats cache)". Those tokens are real, but the cache has no project info, and the input/output/cache split is apportioned from each model's lifetime totals. Set `"cleanupPeriodDays": 99999` in `~/.claude/settings.json` to keep transcripts.

**Output:** `claude_code_data.json`, plus `dashboard.html` with `--visualize`

See `ENERGY_ESTIMATES.md` for details on energy calculation methodology.

## The dashboard

Both analyzers feed one page, `dashboard.html`. `--visualize` on either analyzer rebuilds
it from whichever data files exist, or rebuild it directly:

```bash
python3 dashboard_generator.py            # reads conversation_data.json + claude_code_data.json
python3 dashboard_generator.py --chat my_data.json --code other.json --output out.html
```

It's a single self-contained file with no network requests. Every number is recomputed
in the browser from the per-conversation records, so the controls in the filter bar
scope the whole page:

- **Sources**: toggle claude.ai chats and Claude Code sessions on and off
- **Range**: last 30 days, 90 days, 1 year, or everything
- **Measure**: conversations, tokens, cost, or energy, used by every chart
- **Focus**: click a chat topic or code project to narrow the page to it

Sections: totals with a chat/code split, activity over time (with a table view),
topic and project rankings, a daily activity calendar, a time-of-week heatmap, energy
equivalents, and a searchable, sortable list of every conversation. It follows the
system light/dark setting, and the Theme button overrides it.

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

To add fields to the dashboard, add them to the records built in `dashboard_generator.py`
(`chat_records` / `code_records`), then render them in `dashboard_template.html`. Charts
are plain SVG/HTML drawn by the template's script, with no charting library.

## Dependencies

No dependencies required for basic usage (standard library only).

Optional (install via `pip install -r requirements.txt`):
- `scikit-learn` - For NLP-based topic clustering (recommended)
- `anthropic` - For LLM-based topic classification
  ```bash
  export ANTHROPIC_API_KEY=your_key
  ```

## Tips

1. **First run**: Use `--clusters 10` (fast, free, no API key)
2. **Better accuracy**: Use `--llm` flag with API key
3. **Large datasets**: Run without `--visualize` first to check stats
4. **Fewer/more topics**: Tune `--clusters N`

## Output Files

- `conversation_data.json` - Processed claude.ai data
- `claude_code_data.json` - Processed Claude Code data
- `dashboard.html` - Combined interactive dashboard (open in browser)

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
- Check the export zips unpack cleanly: `python3 import_export.py`
- Script handles both dict and list formats
- May need to update field names in `extract_date()` and `count_messages()`

## Privacy Note

All analysis is local. The `--llm` flag sends conversation snippets (first 2000 chars) to Claude API for classification only.
