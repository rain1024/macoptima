#!/usr/bin/env python3
"""
MacOptima Unified Analyzer
Runs all analyzers and generates a comprehensive HTML report.
"""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from application_storage_analyzer import (
    analyze_applications_folder,
    format_bytes,
)
from cache_storage_analyzer import analyze_directory, get_common_cache_locations


def generate_html_report(apps_data, cache_data, output_file='storage_report.html'):
    """Generate comprehensive HTML report of all analysis."""

    # Calculate totals
    total_apps_size = sum(app['size'] for app in apps_data)
    total_data_size = sum(app['data_size'] for app in apps_data)
    total_cache_size = sum(stats['total_size'] for _, stats in cache_data)

    now = datetime.now()

    # Statistics for apps
    never_used_apps = [app for app in apps_data if app['last_opened'] is None]
    not_used_recently = [
        app for app in apps_data if app['last_opened'] and (now - app['last_opened']).days > 180
    ]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MacOptima Storage Report - {now.strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            font-weight: 700;
        }}

        header p {{
            font-size: 1.1rem;
            opacity: 0.9;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}

        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .summary-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 15px rgba(0,0,0,0.15);
        }}

        .summary-card h3 {{
            color: #667eea;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            font-weight: 600;
        }}

        .summary-card .value {{
            font-size: 2rem;
            font-weight: 700;
            color: #2d3748;
        }}

        .summary-card .subtitle {{
            color: #718096;
            font-size: 0.85rem;
            margin-top: 5px;
        }}

        .content {{
            padding: 40px;
        }}

        section {{
            margin-bottom: 50px;
        }}

        h2 {{
            color: #2d3748;
            font-size: 1.8rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #667eea;
        }}

        h3 {{
            color: #4a5568;
            font-size: 1.3rem;
            margin: 30px 0 15px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        thead {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}

        th {{
            padding: 15px;
            text-align: left;
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        th.right {{
            text-align: right;
        }}

        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e2e8f0;
            color: #4a5568;
        }}

        td.right {{
            text-align: right;
        }}

        tbody tr:hover {{
            background: #f7fafc;
        }}

        tbody tr:last-child td {{
            border-bottom: none;
        }}

        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}

        .info {{
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}

        .size-large {{
            color: #dc3545;
            font-weight: 600;
        }}

        .size-medium {{
            color: #ffc107;
            font-weight: 600;
        }}

        .size-small {{
            color: #28a745;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }}

        .badge-danger {{
            background: #fee;
            color: #c00;
        }}

        .badge-warning {{
            background: #fffbea;
            color: #ff8c00;
        }}

        .badge-success {{
            background: #e6f7ed;
            color: #0a7d3a;
        }}

        footer {{
            background: #2d3748;
            color: white;
            padding: 20px;
            text-align: center;
            font-size: 0.9rem;
        }}

        .chart-bar {{
            height: 30px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 4px;
            margin: 5px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>MacOptima Storage Report</h1>
            <p>Generated on {now.strftime('%B %d, %Y at %H:%M:%S')}</p>
        </header>

        <div class="summary">
            <div class="summary-card">
                <h3>Total Apps Analyzed</h3>
                <div class="value">{len(apps_data)}</div>
                <div class="subtitle">Installed applications</div>
            </div>
            <div class="summary-card">
                <h3>Apps Storage</h3>
                <div class="value">{format_bytes(total_apps_size)}</div>
                <div class="subtitle">Application binaries</div>
            </div>
            <div class="summary-card">
                <h3>Data Storage</h3>
                <div class="value">{format_bytes(total_data_size)}</div>
                <div class="subtitle">Application data</div>
            </div>
            <div class="summary-card">
                <h3>Cache Storage</h3>
                <div class="value">{format_bytes(total_cache_size)}</div>
                <div class="subtitle">System-wide caches</div>
            </div>
            <div class="summary-card">
                <h3>Total Storage</h3>
                <div class="value">{format_bytes(total_apps_size + total_data_size + total_cache_size)}</div>
                <div class="subtitle">Combined total</div>
            </div>
            <div class="summary-card">
                <h3>Reclaimable Space</h3>
                <div class="value">{format_bytes(total_cache_size + sum(app['size'] for app in never_used_apps))}</div>
                <div class="subtitle">Potential cleanup</div>
            </div>
        </div>

        <div class="content">
"""

    # Applications section
    html += """
            <section>
                <h2>=� Applications Storage Analysis</h2>
"""

    # Top 20 applications by size
    apps_by_size = sorted(apps_data, key=lambda x: x['size'], reverse=True)[:20]
    html += """
                <h3>Top 20 Largest Applications</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Application</th>
                            <th class="right">App Size</th>
                            <th class="right">Data Size</th>
                            <th class="right">Cache Size</th>
                            <th class="right">Total</th>
                            <th>Last Used</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    for app in apps_by_size:
        total = app['size'] + app['data_size'] + app['cache_size']
        size_class = (
            'size-large' if total > 1024**3 else 'size-medium' if total > 100 * 1024**2 else ''
        )
        last_used = (
            app['last_opened'].strftime('%Y-%m-%d')
            if app['last_opened']
            else '<span class="badge badge-warning">Never</span>'
        )
        html += f"""
                        <tr>
                            <td><strong>{app['name']}</strong></td>
                            <td class="right">{format_bytes(app['size'])}</td>
                            <td class="right">{format_bytes(app['data_size']) if app['data_size'] > 0 else '-'}</td>
                            <td class="right">{format_bytes(app['cache_size']) if app['cache_size'] > 0 else '-'}</td>
                            <td class="right {size_class}">{format_bytes(total)}</td>
                            <td>{last_used}</td>
                        </tr>
"""
    html += """
                    </tbody>
                </table>
"""

    # Never used apps
    if never_used_apps:
        never_used_size = sum(
            app['size'] + app['data_size'] + app['cache_size'] for app in never_used_apps
        )
        html += f"""
                <h3>� Never Used Applications ({len(never_used_apps)} apps, {format_bytes(never_used_size)})</h3>
                <div class="warning">
                    These applications have never been opened. Consider removing them to free up space.
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Application</th>
                            <th class="right">Total Size</th>
                            <th>Installed</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for app in sorted(never_used_apps, key=lambda x: x['size'], reverse=True):
            total = app['size'] + app['data_size'] + app['cache_size']
            installed = app['created'].strftime('%Y-%m-%d') if app['created'] else 'Unknown'
            html += f"""
                        <tr>
                            <td><strong>{app['name']}</strong></td>
                            <td class="right">{format_bytes(total)}</td>
                            <td>{installed}</td>
                        </tr>
"""
        html += """
                    </tbody>
                </table>
"""

    # Not used recently
    if not_used_recently:
        not_used_size = sum(
            app['size'] + app['data_size'] + app['cache_size'] for app in not_used_recently
        )
        html += f"""
                <h3>=� Not Used Recently ({len(not_used_recently)} apps, {format_bytes(not_used_size)})</h3>
                <div class="info">
                    These applications haven't been used in over 6 months.
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Application</th>
                            <th class="right">Total Size</th>
                            <th>Last Used</th>
                            <th>Days Ago</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for app in sorted(not_used_recently, key=lambda x: x['size'], reverse=True)[:20]:
            total = app['size'] + app['data_size'] + app['cache_size']
            last_used = app['last_opened'].strftime('%Y-%m-%d') if app['last_opened'] else 'Never'
            days_ago = (now - app['last_opened']).days if app['last_opened'] else 0
            html += f"""
                        <tr>
                            <td><strong>{app['name']}</strong></td>
                            <td class="right">{format_bytes(total)}</td>
                            <td>{last_used}</td>
                            <td>{days_ago} days</td>
                        </tr>
"""
        html += """
                    </tbody>
                </table>
"""

    html += """
            </section>
"""

    # Cache analysis section
    html += """
            <section>
                <h2>=� Cache Storage Analysis</h2>
"""

    cache_sorted = sorted(cache_data, key=lambda x: x[1]['total_size'], reverse=True)
    html += """
                <h3>Cache Locations</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Location</th>
                            <th class="right">Size</th>
                            <th class="right">Files</th>
                            <th class="right">Folders</th>
                        </tr>
                    </thead>
                    <tbody>
"""
    for path, stats in cache_sorted:
        size_class = (
            'size-large'
            if stats['total_size'] > 1024**3
            else 'size-medium'
            if stats['total_size'] > 100 * 1024**2
            else ''
        )
        html += f"""
                        <tr>
                            <td><code>{path}</code></td>
                            <td class="right {size_class}">{format_bytes(stats['total_size'])}</td>
                            <td class="right">{stats['file_count']:,}</td>
                            <td class="right">{stats['folder_count']:,}</td>
                        </tr>
"""
    html += """
                    </tbody>
                </table>
"""

    # Top subfolders from largest cache location
    if cache_sorted and cache_sorted[0][1].get('subfolders'):
        largest_cache_path, largest_cache_stats = cache_sorted[0]
        html += f"""
                <h3>Top Subfolders in {largest_cache_path}</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Folder</th>
                            <th class="right">Size</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        for subfolder, size in largest_cache_stats['subfolders'][:15]:
            folder_name = Path(subfolder).name
            size_class = (
                'size-large' if size > 1024**3 else 'size-medium' if size > 100 * 1024**2 else ''
            )
            html += f"""
                        <tr>
                            <td><code>{folder_name}</code></td>
                            <td class="right {size_class}">{format_bytes(size)}</td>
                        </tr>
"""
        html += """
                    </tbody>
                </table>
"""

    html += """
            </section>

            <section>
                <h2>=� Recommendations</h2>
                <div class="info">
                    <h3 style="margin-bottom: 10px;">Quick Wins</h3>
                    <ul style="margin-left: 20px; line-height: 1.8;">
"""
    if never_used_apps:
        never_used_size = sum(
            app['size'] + app['data_size'] + app['cache_size'] for app in never_used_apps
        )
        html += f"""
                        <li><strong>Remove {len(never_used_apps)} never-used applications</strong> to free up {format_bytes(never_used_size)}</li>
"""

    if total_cache_size > 1024**3:
        html += f"""
                        <li><strong>Clear cache folders</strong> to reclaim {format_bytes(total_cache_size)}</li>
"""

    if not_used_recently:
        not_used_size = sum(
            app['size'] + app['data_size'] + app['cache_size'] for app in not_used_recently[:10]
        )
        html += f"""
                        <li><strong>Review {len(not_used_recently)} unused applications</strong> (not used in 6+ months)</li>
"""

    html += """
                    </ul>
                </div>
            </section>
        </div>

        <footer>
            <p>Generated by MacOptima - macOS Storage Optimization Toolkit</p>
            <p style="margin-top: 5px; opacity: 0.8;">Report generated at {now.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </footer>
    </div>
</body>
</html>
"""

    # Write to file
    with open(output_file, 'w') as f:
        f.write(html)

    return output_file


def main():
    """Run all analyzers and generate HTML report."""
    print('MacOptima Unified Analyzer')
    print('=' * 70)

    # Analyze applications
    print('\n[1/2] Analyzing applications...')
    apps = analyze_applications_folder('/Applications')

    # Also analyze user Applications
    user_apps_path = Path.home() / 'Applications'
    if user_apps_path.exists():
        print('      Analyzing user applications...')
        user_apps = analyze_applications_folder(str(user_apps_path))
        apps.extend(user_apps)

    print(f'      Found {len(apps)} applications')

    # Analyze caches
    print('\n[2/2] Analyzing cache locations...')
    cache_locations = get_common_cache_locations()
    cache_results = []

    for path in cache_locations:
        stats = analyze_directory(path, recursive=True, show_subfolders=True, top_n=30)
        if stats and stats['total_size'] > 0:
            cache_results.append((path, stats))
            print(f'      {path}: {format_bytes(stats["total_size"])}')

    # Generate HTML report
    print('\n[3/3] Generating HTML report...')
    output_file = generate_html_report(apps, cache_results)

    print(f'\n Report generated: {output_file}')
    print('\nOpen the report in your browser:')
    print(f'   open {output_file}')

    # Summary
    total_apps_size = sum(app['size'] for app in apps)
    total_data_size = sum(app['data_size'] for app in apps)
    total_cache_size = sum(stats['total_size'] for _, stats in cache_results)

    print(f'\n{"=" * 70}')
    print('Summary:')
    print(f'  Applications:   {len(apps)} apps, {format_bytes(total_apps_size)}')
    print(f'  Data:           {format_bytes(total_data_size)}')
    print(f'  Cache:          {format_bytes(total_cache_size)}')
    print(f'  Total:          {format_bytes(total_apps_size + total_data_size + total_cache_size)}')
    print(f'{"=" * 70}\n')


if __name__ == '__main__':
    main()
