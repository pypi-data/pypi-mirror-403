"""Exhaustive tests for icalcreate CLI module."""

import os
import subprocess
import sys
from datetime import datetime, timedelta
from urllib.parse import parse_qs, urlparse
import pytest
import pytz
from icalendar import Calendar

from icalcreate.cli import (
    parse_datetime, parse_duration, parse_alert, create_ics_event, generate_google_calendar_url
)


class TestParseDatetime:
    """Tests for parse_datetime function with various formats and timezones."""

    @pytest.mark.parametrize("dt_string,expected_dt", [
        ("2024-12-25 14:00", datetime(2024, 12, 25, 14, 0)),
        ("2024-12-25T14:00", datetime(2024, 12, 25, 14, 0)),
        ("2024-12-25 14:00:30", datetime(2024, 12, 25, 14, 0, 30)),
        ("2024-12-25T14:00:30", datetime(2024, 12, 25, 14, 0, 30)),
        ("25/12/2024 14:00", datetime(2024, 12, 25, 14, 0)),
        ("12/25/2024 14:00", datetime(2024, 12, 25, 14, 0)),
    ])
    def test_parse_datetime_formats_utc(self, dt_string, expected_dt):
        """Test parsing various datetime formats with UTC timezone."""
        result = parse_datetime(dt_string, "UTC")
        assert result.year == expected_dt.year
        assert result.month == expected_dt.month
        assert result.day == expected_dt.day
        assert result.hour == expected_dt.hour
        assert result.minute == expected_dt.minute
        assert result.tzinfo is not None

    @pytest.mark.parametrize("timezone", [
        "UTC", "America/New_York", "America/Los_Angeles", "Europe/London", "Europe/Paris",
        "Asia/Tokyo", "Australia/Sydney", "Africa/Cairo", "America/Sao_Paulo"
    ])
    def test_parse_datetime_various_timezones(self, timezone):
        """Test parsing datetime with various IANA timezones."""
        result = parse_datetime("2024-12-25 14:00", timezone)
        assert result.tzinfo is not None
        assert result.year == 2024 and result.month == 12 and result.day == 25
        assert result.hour == 14 and result.minute == 0

    def test_parse_datetime_timezone_offset_applied(self):
        """Test that timezone is correctly applied to the datetime."""
        utc_result = parse_datetime("2024-12-25 14:00", "UTC")
        ny_result = parse_datetime("2024-12-25 14:00", "America/New_York")
        assert utc_result.utcoffset() != ny_result.utcoffset()

    @pytest.mark.parametrize("invalid_dt", [
        "invalid", "2024-13-25 14:00", "2024-12-32 14:00", "2024/12/25 14:00",
        "25-12-2024 14:00", "14:00 2024-12-25", "", "2024-12-25"
    ])
    def test_parse_datetime_invalid_formats(self, invalid_dt):
        """Test that invalid datetime formats raise ValueError."""
        with pytest.raises(ValueError, match="Unable to parse datetime"):
            parse_datetime(invalid_dt, "UTC")

    def test_parse_datetime_invalid_timezone(self):
        """Test that invalid timezone raises exception."""
        with pytest.raises(pytz.UnknownTimeZoneError):
            parse_datetime("2024-12-25 14:00", "Invalid/Timezone")


class TestParseDuration:
    """Tests for parse_duration function with various formats."""

    @pytest.mark.parametrize("duration_str,expected_minutes", [
        ("1h", 60), ("2h", 120), ("30m", 30), ("90m", 90), ("1h30m", 90), ("2h15m", 135),
        ("1d", 1440), ("2d", 2880), ("1d12h", 1440 + 720), ("1d2h30m", 1440 + 120 + 30),
        ("90", 90), ("60", 60), ("120", 120),
        ("1H", 60), ("30M", 30), ("1D", 1440),
        ("  1h  ", 60), ("1h 30m", 90),
    ])
    def test_parse_duration_valid_formats(self, duration_str, expected_minutes):
        """Test parsing various valid duration formats."""
        result = parse_duration(duration_str)
        assert result == timedelta(minutes=expected_minutes)

    @pytest.mark.parametrize("invalid_duration", ["", "0", "0h", "0m", "abc", "h", "m", "d"])
    def test_parse_duration_invalid_formats(self, invalid_duration):
        """Test that invalid duration formats raise ValueError."""
        with pytest.raises(ValueError, match="Unable to parse duration"):
            parse_duration(invalid_duration)

    def test_parse_duration_edge_cases(self):
        """Test edge cases for duration parsing."""
        assert parse_duration("1") == timedelta(minutes=1)
        assert parse_duration("100h") == timedelta(hours=100)
        assert parse_duration("1000m") == timedelta(minutes=1000)


