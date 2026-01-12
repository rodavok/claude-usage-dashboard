#!/usr/bin/env python3
"""
Dashboard Generator - Creates interactive HTML visualization
"""

import json
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
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Claude Conversations Dashboard</h1>
        
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
                <div class="value">{len(data['by_topic'])}</div>
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
            <h2>📋 Detailed Topic Breakdown</h2>
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
        
        <div class="footer">
            Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
    
    <script>
        const data = {json.dumps(data)};
        
        // Color palette
        const colors = [
            '#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6',
            '#1abc9c', '#34495e', '#e67e22', '#95a5a6', '#16a085'
        ];
        
        // Prepare topic data
        const topics = Object.keys(data.by_topic);
        const topicCounts = topics.map(t => data.by_topic[t].count);
        const topicMessages = topics.map(t => data.by_topic[t].messages);
        const topicTokens = topics.map(t => data.by_topic[t].estimated_tokens);
        
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
                    backgroundColor: '#3498db',
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
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
                    backgroundColor: '#2ecc71',
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
        
        // Timeline Chart
        const timelineData = data.timeline;
        const dates = timelineData.map(d => d.date);
        
        // Create dataset for each topic
        const timelineDatasets = topics.map((topic, i) => ({{
            label: topic,
            data: timelineData.map(d => d.topics[topic] || 0),
            borderColor: colors[i % colors.length],
            backgroundColor: colors[i % colors.length] + '80',
            fill: false,
        }}));
        
        new Chart(document.getElementById('timelineChart'), {{
            type: 'line',
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
                scales: {{
                    x: {{
                        display: true,
                        title: {{
                            display: true,
                            text: 'Date'
                        }}
                    }},
                    y: {{
                        display: true,
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
    import os
    
    if len(sys.argv) < 2:
        print("Usage: python dashboard_generator.py <data.json>")
        sys.exit(1)
    
    generate_dashboard(sys.argv[1])
