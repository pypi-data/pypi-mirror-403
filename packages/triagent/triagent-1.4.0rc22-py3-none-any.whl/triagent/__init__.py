"""Triagent - Claude-powered CLI for Azure DevOps automation."""

try:
    # First try the generated _version.py from hatch-vcs
    from triagent._version import __version__
except ImportError:
    # Fallback for editable installs or when _version.py doesn't exist
    try:
        from importlib.metadata import version

        __version__ = version("triagent")
    except Exception:
        # During build or when not installed as package
        __version__ = "0.0.0+unknown"

__author__ = "Santosh Dandey"
