#!/usr/bin/env python3
"""
Claude Code Dashboard Generator
Creates interactive HTML visualization for Claude Code usage data.
"""

import json
import os
from datetime import datetime


def format_large_number(value):
    """Format large numbers with M suffix for millions."""
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f} M"
    return f"{value:,}"


def generate_claude_code_dashboard(data_path, output_path='claude_code_dashboard.html'):
    """Generate interactive HTML dashboard for Claude Code usage."""

    with open(data_path, 'r') as f:
        data = json.load(f)

    # Load Chart.js from local file for offline support
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chartjs_path = os.path.join(script_dir, 'chartjs.min.js')
    with open(chartjs_path, 'r') as f:
        chartjs_code = f.read()

    summary = data['summary']
    tokens = summary['tokens']

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Claude Code Usage Dashboard</title>
    <script>{chartjs_code}</script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0f0f23;
            color: #cccccc;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #00cc00;
            border-bottom: 2px solid #00cc00;
            padding-bottom: 10px;
            font-family: 'Source Code Pro', monospace;
        }}
        h2 {{
            color: #cccccc;
            margin-top: 0;
        }}
        .tabs {{
            display: flex;
            gap: 0;
            margin-bottom: 20px;
            border-bottom: 2px solid #333;
        }}
        .tab-btn {{
            padding: 12px 24px;
            border: none;
            background: none;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            color: #666;
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
            transition: all 0.2s;
        }}
        .tab-btn:hover {{
            color: #00cc00;
        }}
        .tab-btn.active {{
            color: #00cc00;
            border-bottom-color: #00cc00;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: #1a1a2e;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #333;
        }}
        .stat-card h3 {{
            margin: 0 0 8px 0;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .stat-card .value {{
            font-size: 28px;
            font-weight: bold;
            color: #00cc00;
            font-family: 'Source Code Pro', monospace;
        }}
        .stat-card .subvalue {{
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }}
        .chart-container {{
            background: #1a1a2e;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            border: 1px solid #333;
        }}
        .chart-wrapper {{
            position: relative;
            height: 350px;
        }}
        .chart-wrapper.tall {{
            height: 450px;
        }}
        .table-container {{
            background: #1a1a2e;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            border: 1px solid #333;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }}
        th {{
            background: #0f0f23;
            font-weight: 600;
            color: #00cc00;
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 1px;
        }}
        tr:hover {{
            background: #252540;
        }}
        .token-bar {{
            display: flex;
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            background: #333;
        }}
        .token-bar .input {{
            background: #3b82f6;
        }}
        .token-bar .output {{
            background: #ef4444;
        }}
        .token-bar .cache {{
            background: #22c55e;
        }}
        .filters {{
            display: flex;
            gap: 16px;
            margin-bottom: 20px;
            flex-wrap: wrap;
            align-items: center;
        }}
        .filter-group {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .filter-group label {{
            font-size: 11px;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
        }}
        .filter-group select, .filter-group input {{
            padding: 8px 12px;
            border: 1px solid #333;
            border-radius: 6px;
            font-size: 14px;
            min-width: 150px;
            background: #0f0f23;
            color: #ccc;
        }}
        .filter-group select:focus, .filter-group input:focus {{
            outline: none;
            border-color: #00cc00;
        }}
        .conv-count {{
            color: #666;
            font-size: 14px;
            margin-left: auto;
        }}
        .conversation-list {{
            background: #1a1a2e;
            border-radius: 8px;
            border: 1px solid #333;
        }}
        .conversation-item {{
            border-bottom: 1px solid #333;
        }}
        .conversation-item:last-child {{
            border-bottom: none;
        }}
        .conversation-header {{
            display: flex;
            align-items: center;
            padding: 16px 20px;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .conversation-header:hover {{
            background: #252540;
        }}
        .expand-icon {{
            width: 16px;
            height: 16px;
            margin-right: 12px;
            transition: transform 0.2s;
            color: #666;
        }}
        .conversation-item.expanded .expand-icon {{
            transform: rotate(90deg);
        }}
        .conversation-title {{
            flex: 1;
            font-weight: 500;
            color: #ccc;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .conversation-meta {{
            display: flex;
            gap: 16px;
            font-size: 13px;
            color: #666;
        }}
        .project-badge {{
            background: #1e3a5f;
            color: #60a5fa;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 500;
        }}
        .model-badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .model-badge.opus {{ background: #7c3aed; color: white; }}
        .model-badge.sonnet {{ background: #0891b2; color: white; }}
        .model-badge.haiku {{ background: #65a30d; color: white; }}
        .model-badge.default {{ background: #666; color: white; }}
        .conversation-details {{
            display: none;
            padding: 0 20px 20px 48px;
            background: #151525;
        }}
        .conversation-item.expanded .conversation-details {{
            display: block;
        }}
        .detail-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 16px;
        }}
        .detail-item {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .detail-item label {{
            font-size: 10px;
            font-weight: 600;
            color: #666;
            text-transform: uppercase;
        }}
        .detail-item span {{
            font-size: 14px;
            color: #ccc;
            font-family: 'Source Code Pro', monospace;
        }}
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        .footer {{
            text-align: center;
            color: #444;
            margin-top: 40px;
            padding: 20px;
            font-size: 12px;
        }}
        .energy-equivalents {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #00cc00;
            margin: 20px 0;
        }}
        .energy-equivalents h2 {{
            color: #00cc00;
            margin: 0 0 8px 0;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .energy-total {{
            font-size: 36px;
            font-weight: bold;
            color: #00cc00;
            font-family: 'Source Code Pro', monospace;
            margin-bottom: 16px;
        }}
        .energy-intro {{
            color: #888;
            font-size: 14px;
            margin-bottom: 16px;
        }}
        .equivalents-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }}
        .equiv-item {{
            background: rgba(0, 204, 0, 0.1);
            padding: 16px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .equiv-icon {{
            font-size: 28px;
            width: 40px;
            text-align: center;
        }}
        .equiv-text {{
            flex: 1;
        }}
        .equiv-value {{
            font-size: 24px;
            font-weight: bold;
            color: #fff;
            font-family: 'Source Code Pro', monospace;
        }}
        .equiv-label {{
            font-size: 12px;
            color: #888;
        }}
        .legend {{
            display: flex;
            gap: 20px;
            margin-top: 10px;
            font-size: 12px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .legend-dot {{
            width: 12px;
            height: 12px;
            border-radius: 2px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>&gt; Claude Code Usage Dashboard</h1>

        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('overview')">Overview</button>
            <button class="tab-btn" onclick="switchTab('projects')">By Project</button>
            <button class="tab-btn" onclick="switchTab('sessions')">Sessions</button>
            <button class="tab-btn" onclick="switchTab('top')">Top Consumers</button>
        </div>

        <!-- Overview Tab -->
        <div id="overview-tab" class="tab-content active">
            <div class="stats">
                <div class="stat-card">
                    <h3>Projects</h3>
                    <div class="value">{summary['total_projects']}</div>
                </div>
                <div class="stat-card">
                    <h3>Sessions</h3>
                    <div class="value">{summary['total_conversations']}</div>
                </div>
                <div class="stat-card">
                    <h3>Total Turns</h3>
                    <div class="value">{format_large_number(summary['total_turns'])}</div>
                </div>
                <div class="stat-card">
                    <h3>Total Tokens</h3>
                    <div class="value">{format_large_number(tokens['total'])}</div>
                </div>
                <div class="stat-card">
                    <h3>Input Tokens</h3>
                    <div class="value">{format_large_number(tokens['input'])}</div>
                    <div class="subvalue">{tokens['input']/tokens['total']*100:.1f}% of total</div>
                </div>
                <div class="stat-card">
                    <h3>Output Tokens</h3>
                    <div class="value">{format_large_number(tokens['output'])}</div>
                    <div class="subvalue">{tokens['output']/tokens['total']*100:.1f}% of total</div>
                </div>
                <div class="stat-card">
                    <h3>Cache Read</h3>
                    <div class="value">{format_large_number(tokens['cache_read'])}</div>
                    <div class="subvalue">Saved tokens from cache</div>
                </div>
                <div class="stat-card">
                    <h3>Est. Energy</h3>
                    <div class="value">{summary['energy_wh']:.1f} Wh</div>
                </div>
                <div class="stat-card">
                    <h3>Est. Token Cost</h3>
                    <div class="value">${summary['cost_estimate']:.2f}</div>
                </div>
            </div>

            <div class="energy-equivalents">
                <h2>Energy Consumption</h2>
                <div class="energy-total">{summary['energy_wh']:.1f} Wh</div>
                <div class="energy-intro">That's as much energy as...</div>
                <div class="equivalents-grid">
                    <div class="equiv-item">
                        <div class="equiv-icon">🚗</div>
                        <div class="equiv-text">
                            <div class="equiv-value">{summary['energy_wh'] / 350:.2f}</div>
                            <div class="equiv-label">miles in a Tesla Model X</div>
                        </div>
                    </div>
                    <div class="equiv-item">
                        <div class="equiv-icon">📱</div>
                        <div class="equiv-text">
                            <div class="equiv-value">{summary['energy_wh'] / 12:.1f}</div>
                            <div class="equiv-label">smartphone charges</div>
                        </div>
                    </div>
                    <div class="equiv-item">
                        <div class="equiv-icon">🌱</div>
                        <div class="equiv-text">
                            <div class="equiv-value">{summary['energy_wh'] / 100:.1f}</div>
                            <div class="equiv-label">hours on a 100W grow light</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="chart-container">
                <h2>Token Distribution by Project</h2>
                <div class="chart-wrapper">
                    <canvas id="projectPieChart"></canvas>
                </div>
            </div>

            <div class="chart-container">
                <h2>Token Types Breakdown</h2>
                <div class="chart-wrapper">
                    <canvas id="tokenTypesChart"></canvas>
                </div>
                <div class="legend">
                    <div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div> Input</div>
                    <div class="legend-item"><div class="legend-dot" style="background:#ef4444"></div> Output</div>
                    <div class="legend-item"><div class="legend-dot" style="background:#22c55e"></div> Cache Read</div>
                    <div class="legend-item"><div class="legend-dot" style="background:#eab308"></div> Cache Creation</div>
                </div>
            </div>

            <div class="chart-container">
                <h2>Energy Consumption by Project (Wh)</h2>
                <div class="chart-wrapper">
                    <canvas id="energyChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Projects Tab -->
        <div id="projects-tab" class="tab-content">
            <div class="table-container">
                <h2>Project Breakdown</h2>
                <table id="projectTable">
                    <thead>
                        <tr>
                            <th>Project</th>
                            <th>Sessions</th>
                            <th>Turns</th>
                            <th>Total Tokens</th>
                            <th>Input</th>
                            <th>Output</th>
                            <th>Cache Read</th>
                            <th>% of Total</th>
                            <th>Energy (Wh)</th>
                            <th>Est. Cost</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>

            <div class="chart-container">
                <h2>Sessions Over Time by Project</h2>
                <div class="chart-wrapper tall">
                    <canvas id="timelineChart"></canvas>
                </div>
            </div>
        </div>

        <!-- Sessions Tab -->
        <div id="sessions-tab" class="tab-content">
            <div class="filters">
                <div class="filter-group">
                    <label>Project</label>
                    <select id="projectFilter">
                        <option value="">All Projects</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>Model</label>
                    <select id="modelFilter">
                        <option value="">All Models</option>
                        <option value="opus">Opus</option>
                        <option value="sonnet">Sonnet</option>
                        <option value="haiku">Haiku</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label>From Date</label>
                    <input type="date" id="dateFromFilter">
                </div>
                <div class="filter-group">
                    <label>To Date</label>
                    <input type="date" id="dateToFilter">
                </div>
                <div class="conv-count" id="sessionCount"></div>
            </div>
            <div class="conversation-list" id="sessionList"></div>
        </div>

        <!-- Top Consumers Tab -->
        <div id="top-tab" class="tab-content">
            <div class="chart-container">
                <h2>Top 20 Token-Consuming Sessions</h2>
                <div class="chart-wrapper tall">
                    <canvas id="topConsumersChart"></canvas>
                </div>
            </div>

            <div class="table-container">
                <h2>Highest Token Usage Sessions</h2>
                <table id="topTable">
                    <thead>
                        <tr>
                            <th>Project</th>
                            <th>Session Title</th>
                            <th>Date</th>
                            <th>Model</th>
                            <th>Total Tokens</th>
                            <th>Input</th>
                            <th>Output</th>
                            <th>Energy (Wh)</th>
                            <th>Cost</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>

        <div class="footer">
            Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Claude Code Usage Analyzer
        </div>
    </div>

    <script>
        const data = {json.dumps(data)};

        // Colors for projects
        const projectColors = [
            '#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6',
            '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
        ];

        // Sort projects by token usage
        const sortedProjects = Object.entries(data.by_project)
            .sort((a, b) => b[1].tokens.total - a[1].tokens.total);
        const projectNames = sortedProjects.map(([name, _]) => name);
        const projectTokens = sortedProjects.map(([_, v]) => v.tokens.total);
        const projectEnergy = sortedProjects.map(([_, v]) => v.energy_wh);

        // Project Pie Chart
        new Chart(document.getElementById('projectPieChart'), {{
            type: 'pie',
            data: {{
                labels: projectNames,
                datasets: [{{
                    data: projectTokens,
                    backgroundColor: projectColors.slice(0, projectNames.length),
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{ color: '#ccc' }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = ((value / total) * 100).toFixed(1);
                                return context.label + ': ' + value.toLocaleString() + ' (' + pct + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Token Types Chart
        new Chart(document.getElementById('tokenTypesChart'), {{
            type: 'bar',
            data: {{
                labels: projectNames,
                datasets: [
                    {{
                        label: 'Input',
                        data: sortedProjects.map(([_, v]) => v.tokens.input),
                        backgroundColor: '#3b82f6'
                    }},
                    {{
                        label: 'Output',
                        data: sortedProjects.map(([_, v]) => v.tokens.output),
                        backgroundColor: '#ef4444'
                    }},
                    {{
                        label: 'Cache Read',
                        data: sortedProjects.map(([_, v]) => v.tokens.cache_read),
                        backgroundColor: '#22c55e'
                    }},
                    {{
                        label: 'Cache Creation',
                        data: sortedProjects.map(([_, v]) => v.tokens.cache_creation),
                        backgroundColor: '#eab308'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        stacked: true,
                        ticks: {{ color: '#666' }},
                        grid: {{ color: '#333' }}
                    }},
                    y: {{
                        stacked: true,
                        ticks: {{
                            color: '#666',
                            callback: v => v.toLocaleString()
                        }},
                        grid: {{ color: '#333' }}
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }}
                }}
            }}
        }});

        // Energy Chart
        new Chart(document.getElementById('energyChart'), {{
            type: 'bar',
            data: {{
                labels: projectNames,
                datasets: [{{
                    label: 'Energy (Wh)',
                    data: projectEnergy,
                    backgroundColor: projectColors.slice(0, projectNames.length)
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        ticks: {{ color: '#666' }},
                        grid: {{ color: '#333' }}
                    }},
                    y: {{
                        ticks: {{
                            color: '#666',
                            callback: v => v.toFixed(1) + ' Wh'
                        }},
                        grid: {{ color: '#333' }}
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: ctx => {{
                                const wh = ctx.parsed.y;
                                return ['Energy: ' + wh.toFixed(2) + ' Wh', 'Phone charges: ' + (wh/12).toFixed(2)];
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // Projects table
        const projectTbody = document.querySelector('#projectTable tbody');
        sortedProjects.forEach(([name, stats]) => {{
            const row = projectTbody.insertRow();
            row.innerHTML = `
                <td><strong>${{name}}</strong></td>
                <td>${{stats.conversation_count}}</td>
                <td>${{stats.total_turns}}</td>
                <td>${{stats.tokens.total.toLocaleString()}}</td>
                <td>${{stats.tokens.input.toLocaleString()}}</td>
                <td>${{stats.tokens.output.toLocaleString()}}</td>
                <td>${{stats.tokens.cache_read.toLocaleString()}}</td>
                <td>${{stats.percentage.toFixed(1)}}%</td>
                <td>${{stats.energy_wh.toFixed(2)}}</td>
                <td>${{stats.cost_estimate.toFixed(2)}}</td>
            `;
        }});

        // Timeline chart - sessions by date per project
        const convsByDate = {{}};
        data.conversations.forEach(conv => {{
            if (conv.date) {{
                if (!convsByDate[conv.date]) convsByDate[conv.date] = {{}};
                convsByDate[conv.date][conv.project] = (convsByDate[conv.date][conv.project] || 0) + 1;
            }}
        }});
        const sortedDates = Object.keys(convsByDate).sort();

        new Chart(document.getElementById('timelineChart'), {{
            type: 'bar',
            data: {{
                labels: sortedDates,
                datasets: projectNames.map((proj, i) => ({{
                    label: proj,
                    data: sortedDates.map(d => convsByDate[d][proj] || 0),
                    backgroundColor: projectColors[i % projectColors.length]
                }}))
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        stacked: true,
                        ticks: {{ color: '#666' }},
                        grid: {{ color: '#333' }}
                    }},
                    y: {{
                        stacked: true,
                        ticks: {{ color: '#666' }},
                        grid: {{ color: '#333' }},
                        title: {{ display: true, text: 'Sessions', color: '#666' }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{ color: '#ccc' }}
                    }}
                }}
            }}
        }});

        // Top consumers chart
        const topData = data.top_consumers.slice(0, 15);
        new Chart(document.getElementById('topConsumersChart'), {{
            type: 'bar',
            data: {{
                labels: topData.map(c => c.title.substring(0, 40) + (c.title.length > 40 ? '...' : '')),
                datasets: [
                    {{
                        label: 'Input',
                        data: topData.map(c => c.input_tokens),
                        backgroundColor: '#3b82f6'
                    }},
                    {{
                        label: 'Output',
                        data: topData.map(c => c.output_tokens),
                        backgroundColor: '#ef4444'
                    }}
                ]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        stacked: true,
                        ticks: {{
                            color: '#666',
                            callback: v => v.toLocaleString()
                        }},
                        grid: {{ color: '#333' }}
                    }},
                    y: {{
                        stacked: true,
                        ticks: {{ color: '#ccc', font: {{ size: 10 }} }},
                        grid: {{ color: '#333' }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{ color: '#ccc' }}
                    }}
                }}
            }}
        }});

        // Top consumers table
        const topTbody = document.querySelector('#topTable tbody');
        data.top_consumers.forEach(conv => {{
            const row = topTbody.insertRow();
            row.innerHTML = `
                <td><span class="project-badge">${{conv.project}}</span></td>
                <td>${{conv.title}}</td>
                <td>${{conv.date || '-'}}</td>
                <td><span class="model-badge ${{conv.model_tier}}">${{conv.model_tier}}</span></td>
                <td>${{conv.total_tokens.toLocaleString()}}</td>
                <td>${{conv.input_tokens.toLocaleString()}}</td>
                <td>${{conv.output_tokens.toLocaleString()}}</td>
                <td>${{conv.energy_wh.toFixed(3)}}</td>
                <td>${{conv.cost_estimate.toFixed(3)}}</td>
            `;
        }});

        // Tab switching
        function switchTab(tabName) {{
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
        }}

        // Sessions tab
        const conversations = data.conversations || [];
        const projectFilter = document.getElementById('projectFilter');
        const modelFilter = document.getElementById('modelFilter');
        const dateFromFilter = document.getElementById('dateFromFilter');
        const dateToFilter = document.getElementById('dateToFilter');
        const sessionList = document.getElementById('sessionList');
        const sessionCount = document.getElementById('sessionCount');

        // Populate project filter
        projectNames.forEach(name => {{
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            projectFilter.appendChild(option);
        }});

        // Set date range
        const convDates = conversations.filter(c => c.date).map(c => c.date).sort();
        if (convDates.length > 0) {{
            dateFromFilter.value = convDates[0];
            dateToFilter.value = convDates[convDates.length - 1];
        }}

        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}

        function renderSessions() {{
            const selectedProject = projectFilter.value;
            const selectedModel = modelFilter.value;
            const fromDate = dateFromFilter.value;
            const toDate = dateToFilter.value;

            const filtered = conversations.filter(conv => {{
                if (selectedProject && conv.project !== selectedProject) return false;
                if (selectedModel && conv.model_tier !== selectedModel) return false;
                if (fromDate && conv.date && conv.date < fromDate) return false;
                if (toDate && conv.date && conv.date > toDate) return false;
                return true;
            }});

            sessionCount.textContent = `Showing ${{filtered.length}} of ${{conversations.length}} sessions`;

            if (filtered.length === 0) {{
                sessionList.innerHTML = '<div class="no-results">No sessions match the selected filters.</div>';
                return;
            }}

            sessionList.innerHTML = filtered.map((conv, idx) => `
                <div class="conversation-item" data-idx="${{idx}}">
                    <div class="conversation-header" onclick="toggleSession(this.parentElement)">
                        <svg class="expand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                        <div class="conversation-title">${{escapeHtml(conv.title)}}</div>
                        <div class="conversation-meta">
                            <span class="project-badge">${{escapeHtml(conv.project)}}</span>
                            <span class="model-badge ${{conv.model_tier}}">${{conv.model_tier}}</span>
                            <span>${{conv.date || 'No date'}}</span>
                            <span>${{conv.tokens.total.toLocaleString()}} tokens</span>
                        </div>
                    </div>
                    <div class="conversation-details">
                        <div class="detail-grid">
                            <div class="detail-item">
                                <label>Turns</label>
                                <span>${{conv.turns}}</span>
                            </div>
                            <div class="detail-item">
                                <label>Total Tokens</label>
                                <span>${{conv.tokens.total.toLocaleString()}}</span>
                            </div>
                            <div class="detail-item">
                                <label>Input Tokens</label>
                                <span>${{conv.tokens.input.toLocaleString()}}</span>
                            </div>
                            <div class="detail-item">
                                <label>Output Tokens</label>
                                <span>${{conv.tokens.output.toLocaleString()}}</span>
                            </div>
                            <div class="detail-item">
                                <label>Cache Read</label>
                                <span>${{conv.tokens.cache_read.toLocaleString()}}</span>
                            </div>
                            <div class="detail-item">
                                <label>Cache Creation</label>
                                <span>${{conv.tokens.cache_creation.toLocaleString()}}</span>
                            </div>
                            <div class="detail-item">
                                <label>Est. Energy</label>
                                <span>${{conv.energy_wh.toFixed(4)}} Wh</span>
                            </div>
                            <div class="detail-item">
                                <label>Est. Cost</label>
                                <span>$${{conv.cost_estimate.toFixed(4)}}</span>
                            </div>
                            <div class="detail-item">
                                <label>Model</label>
                                <span>${{conv.primary_model || conv.model_tier}}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }}

        function toggleSession(item) {{
            item.classList.toggle('expanded');
        }}

        projectFilter.addEventListener('change', renderSessions);
        modelFilter.addEventListener('change', renderSessions);
        dateFromFilter.addEventListener('change', renderSessions);
        dateToFilter.addEventListener('change', renderSessions);

        renderSessions();
    </script>
</body>
</html>"""

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"\nDashboard generated: {output_path}")
    print(f"Open in browser: file://{os.path.abspath(output_path)}")

    return output_path


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python claude_code_dashboard.py <data.json>")
        sys.exit(1)

    generate_claude_code_dashboard(sys.argv[1])