class TestParseAlert:
    """Tests for parse_alert function."""

    @pytest.mark.parametrize("alert_str,expected_minutes", [
        ("5m", 5), ("15m", 15), ("30m", 30), ("1h", 60), ("2h", 120), ("1d", 1440), ("1h30m", 90)
    ])
    def test_parse_alert_valid_formats(self, alert_str, expected_minutes):
        """Test parsing various valid alert time formats."""
        result = parse_alert(alert_str)
        assert result == timedelta(minutes=expected_minutes)

    def test_parse_alert_invalid_format(self):
        """Test that invalid alert format raises ValueError."""
        with pytest.raises(ValueError):
            parse_alert("invalid")


class TestCreateIcsEvent:
    """Tests for create_ics_event function with various parameter combinations."""

    def test_create_event_required_params_only(self, sample_datetime_utc, sample_duration_1h):
        """Test creating event with only required parameters."""
        cal = create_ics_event("Test Event", sample_datetime_utc, sample_duration_1h)
        ics_data = cal.to_ical().decode('utf-8')
        assert "BEGIN:VCALENDAR" in ics_data
        assert "BEGIN:VEVENT" in ics_data
        assert "SUMMARY:Test Event" in ics_data
        assert "END:VEVENT" in ics_data
        assert "END:VCALENDAR" in ics_data

    def test_create_event_with_location(self, sample_datetime_utc, sample_duration_1h):
        """Test creating event with location."""
        cal = create_ics_event("Test Event", sample_datetime_utc, sample_duration_1h, location="Room 101")
        ics_data = cal.to_ical().decode('utf-8')
        assert "LOCATION:Room 101" in ics_data

    def test_create_event_with_notes(self, sample_datetime_utc, sample_duration_1h):
        """Test creating event with notes/description."""
        cal = create_ics_event("Test Event", sample_datetime_utc, sample_duration_1h, notes="Meeting notes here")
        ics_data = cal.to_ical().decode('utf-8')
        assert "DESCRIPTION:Meeting notes here" in ics_data

    def test_create_event_with_url(self, sample_datetime_utc, sample_duration_1h):
        """Test creating event with URL."""
        cal = create_ics_event("Test Event", sample_datetime_utc, sample_duration_1h, url="https://example.com")
        ics_data = cal.to_ical().decode('utf-8')
        assert "URL:https://example.com" in ics_data

    def test_create_event_with_single_alert(self, sample_datetime_utc, sample_duration_1h):
        """Test creating event with a single alert."""
        alerts = [timedelta(minutes=15)]
        cal = create_ics_event("Test Event", sample_datetime_utc, sample_duration_1h, alerts=alerts)
        ics_data = cal.to_ical().decode('utf-8')
        assert "BEGIN:VALARM" in ics_data
        assert "ACTION:DISPLAY" in ics_data
        assert "END:VALARM" in ics_data

    def test_create_event_with_multiple_alerts(self, sample_datetime_utc, sample_duration_1h):
        """Test creating event with multiple alerts."""
        alerts = [timedelta(minutes=15), timedelta(hours=1), timedelta(days=1)]
        cal = create_ics_event("Test Event", sample_datetime_utc, sample_duration_1h, alerts=alerts)
        ics_data = cal.to_ical().decode('utf-8')
        assert ics_data.count("BEGIN:VALARM") == 3
        assert ics_data.count("END:VALARM") == 3

    def test_create_event_with_all_params(self, sample_datetime_utc, sample_duration_1h):
        """Test creating event with all parameters."""
        alerts = [timedelta(minutes=15), timedelta(hours=1)]
        cal = create_ics_event(
            title="Full Event", start_time=sample_datetime_utc, duration=sample_duration_1h,
            location="Conference Room A", notes="Important meeting", url="https://meet.example.com", alerts=alerts
        )
        ics_data = cal.to_ical().decode('utf-8')
        assert "SUMMARY:Full Event" in ics_data
        assert "LOCATION:Conference Room A" in ics_data
        assert "DESCRIPTION:Important meeting" in ics_data
        assert "URL:https://meet.example.com" in ics_data
        assert ics_data.count("BEGIN:VALARM") == 2

    def test_create_event_dtstart_dtend_correct(self, sample_datetime_utc):
        """Test that DTSTART and DTEND are correctly set based on duration."""
        duration = timedelta(hours=2, minutes=30)
        cal = create_ics_event("Test", sample_datetime_utc, duration)
        event = list(cal.walk('VEVENT'))[0]
        dtstart = event.get('dtstart').dt
        dtend = event.get('dtend').dt
        assert dtend - dtstart == duration

    def test_create_event_calendar_properties(self, sample_datetime_utc, sample_duration_1h):
        """Test that calendar has correct properties."""
        cal = create_ics_event("Test", sample_datetime_utc, sample_duration_1h)
        assert cal.get('prodid') == '-//icalcreate//EN'
        assert cal.get('version') == '2.0'
        assert cal.get('calscale') == 'GREGORIAN'
        assert cal.get('method') == 'PUBLISH'

    def test_create_event_has_uid(self, sample_datetime_utc, sample_duration_1h):
        """Test that event has a unique UID."""
        cal = create_ics_event("Test", sample_datetime_utc, sample_duration_1h)
        event = list(cal.walk('VEVENT'))[0]
        uid = str(event.get('uid'))
        assert '@icalcreate' in uid

    def test_create_event_special_characters_in_title(self, sample_datetime_utc, sample_duration_1h):
        """Test event creation with special characters in title."""
        special_title = "Meeting: Q&A Session (Virtual) - 2024"
        cal = create_ics_event(special_title, sample_datetime_utc, sample_duration_1h)
        event = list(cal.walk('VEVENT'))[0]
        assert str(event.get('summary')) == special_title

    @pytest.mark.parametrize("duration", [
        timedelta(minutes=15), timedelta(minutes=30), timedelta(hours=1), timedelta(hours=2),
        timedelta(hours=8), timedelta(days=1), timedelta(days=7)
    ])
    def test_create_event_various_durations(self, sample_datetime_utc, duration):
        """Test event creation with various durations."""
        cal = create_ics_event("Test", sample_datetime_utc, duration)
        event = list(cal.walk('VEVENT'))[0]
        actual_duration = event.get('dtend').dt - event.get('dtstart').dt
        assert actual_duration == duration


