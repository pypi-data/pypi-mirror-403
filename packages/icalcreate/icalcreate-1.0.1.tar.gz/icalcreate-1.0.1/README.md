# icalcreate

A CLI tool to create `.ics` calendar files and Google Calendar links.

## Installation

```bash
pip install icalcreate
```

Or install dependencies directly:

```bash
pip install icalendar pytz
```

## Usage

```bash
ical -t "Event Title" --time "2024-12-25 14:00" -d 1h [options]
```

### Required Arguments

| Argument | Description |
|----------|-------------|
| `-t, --title` | Event title |
| `--time` | Start time (e.g., "2024-12-25 14:00") |
| `-d, --duration` | Duration (e.g., "1h", "30m", "1h30m") |

### Optional Arguments

| Argument | Description |
|----------|-------------|
| `-l, --location` | Event location |
| `-n, --notes` | Event notes/description |
| `-u, --url` | Event URL |
| `-z, --timezone` | Time zone (default: UTC) |
| `-a, --alert` | Alert before event (can be used multiple times) |
| `-o, --output` | Output file name (default: `<title>.ics`) |
| `--google` | Generate and print Google Calendar URL |

## Examples

### Basic event
```bash
icalcreate -t "Team Meeting" --time "2024-12-25 14:00" -d 1h
```

### Event with location and notes
```bash
icalcreate -t "Conference" --time "2024-12-25 09:00" -d 2h30m \
    -l "Room 101" -n "Quarterly review meeting" -o conference.ics
```

### Event with multiple alerts
```bash
icalcreate -t "Important Call" --time "2024-12-25 10:00" -d 30m \
    --alert 15m --alert 5m --alert 1h
```

### Event with timezone
```bash
icalcreate -t "Webinar" --time "2024-12-25 15:00" -d 1h \
    -z "America/New_York"
```

### Generate Google Calendar link
```bash
icalcreate -t "Quick Sync" --time "2024-12-25 11:00" -d 15m --google
```

## Duration Format

- `30m` - 30 minutes
- `1h` - 1 hour
- `1h30m` - 1 hour 30 minutes
- `2d` - 2 days
- `90` - 90 minutes (plain number)

## Time Zones

Use standard IANA time zone names:
- `UTC`
- `America/New_York`
- `America/Los_Angeles`
- `Europe/London`
- `Europe/Paris`
- `Asia/Tokyo`

## Running as a Module

```bash
python -m icalcreate -t "Event" --time "2024-12-25 14:00" -d 1h
```

## License

AGPL3