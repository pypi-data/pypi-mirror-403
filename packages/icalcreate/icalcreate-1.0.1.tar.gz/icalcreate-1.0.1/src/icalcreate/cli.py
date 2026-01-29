"""
CLI module for icalcreate - A command-line tool to create iCalendar (.ics) files.

This module provides functionality to:
- Parse datetime strings and duration formats
- Create iCalendar events with optional location, notes, URL, and alerts
- Generate Google Calendar URLs for easy event sharing
"""

import argparse
import sys
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urlencode
import uuid
from icalendar import Calendar, Event, Alarm
import pytz
from rich_argparse import RichHelpFormatter
from rich import print as rprint


def parse_datetime(dt_string: str, timezone: str) -> datetime:
    """
    Parse a datetime string into a timezone-aware datetime object.

    Args:
        dt_string: Datetime string in formats like "YYYY-MM-DD HH:MM", "YYYY-MM-DDTHH:MM",
                   "DD/MM/YYYY HH:MM", or "MM/DD/YYYY HH:MM".
        timezone: IANA timezone name (e.g., "UTC", "America/New_York", "Europe/London").

    Returns:
        A timezone-aware datetime object.

    Raises:
        ValueError: If the datetime string cannot be parsed in any supported format.
    """
    formats = ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
               "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M"]
    tz = pytz.timezone(timezone)
    for fmt in formats:
        try:
            return tz.localize(datetime.strptime(dt_string, fmt))
        except ValueError:
            continue

    raise ValueError(f"Unable to parse datetime '{dt_string}'. Use format: YYYY-MM-DD HH:MM")


def parse_duration(duration_string: str) -> timedelta:
    """
    Parse a duration string into a timedelta object.

    Supports formats like "1h", "30m", "1h30m", "2d", or plain minutes "90".

    Args:
        duration_string: Duration string with optional d/h/m suffixes.

    Returns:
        A timedelta object representing the duration.

    Raises:
        ValueError: If the duration string cannot be parsed or results in zero duration.
    """
    duration_string = duration_string.strip().lower()
    total_minutes, current_num = 0, ""
    for char in duration_string:
        if char.isdigit():
            current_num += char
        elif char == 'h' and current_num:
            total_minutes += int(current_num) * 60
            current_num = ""
        elif char == 'm' and current_num:
            total_minutes += int(current_num)
            current_num = ""
        elif char == 'd' and current_num:
            total_minutes += int(current_num) * 60 * 24
            current_num = ""

    if current_num:
        total_minutes += int(current_num)

    if total_minutes == 0:
        raise ValueError(f"Unable to parse duration '{duration_string}'. Use format: 1h30m, 90m, 2h, etc.")

    return timedelta(minutes=total_minutes)


def parse_alert(alert_string: str) -> timedelta:
    """
    Parse an alert time string into a timedelta representing time before event.

    Args:
        alert_string: Alert time string (e.g., "15m", "1h", "1d").

    Returns:
        A timedelta object representing how long before the event to trigger the alert.
    """
    return parse_duration(alert_string)


def create_ics_event(title: str, start_time: datetime, duration: timedelta, location: Optional[str] = None,
                     notes: Optional[str] = None, url: Optional[str] = None,
                     alerts: Optional[List[timedelta]] = None) -> Calendar:
    """
    Create an iCalendar event and return it as a Calendar object.

    Args:
        title: Event title/summary.
        start_time: Timezone-aware start datetime.
        duration: Event duration as timedelta.
        location: Optional event location.
        notes: Optional event description/notes.
        url: Optional URL associated with the event.
        alerts: Optional list of timedeltas for reminder alerts before the event.

    Returns:
        A Calendar object containing the event, ready to be serialized to .ics format.
    """
    cal = Calendar()
    cal.add('prodid', '-//icalcreate//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')
    cal.add('method', 'PUBLISH')
    event = Event()
    event.add('summary', title)
    event.add('dtstart', start_time)
    event.add('dtend', start_time + duration)
    event.add('dtstamp', datetime.now(pytz.UTC))
    event.add('uid', str(uuid.uuid4()) + '@icalcreate')
    if location:
        event.add('location', location)

    if notes:
        event.add('description', notes)

    if url:
        event.add('url', url)

    if alerts:
        for alert_time in alerts:
            alarm = Alarm()
            alarm.add('action', 'DISPLAY')
            alarm.add('description', f'Reminder: {title}')
            alarm.add('trigger', -alert_time)
            event.add_component(alarm)

    cal.add_component(event)
    return cal


