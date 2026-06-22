#!/usr/bin/env python3
"""Summarize the first causal events in a ROS/SLAM run directory."""

from __future__ import annotations

import argparse
import collections
import re
import statistics
from pathlib import Path


EVENT_PATTERNS = {
    "initialization": re.compile(
        r"IMU Initial Done|Initialize the map|Node init finished", re.I
    ),
    "mode_or_control": re.compile(
        r"received control|requested with map_id|queued hint|mode=", re.I
    ),
    "localization_success": re.compile(
        r"Hint localization succeeded|Auto relocalization succeeded", re.I
    ),
    "correction_gate": re.compile(r"correction gated", re.I),
    "tracking_lost": re.compile(r"Tracking lost", re.I),
    "recovery_rejected": re.compile(
        r"recovery .*rejected|relocalization .*rejected", re.I
    ),
    "no_effective_points": re.compile(r"No Effective Points", re.I),
    "timestamp_or_tf": re.compile(
        r"timestamp|loop back|time sync|extrapolation|transform cache", re.I
    ),
    "queue_or_drop": re.compile(r"queue is full|dropping message|dropped", re.I),
    "map_io": re.compile(
        r"load_map|Saving map|wrote pcd|built localization map index", re.I
    ),
    "process_failure": re.compile(
        r"process has died|Segmentation fault|exit code|terminate called", re.I
    ),
}

TIMESTAMP = re.compile(r"\[(\d{9,}(?:\.\d+)?)\]")


def choose_run(path: Path, latest: bool) -> Path:
    if not latest:
        return path
    candidates = {
        file.parent
        for file in path.rglob("*.log")
        if file.is_file()
    }
    if not candidates:
        raise SystemExit(f"no .log files found below {path}")
    return max(
        candidates,
        key=lambda directory: max(
            (file.stat().st_mtime for file in directory.glob("*.log")),
            default=0,
        ),
    )


def parse_events(run: Path):
    events = []
    counts = collections.Counter()
    for log in sorted(run.glob("*.log")):
        try:
            lines = log.read_text(errors="replace").splitlines()
        except OSError as error:
            print(f"warning: cannot read {log}: {error}")
            continue
        for line_number, line in enumerate(lines, 1):
            kinds = [name for name, pattern in EVENT_PATTERNS.items() if pattern.search(line)]
            if not kinds:
                continue
            match = TIMESTAMP.search(line)
            timestamp = float(match.group(1)) if match else None
            for kind in kinds:
                counts[kind] += 1
            events.append((timestamp, log.name, line_number, kinds, line.strip()))
    events.sort(key=lambda item: (item[0] is None, item[0] or 0, item[1], item[2]))
    return events, counts


def interval_summary(events, kind: str) -> str | None:
    times = [
        timestamp
        for timestamp, _, _, kinds, _ in events
        if timestamp is not None and kind in kinds
    ]
    if len(times) < 3:
        return None
    intervals = [right - left for left, right in zip(times, times[1:]) if right >= left]
    if not intervals:
        return None
    return (
        f"{kind}: n={len(times)} median_interval={statistics.median(intervals):.3f}s "
        f"min={min(intervals):.3f}s max={max(intervals):.3f}s"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path, help="run directory or root containing runs")
    parser.add_argument("--latest", action="store_true", help="select newest directory with logs")
    parser.add_argument(
        "--timeline-limit",
        type=int,
        default=80,
        help="maximum selected events to print",
    )
    args = parser.parse_args()

    run = choose_run(args.path.resolve(), args.latest)
    if not run.is_dir():
        raise SystemExit(f"not a directory: {run}")

    events, counts = parse_events(run)
    print(f"run: {run}")
    print("artifacts:")
    for artifact in sorted(run.iterdir()):
        if artifact.is_file():
            print(f"  {artifact.name}: {artifact.stat().st_size} bytes")

    print("event counts:")
    for kind, count in counts.most_common():
        print(f"  {kind}: {count}")

    print("periodicity:")
    periodic = False
    for kind in ("tracking_lost", "recovery_rejected", "correction_gate"):
        summary = interval_summary(events, kind)
        if summary:
            periodic = True
            print(f"  {summary}")
    if not periodic:
        print("  insufficient repeated timestamped events")

    important = [
        event
        for event in events
        if any(
            kind in event[3]
            for kind in (
                "localization_success",
                "correction_gate",
                "tracking_lost",
                "recovery_rejected",
                "timestamp_or_tf",
                "queue_or_drop",
                "process_failure",
            )
        )
    ]
    print("causal timeline:")
    for timestamp, filename, line_number, kinds, line in important[: args.timeline_limit]:
        time_text = f"{timestamp:.6f}" if timestamp is not None else "no-time"
        print(
            f"  {time_text} {filename}:{line_number} "
            f"[{','.join(kinds)}] {line}"
        )
    if len(important) > args.timeline_limit:
        print(f"  ... {len(important) - args.timeline_limit} more events omitted")


if __name__ == "__main__":
    main()