class TestGenerateGoogleCalendarUrl:
    """Tests for generate_google_calendar_url function."""

    def test_google_url_basic(self, sample_datetime_utc, sample_duration_1h):
        """Test basic Google Calendar URL generation."""
        url = generate_google_calendar_url("Test Event", sample_datetime_utc, sample_duration_1h)
        assert url.startswith("https://calendar.google.com/calendar/render?")
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert params['action'][0] == 'TEMPLATE'
        assert params['text'][0] == 'Test Event'
        assert 'dates' in params
        assert 'ctz' in params

    def test_google_url_with_location(self, sample_datetime_utc, sample_duration_1h):
        """Test Google Calendar URL with location."""
        url = generate_google_calendar_url("Test", sample_datetime_utc, sample_duration_1h, location="Room 101")
        params = parse_qs(urlparse(url).query)
        assert params['location'][0] == 'Room 101'

    def test_google_url_with_notes(self, sample_datetime_utc, sample_duration_1h):
        """Test Google Calendar URL with notes/details."""
        url = generate_google_calendar_url("Test", sample_datetime_utc, sample_duration_1h, notes="Event details")
        params = parse_qs(urlparse(url).query)
        assert params['details'][0] == 'Event details'

    def test_google_url_with_all_params(self, sample_datetime_utc, sample_duration_1h):
        """Test Google Calendar URL with all parameters."""
        url = generate_google_calendar_url(
            "Full Event", sample_datetime_utc, sample_duration_1h, location="Office", notes="Important"
        )
        params = parse_qs(urlparse(url).query)
        assert params['text'][0] == 'Full Event'
        assert params['location'][0] == 'Office'
        assert params['details'][0] == 'Important'

    def test_google_url_dates_format(self, sample_datetime_utc, sample_duration_1h):
        """Test that dates are in correct format (YYYYMMDDTHHmmss)."""
        url = generate_google_calendar_url("Test", sample_datetime_utc, sample_duration_1h)
        params = parse_qs(urlparse(url).query)
        dates = params['dates'][0]
        assert '/' in dates
        start, end = dates.split('/')
        assert len(start) == 15 and 'T' in start
        assert len(end) == 15 and 'T' in end

    def test_google_url_timezone_utc(self, sample_datetime_utc, sample_duration_1h):
        """Test Google Calendar URL includes correct timezone for UTC."""
        url = generate_google_calendar_url("Test", sample_datetime_utc, sample_duration_1h)
        params = parse_qs(urlparse(url).query)
        assert params['ctz'][0] == 'UTC'

    def test_google_url_timezone_ny(self, sample_datetime_ny, sample_duration_1h):
        """Test Google Calendar URL includes correct timezone for New York."""
        url = generate_google_calendar_url("Test", sample_datetime_ny, sample_duration_1h)
        params = parse_qs(urlparse(url).query)
        assert params['ctz'][0] == 'America/New_York'

    def test_google_url_special_characters_encoded(self, sample_datetime_utc, sample_duration_1h):
        """Test that special characters are URL-encoded."""
        url = generate_google_calendar_url("Q&A Session", sample_datetime_utc, sample_duration_1h, location="Room #1")
        assert "Q%26A" in url or "Q&A" in url
        params = parse_qs(urlparse(url).query)
        assert params['text'][0] == 'Q&A Session'