def generate_google_calendar_url(title: str, start_time: datetime, duration: timedelta,
                                  location: Optional[str] = None, notes: Optional[str] = None) -> str:
    """
    Generate a Google Calendar URL for creating an event.

    Args:
        title: Event title.
        start_time: Timezone-aware start datetime.
        duration: Event duration as timedelta.
        location: Optional event location.
        notes: Optional event description.

    Returns:
        A URL string that opens Google Calendar with the event pre-filled.
    """
    end_time = start_time + duration
    date_format = "%Y%m%dT%H%M%S"
    start_str, end_str = start_time.strftime(date_format), end_time.strftime(date_format)
    tz_name = start_time.tzinfo.zone if start_time.tzinfo and hasattr(start_time.tzinfo, 'zone') else "UTC"  # type: ignore
    params = {'action': 'TEMPLATE', 'text': title, 'dates': f"{start_str}/{end_str}", 'ctz': tz_name}
    if location:
        params['location'] = location

    if notes:
        params['details'] = notes

    return f"https://calendar.google.com/calendar/render?{urlencode(params)}"


def main() -> None:
    """
    Main entry point for the icalcreate CLI.

    Parses command-line arguments, validates input, creates the calendar event,
    and optionally generates a Google Calendar URL.
    """
    parser = argparse.ArgumentParser(
        prog='icalcreate', description='Create .ics calendar files and Google Calendar links',
        formatter_class=RichHelpFormatter,
        epilog="""[bold cyan]Examples:[/bold cyan]
  icalcreate -t "Meeting" --time "2024-12-25 14:00" -d 1h
  icalcreate -t "Conference" --time "2024-12-25 09:00" -d 2h30m -l "Room 101" -o event.ics
  icalcreate -t "Call" --time "2024-12-25 10:00" -d 30m --alert 15m --alert 5m
  icalcreate -t "Webinar" --time "2024-12-25 15:00" -d 1h --google""")
    parser.add_argument('-t', '--title', required=True, help='Event title (required)')
    parser.add_argument('--time', required=True, help='Start time (e.g., "2024-12-25 14:00" or "2024-12-25T14:00")')
    parser.add_argument('-d', '--duration', required=True, help='Duration (e.g., "1h", "30m", "1h30m", "90")')
    parser.add_argument('-l', '--location', help='Event location')
    parser.add_argument('-n', '--notes', help='Event notes/description')
    parser.add_argument('-u', '--url', help='Event URL')
    parser.add_argument('-z', '--timezone', default='UTC',
            help='Time zone (e.g., "America/New_York"). Default: UTC')
    parser.add_argument('-a', '--alert', action='append', dest='alerts', metavar='TIME',
                        help='Alert before event (e.g., "15m", "1h", "1d"). Can be specified multiple times.')
    parser.add_argument('-o', '--output', help='Output .ics file name (default: <title>.ics)')
    parser.add_argument('--google', action='store_true', help='Generate and print Google Calendar URL')
    parser.add_argument('-s', '--silent', action='store_true', default=False,
                        help='To supress the summary in the console at the end.')
    args = parser.parse_args()

    try:
        pytz.timezone(args.timezone)
        start_time = parse_datetime(args.time, args.timezone)
        duration = parse_duration(args.duration)
    except pytz.UnknownTimeZoneError:
        rprint(f"[bold red]Error: Unknown timezone '{args.timezone}'[/bold red]", file=sys.stderr)
        rprint("[red]Use standard timezone names like 'America/New_York', 'Europe/London', 'UTC'[red]",
               file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        rprint(f"[bold red]Error: {e}[/bold red]", file=sys.stderr)
        sys.exit(1)

    alerts: List[timedelta] = []
    if args.alerts:
        for alert_str in args.alerts:
            try:
                alerts.append(parse_alert(alert_str))
            except ValueError as e:
                rprint(f"[bold red]Error parsing alert: {e}[/bold red]", file=sys.stderr)
                sys.exit(1)

    if args.google:
        google_url = generate_google_calendar_url(args.title, start_time, duration, args.location, args.notes)
        rprint(f"\n[bold]Google Calendar URL:[/bold]\n{google_url}\n")

    cal = create_ics_event(args.title, start_time, duration, args.location, args.notes, args.url, alerts)

    if args.output:
        output_file = args.output
    else:
        safe_title = "".join(c if c.isalnum() or c in ' -_' else '_' for c in args.title).replace(' ', '_')
        output_file = f"{safe_title}.ics"
    if not output_file.endswith('.ics'):
        output_file += '.ics'

    with open(output_file, 'wb') as f:
        f.write(cal.to_ical())

    if not args.silent:
        rprint(f"[bold]Calendar event created:[/bold] {output_file}")
        rprint(f"[bold]  Title:[/bold] {args.title}")
        rprint(f"[bold]  Start:[/bold] {start_time.strftime('%Y-%m-%d %H:%M %Z')}")
        rprint(f"[bold]  Duration:[/bold] {args.duration}")
        if args.location:
            rprint(f"[bold]  Location:[/bold] {args.location}")
        if args.notes:
            rprint(f"[bold]  Notes:[/bold] {args.notes}")
        if args.url:
            rprint(f"[bold]  URL:[/bold] {args.url}")
        if alerts:
            rprint(f"[bold]  Alerts:[/bold] {', '.join(str(a) for a in alerts)} before event")


if __name__ == '__main__':
    main()