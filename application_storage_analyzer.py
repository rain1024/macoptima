#!/usr/bin/env python3
"""
Application Storage Analyzer
Analyzes installed applications for installation time, last usage, and storage size.
"""

import argparse
import plistlib
import subprocess
from datetime import datetime
from pathlib import Path


def format_bytes(bytes_size):
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f'{bytes_size:.2f} {unit}'
        bytes_size /= 1024.0
    return f'{bytes_size:.2f} PB'


def get_directory_size(path):
    """Calculate total size of a directory."""
    total = 0
    try:
        for item in path.rglob('*'):
            try:
                if item.is_file():
                    total += item.stat().st_size
            except (OSError, PermissionError):
                continue
    except (OSError, PermissionError):
        pass
    return total


import sys

sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.apps.chrome import ChromeAnalyzer

    HAS_CHROME_ANALYZER = True
except ImportError:
    HAS_CHROME_ANALYZER = False


# Mapping for apps with special folder names
APP_FOLDER_MAPPING = {
    'Docker': {'data': ['Docker'], 'cache': ['com.docker.docker']},
    'Figma': {'data': ['Figma', 'figma-desktop'], 'cache': ['Figma']},
    'Postman': {'data': ['Postman'], 'cache': ['Postman']},
    'Visual Studio Code': {'data': ['Code'], 'cache': ['Code']},
    'Xmind': {'data': ['Xmind'], 'cache': ['Xmind']},
}


