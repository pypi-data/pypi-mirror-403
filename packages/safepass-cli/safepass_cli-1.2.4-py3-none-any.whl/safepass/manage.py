#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'safepass.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    argv = sys.argv
    if 'runserver' in argv and not any(a for a in argv if a.startswith('runserver') and ':' in a):
        idx = argv.index('runserver')
        # runserver komutundan sonra port yoksa ekle
        if len(argv) == idx + 1 or not argv[idx + 1].isdigit():
            argv.insert(idx + 1, '2025')
    execute_from_command_line(argv)


if __name__ == '__main__':
    main()
