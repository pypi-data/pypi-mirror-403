#!/usr/bin/env python3
"""
FinOps Report Generator - Deloitte Omnia Data
Generates interactive HTML cost reports for Azure Databricks costs.

Usage:
    python generate_finops_report.py [options]

Options:
    --start-date DATE    Start date (YYYY-MM-DD), default: 30 days ago
    --end-date DATE      End date (YYYY-MM-DD), default: today
    --output PATH        Output file path, default: from config
    --report-type TYPE   Report type: daily, weekly, monthly (default: daily)
    --regions REGIONS    Comma-separated regions: ame,ema,apa (default: ame,ema)
    --open-browser       Open report in browser after generation
    --config PATH        Path to config file (default: finops_config.json)
    --verbose            Enable verbose output

Author: Santosh Dandey
Version: 1.0.0
Last Updated: 2026-01-21
"""

import argparse
import json
import subprocess
import sys
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def load_config(config_path: str) -> dict[str, Any]:
    """Load configuration from JSON file."""
    path = Path(config_path)
    if not path.exists():
        # Try relative to script directory
        script_dir = Path(__file__).parent
        path = script_dir / "finops_config.json"

    if not path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    with open(path) as f:
        return json.load(f)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate FinOps HTML cost report for Azure Databricks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate daily report (last 30 days) and open in browser
    python generate_finops_report.py --open-browser

    # Generate weekly report
    python generate_finops_report.py --report-type weekly --open-browser

    # Custom date range
    python generate_finops_report.py --start-date 2025-12-01 --end-date 2026-01-21

    # Custom output path
    python generate_finops_report.py --output /tmp/cost-report.html
        """
    )

    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date (YYYY-MM-DD), default: today"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output file path"
    )
    parser.add_argument(
        "--report-type",
        type=str,
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="Report type (default: daily)"
    )
    parser.add_argument(
        "--regions",
        type=str,
        default="ame,ema",
        help="Comma-separated regions (default: ame,ema)"
    )
    parser.add_argument(
        "--open-browser",
        action="store_true",
        help="Open report in browser after generation"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="finops_config.json",
        help="Path to config file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    return parser.parse_args()


def calculate_date_range(args: argparse.Namespace, config: dict) -> tuple[str, str]:
    """Calculate start and end dates based on arguments and config."""
    end_date = datetime.now()

    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    else:
        report_config = config.get("report_types", {}).get(args.report_type, {})
        days_lookback = report_config.get("days_lookback", 30)
        start_date = end_date - timedelta(days=days_lookback)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def query_azure_costs(subscription_id: str, start_date: str, end_date: str,
                       azure_cli: str, verbose: bool = False) -> list[list]:
    """Query Azure Cost Management API for Databricks costs."""

    uri = f"https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.CostManagement/query?api-version=2023-03-01"

    body = {
        "type": "ActualCost",
        "timeframe": "Custom",
        "timePeriod": {"from": start_date, "to": end_date},
        "dataset": {
            "granularity": "Daily",
            "aggregation": {"totalCost": {"name": "Cost", "function": "Sum"}},
            "grouping": [
                {"type": "Dimension", "name": "ResourceGroup"},
                {"type": "Dimension", "name": "MeterSubCategory"}
            ],
            "filter": {
                "dimensions": {
                    "name": "ServiceName",
                    "operator": "In",
                    "values": ["Azure Databricks"]
                }
            }
        }
    }

    cmd = [
        azure_cli, "rest",
        "--method", "POST",
        "--uri", uri,
        "--body", json.dumps(body)
    ]

    if verbose:
        print(f"Querying subscription: {subscription_id}")
        print(f"Date range: {start_date} to {end_date}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        response = json.loads(result.stdout)
        rows = response.get("properties", {}).get("rows", [])

        if verbose:
            print(f"Retrieved {len(rows)} cost records")

        return rows

    except subprocess.CalledProcessError as e:
        print(f"Error querying Azure Cost Management API: {e.stderr}")
        return []
    except json.JSONDecodeError as e:
        print(f"Error parsing API response: {e}")
        return []


def process_cost_data(rows: list[list]) -> list[list]:
    """Process raw API rows into the format expected by the HTML template.

    Input format: [cost, billing_period_int, resource_group, meter_subcategory, currency]
    Output format: [cost, date_int, resource_group, meter_subcategory, currency]

    Note: The API returns billing_period as YYYYMMDD integer (e.g., 20260103)
    """
    processed = []
    for row in rows:
        # API returns: [cost, billing_period_int, resource_group, meter_subcategory, currency]
        cost = row[0]
        date_int = row[1]  # Already in YYYYMMDD format
        resource_group = row[2].lower() if len(row) > 2 else ""
        meter_subcategory = row[3] if len(row) > 3 else ""
        currency = row[4] if len(row) > 4 else "USD"

        processed.append([cost, date_int, resource_group, meter_subcategory, currency])

    return processed


def calculate_metrics(ame_data: list[list], ema_data: list[list],
                       start_date: str, end_date: str) -> dict:
    """Calculate summary metrics from cost data."""

    def sum_by_domain(data: list[list], domain_pattern: str) -> float:
        return sum(row[0] for row in data if domain_pattern in row[2])

    ame_dataeng = sum_by_domain(ame_data, "dataeng")
    ame_dataspec = sum_by_domain(ame_data, "dataspec")
    ema_dataeng = sum_by_domain(ema_data, "dataeng")
    ema_dataspec = sum_by_domain(ema_data, "dataspec")

    total_ame = ame_dataeng + ame_dataspec
    total_ema = ema_dataeng + ema_dataspec
    grand_total = total_ame + total_ema

    # Calculate days in range
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    days = (end - start).days + 1

    return {
        "ame_dataeng": ame_dataeng,
        "ame_dataspec": ame_dataspec,
        "ema_dataeng": ema_dataeng,
        "ema_dataspec": ema_dataspec,
        "total_ame": total_ame,
        "total_ema": total_ema,
        "total_dataeng": ame_dataeng + ema_dataeng,
        "total_dataspec": ame_dataspec + ema_dataspec,
        "grand_total": grand_total,
        "daily_average": grand_total / days if days > 0 else 0,
        "days": days
    }


def format_date_range(start_date: str, end_date: str) -> str:
    """Format date range for display."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    days = (end - start).days + 1

    start_fmt = start.strftime("%B %d, %Y")
    end_fmt = end.strftime("%B %d, %Y")

    return f"{start_fmt} - {end_fmt} ({days} Days)"


