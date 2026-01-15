#!/usr/bin/env python3
"""
Dashboard Generator - Creates interactive HTML visualization
"""

import json
import os
from datetime import datetime


def generate_dashboard(data_path, output_path='dashboard.html'):
    """Generate interactive HTML dashboard"""
    
    with open(data_path, 'r') as f:
        data = json.load(f)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Claude Conversations Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        /* Tab styles */
        .tabs {{
            display: flex;
            gap: 0;
            margin-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .tab-btn {{
            padding: 12px 24px;
            border: none;
            background: none;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            color: #7f8c8d;
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
            transition: all 0.2s;
        }}
        .tab-btn:hover {{
            color: #3498db;
        }}
        .tab-btn.active {{
            color: #3498db;
            border-bottom-color: #3498db;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: #7f8c8d;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .chart-wrapper {{
            position: relative;
            height: 400px;
        }}
        .chart-wrapper.timeline {{
            height: 500px;
        }}
        .table-container {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #2c3e50;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .footer {{
            text-align: center;
            color: #7f8c8d;
            margin-top: 40px;
            padding: 20px;
        }}
        /* Conversations tab styles */
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
            font-size: 12px;
            font-weight: 600;
            color: #7f8c8d;
            text-transform: uppercase;
        }}
        .filter-group select, .filter-group input {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            min-width: 150px;
        }}
        .filter-group select:focus, .filter-group input:focus {{
            outline: none;
            border-color: #3498db;
        }}
        .conversation-count {{
            color: #7f8c8d;
            font-size: 14px;
            margin-left: auto;
        }}
        .conversation-list {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .conversation-item {{
            border-bottom: 1px solid #ecf0f1;
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
            background: #f8f9fa;
        }}
        .expand-icon {{
            width: 20px;
            height: 20px;
            margin-right: 12px;
            transition: transform 0.2s;
            color: #7f8c8d;
        }}
        .conversation-item.expanded .expand-icon {{
            transform: rotate(90deg);
        }}
        .conversation-title {{
            flex: 1;
            font-weight: 500;
            color: #2c3e50;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        .conversation-meta {{
            display: flex;
            gap: 16px;
            font-size: 13px;
            color: #7f8c8d;
        }}
        .conversation-meta span {{
            display: flex;
            align-items: center;
            gap: 4px;
        }}
        .topic-badge {{
            background: #e8f4fd;
            color: #3498db;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 500;
        }}
        .conversation-details {{
            display: none;
            padding: 0 20px 20px 52px;
            background: #fafbfc;
        }}
        .conversation-item.expanded .conversation-details {{
            display: block;
        }}
        .detail-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
        }}
        .detail-item {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .detail-item label {{
            font-size: 11px;
            font-weight: 600;
            color: #95a5a6;
            text-transform: uppercase;
        }}
        .detail-item span {{
            font-size: 14px;
            color: #2c3e50;
        }}
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Claude Conversations Dashboard</h1>

        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('analytics')">Analytics</button>
            <button class="tab-btn" onclick="switchTab('conversations')">Conversations</button>
        </div>

        <div id="analytics-tab" class="tab-content active">
        
        <div class="stats">
            <div class="stat-card">
                <h3>Total Conversations</h3>
                <div class="value">{data['summary']['total_conversations']}</div>
            </div>
            <div class="stat-card">
                <h3>Total Messages</h3>
                <div class="value">{data['summary']['total_messages']}</div>
            </div>
            <div class="stat-card">
                <h3>Avg Messages/Conv</h3>
                <div class="value">{data['summary']['total_messages'] / data['summary']['total_conversations']:.1f}</div>
            </div>
            <div class="stat-card">
                <h3>Topics Covered</h3>
                <div class="value">{len(data['by_topic'])-1}</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>📈 Conversations by Topic</h2>
            <div class="chart-wrapper">
                <canvas id="topicPieChart"></canvas>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>💬 Messages by Topic</h2>
            <div class="chart-wrapper">
                <canvas id="messagesBarChart"></canvas>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>🪙 Estimated Token Usage by Topic</h2>
            <div class="chart-wrapper">
                <canvas id="tokensBarChart"></canvas>
            </div>
        </div>
        
        <div class="chart-container">
            <h2>📅 Timeline: Conversations Over Time</h2>
            <div class="chart-wrapper timeline">
                <canvas id="timelineChart"></canvas>
            </div>
        </div>
        
        <div class="table-container">
            <h2>Detailed Topic Breakdown</h2>
            <table id="topicTable">
                <thead>
                    <tr>
                        <th>Topic</th>
                        <th>Conversations</th>
                        <th>% of Total</th>
                        <th>Messages</th>
                        <th>Avg Messages</th>
                        <th>Size (KB)</th>
                        <th>Est. Tokens</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
        </div>

        <div id="conversations-tab" class="tab-content">
            <div class="filters">
                <div class="filter-group">
                    <label>Topic</label>
                    <select id="topicFilter">
                        <option value="">All Topics</option>
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
                <div class="conversation-count" id="conversationCount"></div>
            </div>
            <div class="conversation-list" id="conversationList"></div>
        </div>

        <div class="footer">
            Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    
    <script>
        const data = {json.dumps(data)};
        
        // Color palette - maximally distinct colors
        const colors = [
            '#2563eb', // blue
            '#dc2626', // red
            '#16a34a', // green
            '#9333ea', // purple
            '#ea580c', // orange
            '#0891b2', // cyan
            '#ca8a04', // yellow
            '#db2777', // pink
            '#4b5563', // gray
            '#84cc16', // lime
            '#6366f1', // indigo
            '#14b8a6', // teal
            '#f97316', // amber
            '#8b5cf6', // violet
            '#06b6d4', // sky
        ];

        // Prepare topic data - sorted by count descending
        const sortedTopics = Object.entries(data.by_topic)
            .sort((a, b) => b[1].count - a[1].count);
        const topics = sortedTopics.map(([t, _]) => t);
        const topicCounts = sortedTopics.map(([_, v]) => v.count);
        const topicMessages = sortedTopics.map(([_, v]) => v.messages);
        const topicTokens = sortedTopics.map(([_, v]) => v.estimated_tokens);
        
        // Pie Chart - Topic Distribution
        new Chart(document.getElementById('topicPieChart'), {{
            type: 'pie',
            data: {{
                labels: topics,
                datasets: [{{
                    data: topicCounts,
                    backgroundColor: colors,
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        position: 'right',
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const pct = ((value / total) * 100).toFixed(1);
                                return label + ': ' + value + ' (' + pct + '%)';
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Bar Chart - Messages by Topic
        new Chart(document.getElementById('messagesBarChart'), {{
            type: 'bar',
            data: {{
                labels: topics,
                datasets: [{{
                    label: 'Total Messages',
                    data: topicMessages,
                    backgroundColor: colors.slice(0, topics.length),
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true
                    }}
                }}
            }}
        }});
        
        // Bar Chart - Tokens by Topic
        new Chart(document.getElementById('tokensBarChart'), {{
            type: 'bar',
            data: {{
                labels: topics,
                datasets: [{{
                    label: 'Estimated Tokens',
                    data: topicTokens,
                    backgroundColor: colors.slice(0, topics.length),
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return value.toLocaleString();
                            }}
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                return 'Tokens: ' + context.parsed.y.toLocaleString();
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // Timeline Chart - Stacked Bar
        const timelineData = data.timeline;
        const dates = timelineData.map(d => d.date);

        // Create dataset for each topic
        const timelineDatasets = topics.map((topic, i) => ({{
            label: topic,
            data: timelineData.map(d => d.topics[topic] || 0),
            backgroundColor: colors[i % colors.length],
        }}));

        new Chart(document.getElementById('timelineChart'), {{
            type: 'bar',
            data: {{
                labels: dates,
                datasets: timelineDatasets
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                interaction: {{
                    mode: 'index',
                    intersect: false,
                }},
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    x: {{
                        display: true,
                        stacked: true,
                        title: {{
                            display: true,
                            text: 'Date'
                        }}
                    }},
                    y: {{
                        display: true,
                        stacked: true,
                        title: {{
                            display: true,
                            text: 'Conversations'
                        }},
                        beginAtZero: true
                    }}
                }}
            }}
        }});
        
        // Populate table
        const tbody = document.querySelector('#topicTable tbody');
        Object.entries(data.by_topic)
            .sort((a, b) => b[1].count - a[1].count)
            .forEach(([topic, stats]) => {{
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td><strong>${{topic}}</strong></td>
                    <td>${{stats.count}}</td>
                    <td>${{stats.percentage.toFixed(1)}}%</td>
                    <td>${{stats.messages}}</td>
                    <td>${{(stats.messages / stats.count).toFixed(1)}}</td>
                    <td>${{(stats.size / 1024).toFixed(1)}}</td>
                    <td>${{stats.estimated_tokens.toLocaleString()}}</td>
                `;
            }});

        // Tab switching
        function switchTab(tabName) {{
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tabName + '-tab').classList.add('active');
            // Mark the clicked button as active
            event.target.classList.add('active');
        }}

        // Conversations tab functionality
        const conversations = data.conversations || [];
        const topicFilter = document.getElementById('topicFilter');
        const dateFromFilter = document.getElementById('dateFromFilter');
        const dateToFilter = document.getElementById('dateToFilter');
        const conversationList = document.getElementById('conversationList');
        const conversationCount = document.getElementById('conversationCount');

        // Populate topic filter
        topics.forEach(topic => {{
            const option = document.createElement('option');
            option.value = topic;
            option.textContent = topic;
            topicFilter.appendChild(option);
        }});

        // Set date range from data
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

        function renderConversations() {{
            const selectedTopic = topicFilter.value;
            const fromDate = dateFromFilter.value;
            const toDate = dateToFilter.value;

            const filtered = conversations.filter(conv => {{
                if (selectedTopic && conv.topic !== selectedTopic) return false;
                if (fromDate && conv.date && conv.date < fromDate) return false;
                if (toDate && conv.date && conv.date > toDate) return false;
                return true;
            }});

            conversationCount.textContent = `Showing ${{filtered.length}} of ${{conversations.length}} conversations`;

            if (filtered.length === 0) {{
                conversationList.innerHTML = '<div class="no-results">No conversations match the selected filters.</div>';
                return;
            }}

            conversationList.innerHTML = filtered.map((conv, idx) => `
                <div class="conversation-item" data-idx="${{idx}}">
                    <div class="conversation-header" onclick="toggleConversation(this.parentElement)">
                        <svg class="expand-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="9 18 15 12 9 6"></polyline>
                        </svg>
                        <div class="conversation-title">${{escapeHtml(conv.title)}}</div>
                        <div class="conversation-meta">
                            <span class="topic-badge">${{escapeHtml(conv.topic)}}</span>
                            <span>${{conv.date || 'No date'}}</span>
                        </div>
                    </div>
                    <div class="conversation-details">
                        <div class="detail-grid">
                            <div class="detail-item">
                                <label>Messages</label>
                                <span>${{conv.messages}}</span>
                            </div>
                            <div class="detail-item">
                                <label>Size</label>
                                <span>${{(conv.size / 1024).toFixed(1)}} KB</span>
                            </div>
                            <div class="detail-item">
                                <label>Est. Tokens</label>
                                <span>${{conv.estimated_tokens.toLocaleString()}}</span>
                            </div>
                            <div class="detail-item">
                                <label>Topic</label>
                                <span>${{escapeHtml(conv.topic)}}</span>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }}

        function toggleConversation(item) {{
            item.classList.toggle('expanded');
        }}

        // Event listeners
        topicFilter.addEventListener('change', renderConversations);
        dateFromFilter.addEventListener('change', renderConversations);
        dateToFilter.addEventListener('change', renderConversations);

        // Initial render
        renderConversations();
    </script>
</body>
</html>"""
    
    with open(output_path, 'w') as f:
        f.write(html)
    
    print(f"\n✅ Dashboard generated: {output_path}")
    print(f"   Open in browser: file://{os.path.abspath(output_path)}")
    
    return output_path


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python dashboard_generator.py <data.json>")
        sys.exit(1)
    
    generate_dashboard(sys.argv[1])
