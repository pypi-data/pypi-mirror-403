"""
icalcreate - A CLI tool to create .ics calendar files and Google Calendar links.

This package provides a command-line interface to create iCalendar (.ics) files
with support for event title, location, notes, URL, timezone, duration, and alerts.
It can also generate Google Calendar URLs for easy event sharing.

Usage:
    icalcreate -t "Event Title" --time "2024-12-25 14:00" -d 1h [options]

For full documentation, see README.md or run: icalcreate --help
"""

__version__ = "1.0.0"
__author__ = "Benito Marcote"
__all__ = ["__version__", "__author__"]