def get_app_info_from_plist(app_path):
    """Extract app information from Info.plist."""
    info = {}
    plist_path = app_path / 'Contents' / 'Info.plist'

    try:
        if plist_path.exists():
            with open(plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
                info['bundle_id'] = plist_data.get('CFBundleIdentifier', 'Unknown')
                info['version'] = plist_data.get('CFBundleShortVersionString', 'Unknown')
                info['bundle_name'] = plist_data.get('CFBundleName', app_path.stem)
    except Exception:
        pass

    return info


def get_app_last_opened(app_path):
    """Get last opened date for an application using multiple methods."""
    last_opened = None
    app_name = app_path.stem

    # Method 1: Check kMDItemLastUsedDate metadata
    try:
        cmd = ['mdls', '-name', 'kMDItemLastUsedDate', '-raw', str(app_path)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip() and result.stdout.strip() != '(null)':
            date_str = result.stdout.strip().replace(' +0000', '')
            try:
                last_opened = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
    except Exception:
        pass

    # Method 2: Check Application Support folder modification time
    folders_to_check = []

    if app_name in APP_FOLDER_MAPPING:
        # Use custom mapping
        for folder_name in APP_FOLDER_MAPPING[app_name].get('data', []):
            folders_to_check.append(Path.home() / 'Library/Application Support' / folder_name)
        for folder_name in APP_FOLDER_MAPPING[app_name].get('cache', []):
            folders_to_check.append(Path.home() / 'Library/Caches' / folder_name)
    else:
        # Use default folders
        folders_to_check.append(Path.home() / 'Library/Application Support' / app_name)
        folders_to_check.append(Path.home() / 'Library/Caches' / app_name)

    # Check all folders and find the most recent modification
    for folder in folders_to_check:
        try:
            if folder.exists():
                mtime = folder.stat().st_mtime
                folder_date = datetime.fromtimestamp(mtime)
                if not last_opened or folder_date > last_opened:
                    last_opened = folder_date
        except (OSError, PermissionError):
            pass

    return last_opened


def analyze_application(app_path):
    """Analyze a single application."""
    app_path = Path(app_path)

    if not app_path.exists() or not app_path.is_dir():
        return None

    app_info = {
        'name': app_path.stem,
        'path': str(app_path),
        'size': 0,
        'data_size': 0,
        'cache_size': 0,
        'created': None,
        'modified': None,
        'last_opened': None,
        'bundle_id': 'Unknown',
        'version': 'Unknown',
    }

    try:
        # Get size
        app_info['size'] = get_directory_size(app_path)

        # Get creation and modification time
        stat_info = app_path.stat()
        app_info['created'] = datetime.fromtimestamp(stat_info.st_birthtime)
        app_info['modified'] = datetime.fromtimestamp(stat_info.st_mtime)

        # Get plist info
        plist_info = get_app_info_from_plist(app_path)
        app_info.update(plist_info)

        # Try to get last opened time
        last_opened = get_app_last_opened(app_path)
        if last_opened:
            app_info['last_opened'] = last_opened

        # Get Application Support (data) size
        app_name = app_path.stem

        # Special handling for Google Chrome
        if app_name == 'Google Chrome' and HAS_CHROME_ANALYZER:
            chrome_analysis = ChromeAnalyzer.analyze()
            app_info['data_size'] = chrome_analysis['data_size']
            app_info['cache_size'] = chrome_analysis['cache_size']
            if chrome_analysis['last_used']:
                app_info['last_opened'] = chrome_analysis['last_used']
        # Check if app has special folder mapping
        elif app_name in APP_FOLDER_MAPPING:
            # Use custom mapping for data folders
            for folder_name in APP_FOLDER_MAPPING[app_name].get('data', []):
                data_path = Path.home() / 'Library/Application Support' / folder_name
                if data_path.exists():
                    app_info['data_size'] += get_directory_size(data_path)

            # Use custom mapping for cache folders
            for folder_name in APP_FOLDER_MAPPING[app_name].get('cache', []):
                cache_path = Path.home() / 'Library/Caches' / folder_name
                if cache_path.exists():
                    app_info['cache_size'] += get_directory_size(cache_path)
        else:
            # Use default folder name (app name)
            app_support = Path.home() / 'Library/Application Support' / app_name
            if app_support.exists():
                app_info['data_size'] = get_directory_size(app_support)

            cache_dir = Path.home() / 'Library/Caches' / app_name
            if cache_dir.exists():
                app_info['cache_size'] = get_directory_size(cache_dir)

    except (OSError, PermissionError):
        return None

    return app_info


def analyze_applications_folder(folder_path='/Applications'):
    """Analyze all applications in a folder."""
    folder = Path(folder_path)

    if not folder.exists():
        print(f'Folder not found: {folder_path}')
        return []

    apps = []

    for item in folder.iterdir():
        if item.suffix == '.app':
            print(f'Analyzing: {item.name}')
            app_info = analyze_application(item)
            if app_info and app_info['size'] > 0:
                apps.append(app_info)

    return apps


def print_analysis(apps, sort_by='size', top_n=None):
    """Print application analysis results."""

    if not apps:
        print('No applications found.')
        return

    # Sort applications
    if sort_by == 'size':
        apps.sort(key=lambda x: x['size'], reverse=True)
    elif sort_by == 'created':
        apps.sort(key=lambda x: x['created'] or datetime.min, reverse=True)
    elif sort_by == 'modified':
        apps.sort(key=lambda x: x['modified'] or datetime.min, reverse=True)
    elif sort_by == 'name':
        apps.sort(key=lambda x: x['name'].lower())

    if top_n:
        apps = apps[:top_n]

    print(f'\n{"=" * 100}')
    print(f'Application Analysis ({len(apps)} apps)')
    print(f'{"=" * 100}\n')

    total_size = sum(app['size'] for app in apps)

    # Print header
    print(
        f'{"Application":<30} {"App Size":>11} {"Data":>11} {"Cache":>11} {"Installed":>11} {"Modified":>11} {"Last Used":>11}'
    )
    print(f'{"-" * 120}')

    for app in apps:
        name = app['name'][:28]
        size = format_bytes(app['size'])
        data_size = format_bytes(app['data_size']) if app['data_size'] > 0 else '-'
        cache_size = format_bytes(app['cache_size']) if app['cache_size'] > 0 else '-'
        created = app['created'].strftime('%Y-%m-%d') if app['created'] else 'Unknown'
        modified = app['modified'].strftime('%Y-%m-%d') if app['modified'] else 'Unknown'
        last_used = app['last_opened'].strftime('%Y-%m-%d') if app['last_opened'] else 'Never'

        print(
            f'{name:<30} {size:>11} {data_size:>11} {cache_size:>11} {created:>11} {modified:>11} {last_used:>11}'
        )

    print(f'\n{"=" * 100}')
    print(f'Total Storage Used: {format_bytes(total_size)}')
    print(f'{"=" * 100}\n')


def print_detailed_analysis(apps):
    """Print detailed analysis with statistics."""
    if not apps:
        return

    total_size = sum(app['size'] for app in apps)
    total_data = sum(app['data_size'] for app in apps)
    total_cache = sum(app['cache_size'] for app in apps)
    avg_size = total_size / len(apps)

    # Calculate age statistics
    now = datetime.now()
    old_apps = []  # Not modified in 1+ year
    recent_apps = []  # Modified in last 30 days
    never_used = []  # Never opened
    not_used_recently = []  # Not used in 6+ months

    for app in apps:
        if app['modified']:
            days_since_modified = (now - app['modified']).days
            if days_since_modified > 365:
                old_apps.append(app)
            elif days_since_modified <= 30:
                recent_apps.append(app)

        if app['last_opened'] is None:
            never_used.append(app)
        elif app['last_opened']:
            days_since_used = (now - app['last_opened']).days
            if days_since_used > 180:
                not_used_recently.append(app)

    print('\nStatistics:')
    print(f'  Total Applications:     {len(apps)}')
    print(f'  Total App Size:         {format_bytes(total_size)}')
    print(f'  Total Data Size:        {format_bytes(total_data)}')
    print(f'  Total Cache Size:       {format_bytes(total_cache)}')
    print(f'  Combined Total:         {format_bytes(total_size + total_data + total_cache)}')
    print(f'  Average App Size:       {format_bytes(avg_size)}')
    print(f'  Recently Modified:      {len(recent_apps)} apps (last 30 days)')
    print(f'  Old Applications:       {len(old_apps)} apps (1+ year old)')
    print(f'  Never Used:             {len(never_used)} apps')
    print(f'  Not Used Recently:      {len(not_used_recently)} apps (6+ months)')

    if never_used:
        never_used_size = sum(app['size'] for app in never_used)
        print(f'\n  Never Used Apps ({len(never_used)} apps, {format_bytes(never_used_size)}):')
        never_used.sort(key=lambda x: x['size'], reverse=True)
        for app in never_used:
            print(f'    {app["name"][:50]:<50} {format_bytes(app["size"]):>12}')

    if not_used_recently:
        not_used_size = sum(app['size'] for app in not_used_recently)
        print(
            f'\n  Not Used in 6+ Months ({len(not_used_recently)} apps, {format_bytes(not_used_size)}):'
        )
        not_used_recently.sort(key=lambda x: x['size'], reverse=True)
        for app in not_used_recently:
            days = (now - app['last_opened']).days
            last_used = app['last_opened'].strftime('%Y-%m-%d') if app['last_opened'] else 'Never'
            print(f'    {app["name"][:40]:<40} {format_bytes(app["size"]):>12}  Last: {last_used}')

    if old_apps:
        old_size = sum(app['size'] for app in old_apps)
        print(
            f'\n  Old Applications (Not Modified in 1+ Year - {len(old_apps)} apps, {format_bytes(old_size)}):'
        )
        old_apps.sort(key=lambda x: x['size'], reverse=True)
        for app in old_apps:
            days = (now - app['modified']).days
            print(f'    {app["name"][:50]:<50} {format_bytes(app["size"]):>12}  ({days} days)')


def main():
    parser = argparse.ArgumentParser(
        description='Analyze installed applications for storage and usage'
    )
    parser.add_argument(
        'folder',
        nargs='?',
        default='/Applications',
        help='Path to applications folder (default: /Applications)',
    )
    parser.add_argument(
        '--sort',
        choices=['size', 'created', 'modified', 'name'],
        default='size',
        help='Sort applications by (default: size)',
    )
    parser.add_argument('--top', type=int, help='Show only top N applications')
    parser.add_argument(
        '--detailed',
        action='store_true',
        default=True,
        help='Show detailed statistics (default: True)',
    )
    parser.add_argument(
        '--no-detailed', action='store_false', dest='detailed', help='Hide detailed statistics'
    )
    parser.add_argument('--user', action='store_true', help='Also analyze ~/Applications folder')

    args = parser.parse_args()

    # Analyze main folder
    apps = analyze_applications_folder(args.folder)

    # Also analyze user Applications if requested
    if args.user:
        user_apps_path = Path.home() / 'Applications'
        if user_apps_path.exists():
            print('\nAnalyzing user applications...')
            user_apps = analyze_applications_folder(str(user_apps_path))
            apps.extend(user_apps)

    # Print results
    print_analysis(apps, sort_by=args.sort, top_n=args.top)

    if args.detailed:
        print_detailed_analysis(apps)


if __name__ == '__main__':
    main()
