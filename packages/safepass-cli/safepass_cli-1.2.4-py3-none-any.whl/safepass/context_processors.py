"""Context processors for SafePass"""

from safepass import __version__


def version_context(request):
    """Add version to all templates"""
    return {
        'APP_VERSION': __version__
    }