class TestCLIIntegration:
    """Integration tests for the CLI using subprocess."""

    def test_cli_help(self):
        """Test that --help works."""
        result = subprocess.run([sys.executable, "-m", "icalcreate", "--help"], capture_output=True, text=True)
        assert result.returncode == 0
        assert "icalcreate" in result.stdout
        assert "--title" in result.stdout
        assert "--time" in result.stdout
        assert "--duration" in result.stdout

    def test_cli_missing_required_args(self):
        """Test CLI fails without required arguments."""
        result = subprocess.run([sys.executable, "-m", "icalcreate"], capture_output=True, text=True)
        assert result.returncode != 0

    def test_cli_create_basic_event(self, temp_output_dir):
        """Test CLI creates basic event file."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Test Event", "--time", "2024-12-25 14:00", "-d", "1h", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            content = f.read()
        assert "BEGIN:VCALENDAR" in content
        assert "SUMMARY:Test Event" in content

    def test_cli_create_event_with_location(self, temp_output_dir):
        """Test CLI creates event with location."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "2024-12-25 14:00", "-d", "1h", "-l", "Room 101", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        with open(output_file, 'r') as f:
            content = f.read()
        assert "LOCATION:Room 101" in content

    def test_cli_create_event_with_notes(self, temp_output_dir):
        """Test CLI creates event with notes."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "2024-12-25 14:00", "-d", "1h", "-n", "Important notes", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        with open(output_file, 'r') as f:
            content = f.read()
        assert "DESCRIPTION:Important notes" in content

    def test_cli_create_event_with_url(self, temp_output_dir):
        """Test CLI creates event with URL."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Webinar", "--time", "2024-12-25 14:00", "-d", "1h", "-u", "https://example.com", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        with open(output_file, 'r') as f:
            content = f.read()
        assert "URL:https://example.com" in content

    def test_cli_create_event_with_timezone(self, temp_output_dir):
        """Test CLI creates event with specific timezone."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "2024-12-25 14:00", "-d", "1h", "-z", "America/New_York", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert os.path.exists(output_file)

    def test_cli_create_event_with_single_alert(self, temp_output_dir):
        """Test CLI creates event with single alert."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "2024-12-25 14:00", "-d", "1h", "-a", "15m", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        with open(output_file, 'r') as f:
            content = f.read()
        assert "BEGIN:VALARM" in content

    def test_cli_create_event_with_multiple_alerts(self, temp_output_dir):
        """Test CLI creates event with multiple alerts."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "2024-12-25 14:00", "-d", "1h",
            "-a", "15m", "-a", "1h", "-a", "1d", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        with open(output_file, 'r') as f:
            content = f.read()
        assert content.count("BEGIN:VALARM") == 3

    def test_cli_create_event_all_params(self, temp_output_dir):
        """Test CLI creates event with all parameters."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Full Event", "--time", "2024-12-25 14:00", "-d", "2h30m",
            "-l", "Conference Room", "-n", "Quarterly review", "-u", "https://meet.example.com",
            "-z", "Europe/London", "-a", "15m", "-a", "1h", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        with open(output_file, 'r') as f:
            content = f.read()
        assert "SUMMARY:Full Event" in content
        assert "LOCATION:Conference Room" in content
        assert "DESCRIPTION:Quarterly review" in content
        assert "URL:https://meet.example.com" in content
        assert content.count("BEGIN:VALARM") == 2

    def test_cli_google_option(self, temp_output_dir):
        """Test CLI --google option outputs Google Calendar URL."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "2024-12-25 14:00", "-d", "1h", "--google", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert "calendar.google.com" in result.stdout

    def test_cli_google_with_location_and_notes(self, temp_output_dir):
        """Test CLI --google option includes location and notes in URL."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "2024-12-25 14:00", "-d", "1h",
            "-l", "Office", "-n", "Notes here", "--google", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert "calendar.google.com" in result.stdout

    def test_cli_invalid_timezone(self, temp_output_dir):
        """Test CLI fails with invalid timezone."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "2024-12-25 14:00", "-d", "1h", "-z", "Invalid/TZ", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode != 0

    def test_cli_invalid_datetime(self, temp_output_dir):
        """Test CLI fails with invalid datetime."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "invalid-date", "-d", "1h", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode != 0

    def test_cli_invalid_duration(self, temp_output_dir):
        """Test CLI fails with invalid duration."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "2024-12-25 14:00", "-d", "invalid", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode != 0

    def test_cli_default_output_filename(self, temp_output_dir):
        """Test CLI creates file with title-based name when -o not specified."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_output_dir)
            result = subprocess.run([
                sys.executable, "-m", "icalcreate",
                "-t", "My Event", "--time", "2024-12-25 14:00", "-d", "1h"
            ], capture_output=True, text=True)
            assert result.returncode == 0, f"CLI failed: {result.stderr}"
            assert os.path.exists(os.path.join(temp_output_dir, "My_Event.ics"))
        finally:
            os.chdir(original_cwd)

    def test_cli_output_adds_ics_extension(self, temp_output_dir):
        """Test CLI adds .ics extension if not provided."""
        output_file = os.path.join(temp_output_dir, "test")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "2024-12-25 14:00", "-d", "1h", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert os.path.exists(output_file + ".ics")

    @pytest.mark.parametrize("duration_str", ["30m", "1h", "1h30m", "2h", "90", "1d"])
    def test_cli_various_durations(self, temp_output_dir, duration_str):
        """Test CLI with various duration formats."""
        output_file = os.path.join(temp_output_dir, f"test_{duration_str}.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "2024-12-25 14:00", "-d", duration_str, "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert os.path.exists(output_file)

    @pytest.mark.parametrize("time_format", [
        "2024-12-25 14:00", "2024-12-25T14:00", "2024-12-25 14:00:30", "25/12/2024 14:00", "12/25/2024 14:00"
    ])
    def test_cli_various_time_formats(self, temp_output_dir, time_format):
        """Test CLI with various time formats."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        result = subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", time_format, "-d", "1h", "-o", output_file
        ], capture_output=True, text=True)
        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert os.path.exists(output_file)


class TestIcsFileContent:
    """Tests verifying the content of generated .ics files matches inputs."""

    def test_ics_file_is_valid_calendar(self, temp_output_dir):
        """Test that generated .ics file can be parsed as valid iCalendar."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Test Event", "--time", "2024-12-25 14:00", "-d", "1h", "-o", output_file
        ], capture_output=True)
        with open(output_file, 'rb') as f:
            cal = Calendar.from_ical(f.read())
        events = list(cal.walk('VEVENT'))
        assert len(events) == 1

    def test_ics_file_content_matches_input(self, temp_output_dir):
        """Test that .ics file content matches CLI inputs."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Important Meeting", "--time", "2024-12-25 14:00", "-d", "2h",
            "-l", "Board Room", "-n", "Annual review", "-u", "https://company.com/meeting", "-o", output_file
        ], capture_output=True)
        with open(output_file, 'rb') as f:
            cal = Calendar.from_ical(f.read())
        event = list(cal.walk('VEVENT'))[0]
        assert str(event.get('summary')) == "Important Meeting"
        assert str(event.get('location')) == "Board Room"
        assert str(event.get('description')) == "Annual review"
        assert str(event.get('url')) == "https://company.com/meeting"

    def test_ics_file_duration_matches_input(self, temp_output_dir):
        """Test that event duration in .ics file matches input."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "2024-12-25 14:00", "-d", "2h30m", "-o", output_file
        ], capture_output=True)
        with open(output_file, 'rb') as f:
            cal = Calendar.from_ical(f.read())
        event = list(cal.walk('VEVENT'))[0]
        dtstart = event.get('dtstart').dt
        dtend = event.get('dtend').dt
        duration = dtend - dtstart
        assert duration == timedelta(hours=2, minutes=30)

    def test_ics_file_alerts_count_matches_input(self, temp_output_dir):
        """Test that number of alerts in .ics file matches input."""
        output_file = os.path.join(temp_output_dir, "test.ics")
        subprocess.run([
            sys.executable, "-m", "icalcreate",
            "-t", "Meeting", "--time", "2024-12-25 14:00", "-d", "1h",
            "-a", "15m", "-a", "1h", "-a", "1d", "-o", output_file
        ], capture_output=True)
        with open(output_file, 'rb') as f:
            cal = Calendar.from_ical(f.read())
        event = list(cal.walk('VEVENT'))[0]
        alarms = list(event.walk('VALARM'))
        assert len(alarms) == 3
