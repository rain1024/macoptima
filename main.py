import argparse
import os


def get_size_str(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f'{size_bytes:.2f} {unit}'
        size_bytes /= 1024.0
    return f'{size_bytes:.2f} PB'


def find_large_files(
    directory: str, min_size_mb: float = 100, max_results: int = 50, exclude_dirs: list[str] = None
) -> list[tuple[str, int]]:
    """
    Find large files in a directory and its subdirectories.

    Args:
        directory: Root directory to search
        min_size_mb: Minimum file size in MB
        max_results: Maximum number of results to return
        exclude_dirs: List of directory names to exclude

    Returns:
        List of tuples (file_path, size_in_bytes) sorted by size descending
    """
    if exclude_dirs is None:
        exclude_dirs = ['.git', 'node_modules', '__pycache__', '.venv', 'venv']

    min_size_bytes = min_size_mb * 1024 * 1024
    large_files = []

    print(f'Scanning {directory}...')
    print(f'Looking for files larger than {min_size_mb} MB\n')

    try:
        for root, dirs, files in os.walk(directory):
            # Remove excluded directories from search
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for filename in files:
                try:
                    filepath = os.path.join(root, filename)

                    # Skip symbolic links
                    if os.path.islink(filepath):
                        continue

                    size = os.path.getsize(filepath)

                    if size >= min_size_bytes:
                        large_files.append((filepath, size))

                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue

    except KeyboardInterrupt:
        print('\n\nSearch interrupted by user.')

    # Sort by size (largest first) and limit results
    large_files.sort(key=lambda x: x[1], reverse=True)
    return large_files[:max_results]


def main():
    parser = argparse.ArgumentParser(
        description='Find large files on your computer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Search current directory for files > 100MB
  python main.py /Users                   # Search /Users for files > 100MB
  python main.py ~ --min-size 500         # Search home directory for files > 500MB
  python main.py /var --max-results 100   # Show top 100 largest files
        """,
    )

    parser.add_argument(
        'directory', nargs='?', default='.', help='Directory to search (default: current directory)'
    )
    parser.add_argument(
        '--min-size', type=float, default=100, help='Minimum file size in MB (default: 100)'
    )
    parser.add_argument(
        '--max-results',
        type=int,
        default=50,
        help='Maximum number of results to show (default: 50)',
    )
    parser.add_argument(
        '--exclude', nargs='+', help='Additional directories to exclude from search'
    )

    args = parser.parse_args()

    # Expand user path if needed
    directory = os.path.expanduser(args.directory)

    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist")
        return

    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a directory")
        return

    exclude_dirs = ['.git', 'node_modules', '__pycache__', '.venv', 'venv']
    if args.exclude:
        exclude_dirs.extend(args.exclude)

    large_files = find_large_files(
        directory,
        min_size_mb=args.min_size,
        max_results=args.max_results,
        exclude_dirs=exclude_dirs,
    )

    if not large_files:
        print(f'No files larger than {args.min_size} MB found.')
        return

    print(f'Found {len(large_files)} large files:\n')
    print(f'{"Size":<12} {"Path"}')
    print('-' * 80)

    total_size = 0
    for filepath, size in large_files:
        print(f'{get_size_str(size):<12} {filepath}')
        total_size += size

    print('-' * 80)
    print(f'Total: {get_size_str(total_size)}')


if __name__ == '__main__':
    main()