def generate_html_report(ame_data: list[list], ema_data: list[list],
                          start_date: str, end_date: str,
                          config: dict) -> str:
    """Generate the HTML report with embedded data."""

    date_range_str = format_date_range(start_date, end_date)
    generation_time = datetime.now().strftime("%B %d, %Y at %H:%M:%S")
    metrics = calculate_metrics(ame_data, ema_data, start_date, end_date)

    # Format data arrays for JavaScript
    ame_js = json.dumps(ame_data, indent=4)
    ema_js = json.dumps(ema_data, indent=4)

    # Get subscription IDs from config
    ame_sub_id = config.get("subscriptions", {}).get("ame_prod", {}).get("id", "")
    ema_sub_id = config.get("subscriptions", {}).get("ema_prod", {}).get("id", "")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deloitte Omnia - Azure Databricks Cost Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* Deloitte Omnia White Theme */
        :root {{
            --primary: #007CB0;
            --primary-dark: #005A87;
            --accent: #86BC25;
            --dataeng: #007CB0;
            --dataspec: #8661c5;
            --ame: #107c10;
            --ema: #ff8c00;
            --bg-light: #F8F8F8;
            --white: #ffffff;
            --border: #E0E0E0;
            --border-dark: #D0D0CE;
            --text: #000000;
            --text-light: #53565A;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--white);
            color: var(--text);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.5;
        }}

        .container {{ max-width: 1600px; margin: 0 auto; }}

        header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 24px 20px;
            background: var(--white);
            border-radius: 8px;
            border: 1px solid var(--border);
        }}

        header h1 {{ font-size: 2.2em; margin-bottom: 10px; font-weight: 600; }}
        header h1 .brand {{ color: var(--text); font-weight: 700; }}
        header h1 .brand-accent {{ color: var(--primary); font-weight: 400; }}
        .subtitle {{ color: var(--text-light); font-size: 1.1em; margin: 4px 0; }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .metric-card {{
            background: var(--white);
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            border: 1px solid var(--border);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-3px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }}

        .metric-card.dataeng {{ border-left: 4px solid var(--dataeng); }}
        .metric-card.dataspec {{ border-left: 4px solid var(--dataspec); }}
        .metric-card.ame {{ border-left: 4px solid var(--ame); }}
        .metric-card.ema {{ border-left: 4px solid var(--ema); }}
        .metric-card.total {{ border-left: 4px solid var(--primary); }}

        .metric-value {{ font-size: 1.8em; font-weight: 700; margin: 10px 0; color: var(--text); }}
        .metric-label {{ color: var(--text-light); font-size: 0.85em; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 500; }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}

        @media (max-width: 1200px) {{ .charts-grid {{ grid-template-columns: 1fr; }} }}

        .chart-card {{
            background: var(--white);
            border-radius: 8px;
            padding: 20px;
            border: 1px solid var(--border);
        }}

        .chart-card.full-width {{ grid-column: 1 / -1; }}

        .chart-title {{
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 15px;
            color: var(--text);
            border-bottom: 1px solid var(--border);
            padding-bottom: 10px;
        }}

        .chart-container {{ position: relative; height: 350px; }}
        .chart-container.tall {{ height: 450px; }}

        .data-table-container {{
            background: var(--white);
            border-radius: 8px;
            padding: 20px;
            border: 1px solid var(--border);
            margin-bottom: 30px;
            overflow-x: auto;
        }}

        table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
        th, td {{ padding: 12px 15px; text-align: right; border-bottom: 1px solid var(--border); }}
        th {{
            background: var(--white);
            color: var(--text);
            text-transform: uppercase;
            font-weight: 600;
            font-size: 0.8em;
            letter-spacing: 0.5px;
            border-bottom: 2px solid var(--border-dark);
        }}
        th:first-child, td:first-child {{ text-align: left; }}
        tr:hover {{ background: #f8fbff; }}
        tfoot tr {{ background: var(--bg-light) !important; font-weight: 600; }}
        tfoot td {{ border-top: 2px solid var(--border-dark); }}

        .filter-controls {{ display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }}

        .filter-btn {{
            padding: 10px 20px;
            border: 1px solid var(--border);
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9em;
            font-weight: 500;
            transition: all 0.2s ease;
            background: var(--white);
            color: var(--text-light);
        }}

        .filter-btn:hover {{ background: var(--bg-light); border-color: var(--border-dark); }}
        .filter-btn.active {{ background: var(--primary); color: var(--white); border-color: var(--primary); }}

        footer {{
            text-align: center;
            padding: 20px;
            color: var(--text-light);
            font-size: 0.85em;
            border-top: 1px solid var(--border);
            margin-top: 20px;
        }}
        footer p {{ margin: 4px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1><span class="brand">Deloitte.</span> <span class="brand-accent">Omnia</span></h1>
            <p class="subtitle">Azure Databricks Cost Report | AME PROD & EMA PROD</p>
            <p class="subtitle">{date_range_str}</p>
        </header>

        <div class="metrics-grid" id="metricsGrid"></div>

        <div class="filter-controls">
            <button class="filter-btn active" data-filter="all">All Regions</button>
            <button class="filter-btn" data-filter="ame">AME Only</button>
            <button class="filter-btn" data-filter="ema">EMA Only</button>
        </div>

        <div class="charts-grid">
            <div class="chart-card full-width">
                <h3 class="chart-title">Daily Cost Trend</h3>
                <div class="chart-container tall"><canvas id="dailyTrendChart"></canvas></div>
            </div>
            <div class="chart-card">
                <h3 class="chart-title">Domain Distribution</h3>
                <div class="chart-container"><canvas id="domainChart"></canvas></div>
            </div>
            <div class="chart-card">
                <h3 class="chart-title">Region Distribution</h3>
                <div class="chart-container"><canvas id="regionChart"></canvas></div>
            </div>
            <div class="chart-card">
                <h3 class="chart-title">Region Comparison by Domain</h3>
                <div class="chart-container"><canvas id="regionCompareChart"></canvas></div>
            </div>
            <div class="chart-card">
                <h3 class="chart-title">Stacked Domain by Region</h3>
                <div class="chart-container"><canvas id="stackedChart"></canvas></div>
            </div>
        </div>

        <div class="data-table-container">
            <h3 class="chart-title">Daily Cost Breakdown</h3>
            <table id="dailyTable">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>AME Data Eng</th>
                        <th>AME Specialist</th>
                        <th>EMA Data Eng</th>
                        <th>EMA Specialist</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody></tbody>
                <tfoot></tfoot>
            </table>
        </div>

        <footer>
            <p>Generated on: {generation_time}</p>
            <p>Data Source: Azure Cost Management API</p>
            <p>Subscriptions: AME PROD ({ame_sub_id}) | EMA PROD ({ema_sub_id})</p>
        </footer>
    </div>

    <script>
        // Raw data from Azure Cost Management API
        const ameRawData = {ame_js};

        const emaRawData = {ema_js};

        // Process data
        function processData(rawData, region) {{
            const daily = {{}};
            rawData.forEach(row => {{
                const [cost, dateInt, rg, meter, currency] = row;
                const dateStr = String(dateInt);
                const date = dateStr.slice(0, 4) + '-' + dateStr.slice(4, 6) + '-' + dateStr.slice(6, 8);
                const domain = rg.includes('dataeng') ? 'dataeng' : 'dataspec';

                if (!daily[date]) daily[date] = {{ dataeng: 0, dataspec: 0 }};
                daily[date][domain] += cost;
            }});
            return daily;
        }}

        const ameDaily = processData(ameRawData, 'ame');
        const emaDaily = processData(emaRawData, 'ema');

        // Combine into chart data
        const allDates = [...new Set([...Object.keys(ameDaily), ...Object.keys(emaDaily)])].sort();
        const labels = allDates.map(d => {{
            const dt = new Date(d);
            return dt.toLocaleDateString('en-US', {{ month: 'short', day: 'numeric' }});
        }});

        let ameDataEng = allDates.map(d => ameDaily[d]?.dataeng || 0);
        let ameDataSpec = allDates.map(d => ameDaily[d]?.dataspec || 0);
        let emaDataEng = allDates.map(d => emaDaily[d]?.dataeng || 0);
        let emaDataSpec = allDates.map(d => emaDaily[d]?.dataspec || 0);

        // Totals
        const totalAmeDataEng = ameDataEng.reduce((a, b) => a + b, 0);
        const totalAmeDataSpec = ameDataSpec.reduce((a, b) => a + b, 0);
        const totalEmaDataEng = emaDataEng.reduce((a, b) => a + b, 0);
        const totalEmaDataSpec = emaDataSpec.reduce((a, b) => a + b, 0);
        const totalAme = totalAmeDataEng + totalAmeDataSpec;
        const totalEma = totalEmaDataEng + totalEmaDataSpec;
        const grandTotal = totalAme + totalEma;
        const numDays = {metrics['days']};

        // Populate metrics
        const fmt = n => '$' + n.toLocaleString('en-US', {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
        document.getElementById('metricsGrid').innerHTML = `
            <div class="metric-card total">
                <div class="metric-label">Total Spend (${{numDays}} Days)</div>
                <div class="metric-value">${{fmt(grandTotal)}}</div>
            </div>
            <div class="metric-card dataeng">
                <div class="metric-label">Data Engineering</div>
                <div class="metric-value">${{fmt(totalAmeDataEng + totalEmaDataEng)}}</div>
            </div>
            <div class="metric-card dataspec">
                <div class="metric-label">Specialist Tools</div>
                <div class="metric-value">${{fmt(totalAmeDataSpec + totalEmaDataSpec)}}</div>
            </div>
            <div class="metric-card ame">
                <div class="metric-label">AME Region</div>
                <div class="metric-value">${{fmt(totalAme)}}</div>
            </div>
            <div class="metric-card ema">
                <div class="metric-label">EMA Region</div>
                <div class="metric-value">${{fmt(totalEma)}}</div>
            </div>
        `;

        // Chart options for white theme
        const chartOptions = {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{ labels: {{ color: '#000000' }} }}
            }},
            scales: {{
                x: {{ grid: {{ color: 'rgba(0,0,0,0.08)' }}, ticks: {{ color: '#53565A' }} }},
                y: {{ grid: {{ color: 'rgba(0,0,0,0.08)' }}, ticks: {{ color: '#53565A' }} }}
            }}
        }};

        // Daily trend chart
        const dailyTrendChart = new Chart(document.getElementById('dailyTrendChart'), {{
            type: 'line',
            data: {{
                labels: labels,
                datasets: [
                    {{ label: 'AME Data Eng', data: ameDataEng, borderColor: '#00bcf2', backgroundColor: 'rgba(0,188,242,0.1)', fill: true }},
                    {{ label: 'AME Specialist', data: ameDataSpec, borderColor: '#8661c5', backgroundColor: 'rgba(134,97,197,0.1)', fill: true }},
                    {{ label: 'EMA Data Eng', data: emaDataEng, borderColor: '#00a86b', backgroundColor: 'rgba(0,168,107,0.1)', fill: true }},
                    {{ label: 'EMA Specialist', data: emaDataSpec, borderColor: '#ff6b6b', backgroundColor: 'rgba(255,107,107,0.1)', fill: true }}
                ]
            }},
            options: chartOptions
        }});

        // Domain doughnut
        new Chart(document.getElementById('domainChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['Data Engineering', 'Specialist Tools'],
                datasets: [{{
                    data: [totalAmeDataEng + totalEmaDataEng, totalAmeDataSpec + totalEmaDataSpec],
                    backgroundColor: ['#007CB0', '#8661c5']
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ labels: {{ color: '#000000' }} }} }} }}
        }});

        // Region doughnut
        new Chart(document.getElementById('regionChart'), {{
            type: 'doughnut',
            data: {{
                labels: ['AME', 'EMA'],
                datasets: [{{
                    data: [totalAme, totalEma],
                    backgroundColor: ['#107c10', '#ff8c00']
                }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ labels: {{ color: '#000000' }} }} }} }}
        }});

        // Region comparison bar
        new Chart(document.getElementById('regionCompareChart'), {{
            type: 'bar',
            data: {{
                labels: ['Data Engineering', 'Specialist Tools'],
                datasets: [
                    {{ label: 'AME', data: [totalAmeDataEng, totalAmeDataSpec], backgroundColor: '#107c10' }},
                    {{ label: 'EMA', data: [totalEmaDataEng, totalEmaDataSpec], backgroundColor: '#ff8c00' }}
                ]
            }},
            options: chartOptions
        }});

        // Stacked bar
        new Chart(document.getElementById('stackedChart'), {{
            type: 'bar',
            data: {{
                labels: ['AME', 'EMA'],
                datasets: [
                    {{ label: 'Data Engineering', data: [totalAmeDataEng, totalEmaDataEng], backgroundColor: '#007CB0' }},
                    {{ label: 'Specialist Tools', data: [totalAmeDataSpec, totalEmaDataSpec], backgroundColor: '#8661c5' }}
                ]
            }},
            options: {{ ...chartOptions, scales: {{ ...chartOptions.scales, x: {{ ...chartOptions.scales.x, stacked: true }}, y: {{ ...chartOptions.scales.y, stacked: true }} }} }}
        }});

        // Function to update chart based on filter
        function updateChart(filter) {{
            if (filter === 'ame') {{
                dailyTrendChart.data.datasets = [
                    {{ label: 'AME Data Eng', data: ameDataEng, borderColor: '#00bcf2', backgroundColor: 'rgba(0,188,242,0.1)', fill: true }},
                    {{ label: 'AME Specialist', data: ameDataSpec, borderColor: '#8661c5', backgroundColor: 'rgba(134,97,197,0.1)', fill: true }}
                ];
            }} else if (filter === 'ema') {{
                dailyTrendChart.data.datasets = [
                    {{ label: 'EMA Data Eng', data: emaDataEng, borderColor: '#00a86b', backgroundColor: 'rgba(0,168,107,0.1)', fill: true }},
                    {{ label: 'EMA Specialist', data: emaDataSpec, borderColor: '#ff6b6b', backgroundColor: 'rgba(255,107,107,0.1)', fill: true }}
                ];
            }} else {{
                dailyTrendChart.data.datasets = [
                    {{ label: 'AME Data Eng', data: ameDataEng, borderColor: '#00bcf2', backgroundColor: 'rgba(0,188,242,0.1)', fill: true }},
                    {{ label: 'AME Specialist', data: ameDataSpec, borderColor: '#8661c5', backgroundColor: 'rgba(134,97,197,0.1)', fill: true }},
                    {{ label: 'EMA Data Eng', data: emaDataEng, borderColor: '#00a86b', backgroundColor: 'rgba(0,168,107,0.1)', fill: true }},
                    {{ label: 'EMA Specialist', data: emaDataSpec, borderColor: '#ff6b6b', backgroundColor: 'rgba(255,107,107,0.1)', fill: true }}
                ];
            }}
            dailyTrendChart.update();
        }}

        // Store table data for filtering
        const tableData = allDates.map(date => ({{
            date,
            ameDE: ameDaily[date]?.dataeng || 0,
            ameDS: ameDaily[date]?.dataspec || 0,
            emaDE: emaDaily[date]?.dataeng || 0,
            emaDS: emaDaily[date]?.dataspec || 0
        }}));

        // Function to render table based on filter
        function renderTable(filter) {{
            const tbody = document.querySelector('#dailyTable tbody');
            const tfoot = document.querySelector('#dailyTable tfoot');
            const thead = document.querySelector('#dailyTable thead tr');

            // Update header based on filter
            if (filter === 'ame') {{
                thead.innerHTML = `<th>Date</th><th>AME Data Eng</th><th>AME Specialist</th><th>Total</th><th>% Change</th>`;
            }} else if (filter === 'ema') {{
                thead.innerHTML = `<th>Date</th><th>EMA Data Eng</th><th>EMA Specialist</th><th>Total</th><th>% Change</th>`;
            }} else {{
                thead.innerHTML = `<th>Date</th><th>AME Data Eng</th><th>AME Specialist</th><th>EMA Data Eng</th><th>EMA Specialist</th><th>Total</th><th>% Change</th>`;
            }}

            let totals = {{ ameDE: 0, ameDS: 0, emaDE: 0, emaDS: 0, total: 0 }};
            tbody.innerHTML = '';
            let prevTotal = null;

            tableData.forEach((row, idx) => {{
                let rowTotal;
                let rowHtml;

                // Calculate row total based on filter
                if (filter === 'ame') {{
                    rowTotal = row.ameDE + row.ameDS;
                    totals.ameDE += row.ameDE;
                    totals.ameDS += row.ameDS;
                }} else if (filter === 'ema') {{
                    rowTotal = row.emaDE + row.emaDS;
                    totals.emaDE += row.emaDE;
                    totals.emaDS += row.emaDS;
                }} else {{
                    rowTotal = row.ameDE + row.ameDS + row.emaDE + row.emaDS;
                    totals.ameDE += row.ameDE;
                    totals.ameDS += row.ameDS;
                    totals.emaDE += row.emaDE;
                    totals.emaDS += row.emaDS;
                }}
                totals.total += rowTotal;

                // Calculate percentage change
                let pctCell;
                if (idx === 0 || prevTotal === 0) {{
                    pctCell = '<td style="color:#666">—</td>';
                }} else {{
                    const pctChange = ((rowTotal - prevTotal) / prevTotal) * 100;
                    if (pctChange > 0) {{
                        pctCell = `<td style="color:#107c10">▲ ${{pctChange.toFixed(1)}}%</td>`;
                    }} else if (pctChange < 0) {{
                        pctCell = `<td style="color:#d13438">▼ ${{Math.abs(pctChange).toFixed(1)}}%</td>`;
                    }} else {{
                        pctCell = '<td style="color:#666">0.0%</td>';
                    }}
                }}
                prevTotal = rowTotal;

                // Build row HTML based on filter
                if (filter === 'ame') {{
                    rowHtml = `<tr>
                        <td>${{row.date}}</td>
                        <td>${{fmt(row.ameDE)}}</td>
                        <td>${{fmt(row.ameDS)}}</td>
                        <td>${{fmt(rowTotal)}}</td>
                        ${{pctCell}}
                    </tr>`;
                }} else if (filter === 'ema') {{
                    rowHtml = `<tr>
                        <td>${{row.date}}</td>
                        <td>${{fmt(row.emaDE)}}</td>
                        <td>${{fmt(row.emaDS)}}</td>
                        <td>${{fmt(rowTotal)}}</td>
                        ${{pctCell}}
                    </tr>`;
                }} else {{
                    rowHtml = `<tr>
                        <td>${{row.date}}</td>
                        <td>${{fmt(row.ameDE)}}</td>
                        <td>${{fmt(row.ameDS)}}</td>
                        <td>${{fmt(row.emaDE)}}</td>
                        <td>${{fmt(row.emaDS)}}</td>
                        <td>${{fmt(rowTotal)}}</td>
                        ${{pctCell}}
                    </tr>`;
                }}
                tbody.innerHTML += rowHtml;
            }});

            // Update footer
            if (filter === 'ame') {{
                tfoot.innerHTML = `<tr>
                    <td>TOTAL</td>
                    <td>${{fmt(totals.ameDE)}}</td>
                    <td>${{fmt(totals.ameDS)}}</td>
                    <td>${{fmt(totals.total)}}</td>
                    <td></td>
                </tr>`;
            }} else if (filter === 'ema') {{
                tfoot.innerHTML = `<tr>
                    <td>TOTAL</td>
                    <td>${{fmt(totals.emaDE)}}</td>
                    <td>${{fmt(totals.emaDS)}}</td>
                    <td>${{fmt(totals.total)}}</td>
                    <td></td>
                </tr>`;
            }} else {{
                tfoot.innerHTML = `<tr>
                    <td>TOTAL</td>
                    <td>${{fmt(totals.ameDE)}}</td>
                    <td>${{fmt(totals.ameDS)}}</td>
                    <td>${{fmt(totals.emaDE)}}</td>
                    <td>${{fmt(totals.emaDS)}}</td>
                    <td>${{fmt(totals.total)}}</td>
                    <td></td>
                </tr>`;
            }}
        }}

        // Initial render
        renderTable('all');

        // Filter button click handlers
        document.querySelectorAll('.filter-btn').forEach(btn => {{
            btn.addEventListener('click', () => {{
                document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                const filter = btn.dataset.filter;
                updateChart(filter);
                renderTable(filter);
            }});
        }});
    </script>
