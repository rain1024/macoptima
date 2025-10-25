#!/usr/bin/env python3
"""
Cache Storage Analyzer
Analyzes cache folders to identify size, file count, and age statistics.
"""

import argparse
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def format_bytes(bytes_size):
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f'{bytes_size:.2f} {unit}'
        bytes_size /= 1024.0
    return f'{bytes_size:.2f} PB'


def get_file_age_days(filepath):
    """Get file age in days."""
    try:
        mtime = os.path.getmtime(filepath)
        age = datetime.now().timestamp() - mtime
        return age / (60 * 60 * 24)  # Convert to days
    except OSError:
        return 0


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


def analyze_directory(path, recursive=True, show_subfolders=False, top_n=30):
    """Analyze a directory and return statistics."""
    path = Path(path).expanduser()

    if not path.exists():
        return None

    stats = {
        'total_size': 0,
        'file_count': 0,
        'folder_count': 0,
        'oldest_file': None,
        'newest_file': None,
        'largest_file': None,
        'file_types': defaultdict(lambda: {'count': 0, 'size': 0}),
        'age_distribution': {
            '0-7 days': 0,
            '7-30 days': 0,
            '30-90 days': 0,
            '90-365 days': 0,
            '1+ years': 0,
        },
        'subfolders': [],
    }

    oldest_time = datetime.now().timestamp()
    newest_time = 0
    largest_size = 0

    try:
        if recursive:
            iterator = path.rglob('*')
        else:
            iterator = path.glob('*')

        for item in iterator:
            try:
                if item.is_file():
                    stats['file_count'] += 1
                    size = item.stat().st_size
                    stats['total_size'] += size
                    mtime = item.stat().st_mtime

                    # Track oldest file
                    if mtime < oldest_time:
                        oldest_time = mtime
                        stats['oldest_file'] = (str(item), mtime)

                    # Track newest file
                    if mtime > newest_time:
                        newest_time = mtime
                        stats['newest_file'] = (str(item), mtime)

                    # Track largest file
                    if size > largest_size:
                        largest_size = size
                        stats['largest_file'] = (str(item), size)

                    # File type statistics
                    ext = item.suffix.lower() if item.suffix else '(no extension)'
                    stats['file_types'][ext]['count'] += 1
                    stats['file_types'][ext]['size'] += size

                    # Age distribution
                    age_days = get_file_age_days(item)
                    if age_days <= 7:
                        stats['age_distribution']['0-7 days'] += 1
                    elif age_days <= 30:
                        stats['age_distribution']['7-30 days'] += 1
                    elif age_days <= 90:
                        stats['age_distribution']['30-90 days'] += 1
                    elif age_days <= 365:
                        stats['age_distribution']['90-365 days'] += 1
                    else:
                        stats['age_distribution']['1+ years'] += 1

                elif item.is_dir():
                    stats['folder_count'] += 1

            except (OSError, PermissionError):
                continue

    except (OSError, PermissionError) as e:
        print(f'Error accessing {path}: {e}')
        return None

    # Analyze immediate subfolders if requested
    if show_subfolders:
        subfolder_sizes = {}
        try:
            for item in path.iterdir():
                if item.is_dir():
                    try:
                        size = get_directory_size(item)
                        if size > 0:
                            subfolder_sizes[str(item)] = size
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass

        # Sort and get top N
        sorted_subfolders = sorted(subfolder_sizes.items(), key=lambda x: x[1], reverse=True)[
            :top_n
        ]
        stats['subfolders'] = sorted_subfolders

    return stats


def print_stats(path, stats):
    """Print formatted statistics."""
    if stats is None:
        print(f' Could not analyze: {path}')
        return

    print(f'\n{"=" * 70}')
    print(f'Cache Folder: {path}')
    print(f'{"=" * 70}')

    print('\nOverall Statistics:')
    print(f'  Total Size:      {format_bytes(stats["total_size"])}')
    print(f'  Files:           {stats["file_count"]:,}')
    print(f'  Folders:         {stats["folder_count"]:,}')

    if stats['oldest_file']:
        oldest_date = datetime.fromtimestamp(stats['oldest_file'][1]).strftime('%Y-%m-%d %H:%M:%S')
        print(f'  Oldest File:     {oldest_date}')

    if stats['newest_file']:
        newest_date = datetime.fromtimestamp(stats['newest_file'][1]).strftime('%Y-%m-%d %H:%M:%S')
        print(f'  Newest File:     {newest_date}')

    if stats['largest_file']:
        print(f'  Largest File:    {format_bytes(stats["largest_file"][1])}')
        print(f'                   {Path(stats["largest_file"][0]).name}')

    print('\nAge Distribution:')
    for age_range, count in stats['age_distribution'].items():
        if count > 0:
            print(f'  {age_range:15} {count:,} files')

    if stats['file_types']:
        print('\nTop File Types by Size:')
        sorted_types = sorted(
            stats['file_types'].items(), key=lambda x: x[1]['size'], reverse=True
        )[:10]

        for ext, data in sorted_types:
            print(f'  {ext:20} {data["count"]:6,} files  {format_bytes(data["size"]):>12}')

    if stats['subfolders']:
        print(f'\nTop {len(stats["subfolders"])} Largest Subfolders:')
        for subfolder, size in stats['subfolders']:
            folder_name = Path(subfolder).name
            print(f'  {format_bytes(size):>12}  {folder_name}')


def get_common_cache_locations():
    """Return common cache folder locations for macOS."""
    home = Path.home()
    return [
        home / 'Library/Caches',
        home / '.cache',
        '/Library/Caches',
        '/System/Library/Caches',
        '/private/var/folders',
        home / 'Library/Application Support',
    ]


def main():
    parser = argparse.ArgumentParser(description='Analyze cache folders to identify storage usage')
    parser.add_argument(
        'paths', nargs='*', help='Paths to analyze (defaults to common cache locations)'
    )
    parser.add_argument(
        '--no-recursive', action='store_true', help='Do not recurse into subdirectories'
    )
    parser.add_argument('--common', action='store_true', help='Analyze common cache locations')
    parser.add_argument(
        '--show-subfolders',
        action='store_true',
        help='Show top 30 largest subfolders in each cache folder',
    )
    parser.add_argument(
        '--top-n', type=int, default=30, help='Number of top subfolders to display (default: 30)'
    )

    args = parser.parse_args()

    paths_to_analyze = []

    if args.common or not args.paths:
        paths_to_analyze.extend(get_common_cache_locations())

    if args.paths:
        paths_to_analyze.extend([Path(p) for p in args.paths])

    if not paths_to_analyze:
        print('No paths to analyze. Use --common or specify paths.')
        return

    print(f'Analyzing {len(paths_to_analyze)} cache location(s)...')

    total_size = 0
    results = []

    for path in paths_to_analyze:
        stats = analyze_directory(
            path,
            recursive=not args.no_recursive,
            show_subfolders=args.show_subfolders,
            top_n=args.top_n,
        )
        if stats and stats['total_size'] > 0:
            results.append((path, stats))
            total_size += stats['total_size']

    # Sort by size (largest first)
    results.sort(key=lambda x: x[1]['total_size'], reverse=True)

    for path, stats in results:
        print_stats(path, stats)

    if results:
        print(f'\n{"=" * 70}')
        print(f'Total Cache Size: {format_bytes(total_size)}')
        print(f'{"=" * 70}')


if __name__ == '__main__':
    main()
