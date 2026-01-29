#!/usr/bin/env python3
import argparse
import json
from datetime import datetime, date, time, timedelta
from pathlib import Path
import sys
import csv

__version__ = "0.3.1"

# Store data under user home to avoid writing inside site-packages after installation.
DATA_DIR = Path.home() / ".zcatcher"
DATA_FILE = DATA_DIR / "sleep_data.jsonl"


def ensure_data_dir(data_file: Path = DATA_FILE):
    data_file.parent.mkdir(parents=True, exist_ok=True)


def read_all_records(data_file: Path = DATA_FILE):
    if not data_file.exists():
        return []
    records = []
    with data_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                # Skip malformed lines
                continue
    return records


def write_record(record: dict, data_file: Path = DATA_FILE):
    ensure_data_dir(data_file)
    with data_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def parse_time_str(s: str) -> time:
    s = s.strip()
    compact = s.replace(":", "")

    if compact.isdigit() and 3 <= len(compact) <= 4:
        if len(compact) == 3:
            hour = int(compact[0])
            minute = int(compact[1:])
        else:
            hour = int(compact[:2])
            minute = int(compact[2:])
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return time(hour, minute)

    # Accept HH:MM in 24-hour format as fallback
    try:
        return datetime.strptime(s, "%H:%M").time()
    except ValueError:
        raise ValueError("Time must be in HH:MM 24-hour format; colon optional (e.g., 23:15 or 2315)")


def prompt_time(label: str) -> time:
    while True:
        inp = input(f"{label} (HHMM or HH:MM 24-hour): ").strip()
        try:
            return parse_time_str(inp)
        except ValueError as e:
            print(f"Invalid time: {e}")


def parse_date_str(s: str) -> date:
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()


def prompt_date(label: str, default: date) -> date:
    while True:
        inp = input(f"{label} (YYYY-MM-DD, default {default.isoformat()}): ").strip()
        if inp == "":
            return default
        try:
            return parse_date_str(inp)
        except ValueError:
            print("Please enter a date as YYYY-MM-DD (e.g., 2026-01-24) or leave blank for today.")


def prompt_difficulty(label: str) -> int:
    while True:
        inp = input(f"{label} (1-5): ").strip()
        try:
            val = int(inp)
            if 1 <= val <= 5:
                return val
        except ValueError:
            pass
        print("Please enter a number from 1 to 5.")


def compute_duration_hours(sleep_t: time, wake_t: time, wake_d: date) -> tuple[float, date]:
    # Assume wake date is today; sleep date may be same day or previous day
    wake_dt = datetime.combine(wake_d, wake_t)
    sleep_dt = datetime.combine(wake_d, sleep_t)
    if sleep_dt > wake_dt:
        # Bedtime is likely the previous day (e.g., 23:00 -> 07:00)
        sleep_dt -= timedelta(days=1)
    duration = wake_dt - sleep_dt
    hours = duration.total_seconds() / 3600.0
    return hours, sleep_dt.date()


def record_interactively(data_file: Path = DATA_FILE):
    print("==============================\nZCATCHER\n==============================\nLet's record your sleep.")
    sleep_t = prompt_time("Time you went to sleep")
    diff_sleep = prompt_difficulty("Difficulty falling asleep")
    wake_t = prompt_time("Time you woke up")
    diff_wake = prompt_difficulty("Difficulty waking up")

    wake_d = prompt_date("Wake date", default=date.today())
    duration_hours, sleep_d = compute_duration_hours(sleep_t, wake_t, wake_d)

    record = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "wake_date": wake_d.isoformat(),
        "sleep_date": sleep_d.isoformat(),
        "wake_time": wake_t.strftime("%H:%M"),
        "sleep_time": sleep_t.strftime("%H:%M"),
        "difficulty_sleep": diff_sleep,
        "difficulty_wake": diff_wake,
        "duration_hours": round(duration_hours, 2),
    }

    write_record(record, data_file)
    print("Saved.")
    print(
        f"You slept for {record['duration_hours']:.2f} hours (from {record['sleep_time']} on {record['sleep_date']} to {record['wake_time']} on {record['wake_date']})."
    )


def _filter_records_by_days(records: list[dict], days: int | None) -> list[dict]:
    if not days or days <= 0:
        return records
    cutoff = date.today() - timedelta(days=days)
    filtered = []
    for r in records:
        try:
            wd = datetime.strptime(r.get("wake_date", ""), "%Y-%m-%d").date()
        except Exception:
            continue
        if wd >= cutoff:
            filtered.append(r)
    return filtered