</body>
</html>'''

    return html


def main():
    """Main entry point."""
    args = parse_arguments()

    # Load config
    script_dir = Path(__file__).parent
    config_path = args.config if Path(args.config).exists() else script_dir / "finops_config.json"
    config = load_config(str(config_path))

    # Calculate date range
    start_date, end_date = calculate_date_range(args, config)

    # Determine output path
    output_path = args.output or config.get("defaults", {}).get("output_path", "finops-cost-report.html")

    # Get Azure CLI command
    azure_cli = config.get("azure_cli", "az-elevated")

    print("FinOps Report Generator")
    print("=" * 50)
    print(f"Report Type: {args.report_type}")
    print(f"Date Range: {start_date} to {end_date}")
    print(f"Regions: {args.regions}")
    print(f"Output: {output_path}")
    print("=" * 50)

    # Get subscriptions to query
    regions = args.regions.split(",")
    ame_data = []
    ema_data = []

    # Query AME PROD if requested
    if "ame" in regions:
        ame_sub_id = config.get("subscriptions", {}).get("ame_prod", {}).get("id")
        if ame_sub_id:
            print(f"\nQuerying AME PROD ({ame_sub_id})...")
            raw_ame = query_azure_costs(ame_sub_id, start_date, end_date, azure_cli, args.verbose)
            ame_data = process_cost_data(raw_ame)
            print(f"Retrieved {len(ame_data)} AME cost records")

    # Query EMA PROD if requested
    if "ema" in regions:
        ema_sub_id = config.get("subscriptions", {}).get("ema_prod", {}).get("id")
        if ema_sub_id:
            print(f"\nQuerying EMA PROD ({ema_sub_id})...")
            raw_ema = query_azure_costs(ema_sub_id, start_date, end_date, azure_cli, args.verbose)
            ema_data = process_cost_data(raw_ema)
            print(f"Retrieved {len(ema_data)} EMA cost records")

    # Generate HTML report
    print("\nGenerating HTML report...")
    html_content = generate_html_report(ame_data, ema_data, start_date, end_date, config)

    # Write output file
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html_content)
    print(f"Report saved to: {output_path}")

    # Calculate and display summary
    metrics = calculate_metrics(ame_data, ema_data, start_date, end_date)
    print("\n" + "=" * 50)
    print("COST SUMMARY")
    print("=" * 50)
    print(f"Grand Total:       ${metrics['grand_total']:,.2f}")
    print(f"Data Engineering:  ${metrics['total_dataeng']:,.2f}")
    print(f"Specialist Tools:  ${metrics['total_dataspec']:,.2f}")
    print(f"AME Region:        ${metrics['total_ame']:,.2f}")
    print(f"EMA Region:        ${metrics['total_ema']:,.2f}")
    print(f"Daily Average:     ${metrics['daily_average']:,.2f}")
    print("=" * 50)

    # Open in browser if requested
    if args.open_browser:
        print("\nOpening report in browser...")
        webbrowser.open(f"file://{output_file.absolute()}")

    print("\nDone!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
