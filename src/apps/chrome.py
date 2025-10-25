"""
Google Chrome specific analyzer.
Handles Chrome's special data and cache folder structure.
"""

from datetime import datetime
from pathlib import Path


class ChromeAnalyzer:
    """Analyzer for Google Chrome application."""

    @staticmethod
    def get_data_folders():
        """Get list of Chrome data folder paths relative to Application Support."""
        return ['Google/Chrome']

    @staticmethod
    def get_cache_folders():
        """Get list of Chrome cache folder paths relative to Caches."""
        return [
            'Google',
            'com.google.GoogleUpdater',
            'com.google.Keystone',
            'com.google.SoftwareUpdate',
        ]

    @staticmethod
    def get_folder_size(path):
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

    @classmethod
    def analyze_data_size(cls):
        """Analyze Chrome's data size in Application Support."""
        total_size = 0
        for folder_name in cls.get_data_folders():
            folder_path = Path.home() / 'Library/Application Support' / folder_name
            if folder_path.exists():
                total_size += cls.get_folder_size(folder_path)
        return total_size

    @classmethod
    def analyze_cache_size(cls):
        """Analyze Chrome's cache size."""
        total_size = 0
        for folder_name in cls.get_cache_folders():
            folder_path = Path.home() / 'Library/Caches' / folder_name
            if folder_path.exists():
                total_size += cls.get_folder_size(folder_path)
        return total_size

    @classmethod
    def get_last_used(cls):
        """Get Chrome's last used date by checking folder modification times."""
        last_used = None

        # Check Application Support folders
        for folder_name in cls.get_data_folders():
            folder_path = Path.home() / 'Library/Application Support' / folder_name
            if folder_path.exists():
                try:
                    mtime = folder_path.stat().st_mtime
                    folder_date = datetime.fromtimestamp(mtime)
                    if not last_used or folder_date > last_used:
                        last_used = folder_date
                except (OSError, PermissionError):
                    pass

        # Check Cache folders
        for folder_name in cls.get_cache_folders():
            folder_path = Path.home() / 'Library/Caches' / folder_name
            if folder_path.exists():
                try:
                    mtime = folder_path.stat().st_mtime
                    folder_date = datetime.fromtimestamp(mtime)
                    if not last_used or folder_date > last_used:
                        last_used = folder_date
                except (OSError, PermissionError):
                    pass

        return last_used

    @classmethod
    def get_profile_info(cls):
        """Get Chrome profile information and sizes."""
        chrome_data = Path.home() / 'Library/Application Support/Google/Chrome'

        if not chrome_data.exists():
            return []

        profiles = []

        # Find all profile directories
        for item in chrome_data.iterdir():
            if item.is_dir() and (item.name.startswith('Profile') or item.name == 'Default'):
                profile_size = cls.get_folder_size(item)

                # Try to get profile name from Preferences
                prefs_file = item / 'Preferences'
                profile_name = item.name

                if prefs_file.exists():
                    try:
                        import json

                        with open(prefs_file) as f:
                            prefs = json.load(f)
                            if 'profile' in prefs and 'name' in prefs['profile']:
                                profile_name = prefs['profile']['name']
                    except (OSError, PermissionError, json.JSONDecodeError, KeyError):
                        pass

                profiles.append(
                    {
                        'name': profile_name,
                        'folder': item.name,
                        'size': profile_size,
                        'path': str(item),
                    }
                )

        # Sort by size
        profiles.sort(key=lambda x: x['size'], reverse=True)
        return profiles

    @classmethod
    def analyze(cls):
        """Full analysis of Chrome installation."""
        return {
            'data_size': cls.analyze_data_size(),
            'cache_size': cls.analyze_cache_size(),
            'last_used': cls.get_last_used(),
            'profiles': cls.get_profile_info(),
        }