def print_stats(data_file: Path = DATA_FILE, days: int | None = None):
    records = read_all_records(data_file)
    if not records:
        print("No data available yet.")
        return

    records = _filter_records_by_days(records, days)
    if not records:
        print("No data in the selected range.")
        return

    n = len(records)
    total_hours = sum(r.get("duration_hours", 0.0) for r in records)
    avg_hours = total_hours / n

    total_diff_sleep = sum(int(r.get("difficulty_sleep", 0)) for r in records)
    total_diff_wake = sum(int(r.get("difficulty_wake", 0)) for r in records)
    avg_diff_sleep = total_diff_sleep / n
    avg_diff_wake = total_diff_wake / n

    print("Sleep Stats:")
    print(f"- Entries: {n}")
    print(f"- Average sleep: {avg_hours:.2f} hours")
    print(f"- Average difficulty falling asleep: {avg_diff_sleep:.2f} / 5")
    print(f"- Average difficulty waking up: {avg_diff_wake:.2f} / 5")
    if days and days > 0:
        print(f"- Range: last {days} days")


def _format_table(rows: list[list[str]]) -> str:
    if not rows:
        return "(no data)"
    # First row is header
    widths = [max(len(str(cell)) for cell in col) for col in zip(*rows)]

    def fmt(row: list[str]) -> str:
        return " | ".join(str(cell).ljust(w) for cell, w in zip(row, widths))

    sep = "-+-".join("-" * w for w in widths)
    header = fmt(rows[0])
    body = [fmt(r) for r in rows[1:]]
    return "\n".join([header, sep, *body]) if body else header


def print_data(data_file: Path = DATA_FILE):
    records = read_all_records(data_file)
    header = [
        "sleep_date",
        "sleep_time",
        "wake_date",
        "wake_time",
        "difficulty_sleep",
        "difficulty_wake",
        "duration_hours",
    ]
    rows = [header]
    for r in records:
        rows.append([
            str(r.get("sleep_date", "")),
            str(r.get("sleep_time", "")),
            str(r.get("wake_date", "")),
            str(r.get("wake_time", "")),
            str(r.get("difficulty_sleep", "")),
            str(r.get("difficulty_wake", "")),
            str(r.get("duration_hours", "")),
        ])
    print(_format_table(rows))


def print_json(data_file: Path = DATA_FILE):
    records = read_all_records(data_file)
    json.dump(records, sys.stdout, ensure_ascii=False, indent=2)
    print()


def print_csv(data_file: Path = DATA_FILE):
    records = read_all_records(data_file)
    writer = csv.writer(sys.stdout)
    header = [
        "sleep_date",
        "sleep_time",
        "wake_date",
        "wake_time",
        "difficulty_sleep",
        "difficulty_wake",
        "duration_hours",
        "created_at",
    ]
    writer.writerow(header)
    for r in records:
        writer.writerow([
            r.get("sleep_date", ""),
            r.get("sleep_time", ""),
            r.get("wake_date", ""),
            r.get("wake_time", ""),
            r.get("difficulty_sleep", ""),
            r.get("difficulty_wake", ""),
            r.get("duration_hours", ""),
            r.get("created_at", ""),
        ])


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Simple CLI to track sleep and view stats",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=(
            """Sleep well!"""
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--stats",
        action="store_true",
        help="View sleep stats (average sleep, difficulties)",
    )
    group.add_argument(
        "--data", action="store_true", help="Output all recorded sleep data"
    )
    group.add_argument(
        "--csv",
        action="store_true",
        help="Output all recorded sleep data in CSV to stdout",
    )
    group.add_argument(
        "--json",
        action="store_true",
        help="Output all recorded sleep data as JSON to stdout",
    )

    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help="Limit stats to the last N days",
    )

    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Custom path for data file (JSONL)",
    )

    args = parser.parse_args(argv)

    data_file = Path(args.file) if args.file else DATA_FILE

    if args.stats:
        print_stats(data_file=data_file, days=args.days)
        return 0
    if args.data:
        print_data(data_file=data_file)
        return 0
    if args.csv:
        print_csv(data_file=data_file)
        return 0
    if args.json:
        print_json(data_file=data_file)
        return 0

    # Default: interactive recording
    record_interactively(data_file=data_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
