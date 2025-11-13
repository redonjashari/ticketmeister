import re
import argparse
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Tuple
import csv
import os

import matplotlib
matplotlib.use("Agg")  # for non-GUI environments
import matplotlib.pyplot as plt


ACCESS_LOG_PATTERN = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<time>.*?)\] "(?P<method>\S+) (?P<path>\S+)[^"]*" (?P<status>\d{3}) (?P<size>\S+) "[^"]*" "(?P<agent>[^"]*)"'
)

ERROR_LOG_PATTERN = re.compile(
    r'\[(?P<time>.*?)\] \[(?P<module>[^\]]+)\] (?:\[pid (?P<pid>\d+)\] )?(?:\[client (?P<ip>[^]]+)\] )?(?P<message>.*)'
)


def parse_access_time(t: str) -> datetime:
    # Example: 09/Nov/2025:10:15:23 +0100
    dt = datetime.strptime(t, "%d/%b/%Y:%H:%M:%S %z")
    # drop timezone info so we can compare with naive datetimes from the error log
    return dt.replace(tzinfo=None)


def parse_error_time(t: str) -> datetime:
    # Examples:
    # Sun Nov 09 10:16:01.123456 2025
    # Sun Nov 09 10:16:01 2025
    for fmt in ("%a %b %d %H:%M:%S.%f %Y", "%a %b %d %H:%M:%S %Y"):
        try:
            return datetime.strptime(t, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unrecognized error-log time format: {t}")


def classify_browser(agent: str) -> str:
    ua = agent.lower()
    if "chrome" in ua and "edge" not in ua and "chromium" not in ua and "opr" not in ua:
        return "Chrome"
    if "firefox" in ua:
        return "Firefox"
    if "safari" in ua and "chrome" not in ua:
        return "Safari"
    if "edge" in ua:
        return "Edge"
    if "trident" in ua or "msie" in ua:
        return "IE"
    return "Other"


def bucket_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


def analyze_logs(access_path: str, error_path: str, prefix: str) -> None:
    # Data structures for access statistics
    page_hits: Dict[str, int] = Counter()
    page_ips: Dict[str, set] = defaultdict(set)
    page_browsers: Dict[str, Counter] = defaultdict(Counter)
    page_timestamps: Dict[str, List[datetime]] = defaultdict(list)

    # Timeline: hits and errors per hour bucket (from access log)
    hits_timeline: Dict[datetime, int] = Counter()
    errors_timeline: Dict[datetime, int] = Counter()

    # Error stats
    error_codes: Counter = Counter()
    error_entries: List[Tuple[datetime, str, str, str]] = []  # (time, ip, code_or_module, message/path)

    # Parse access log
    with open(access_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = ACCESS_LOG_PATTERN.match(line)
            if not m:
                continue  # skip lines we can't parse
            ip = m.group("ip")
            t_raw = m.group("time")
            method = m.group("method")
            path = m.group("path")
            status = int(m.group("status"))
            agent = m.group("agent")

            dt = parse_access_time(t_raw)
            bucket = bucket_hour(dt)

            page_hits[path] += 1
            page_ips[path].add(ip)
            page_browsers[path][classify_browser(agent)] += 1
            page_timestamps[path].append(dt)

            hits_timeline[bucket] += 1

            if status >= 400:
                # treat as error
                error_codes[status] += 1
                errors_timeline[bucket] += 1
                error_entries.append((dt, ip, str(status), path))

    # Parse error log for extra info
    if error_path and os.path.exists(error_path):
        with open(error_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                m = ERROR_LOG_PATTERN.match(line)
                if not m:
                    continue
                t_raw = m.group("time")
                module = m.group("module")
                ip = m.group("ip") or "-"
                message = (m.group("message") or "").strip()
                dt = parse_error_time(t_raw)
                bucket = bucket_hour(dt)
                # Count all error-log entries under a pseudo code "ERROR" (using module name)
                error_codes[module] += 1
                errors_timeline[bucket] += 1
                error_entries.append((dt, ip, module, message))

    # Sort timelines
    all_buckets = sorted(set(hits_timeline.keys()) | set(errors_timeline.keys()))

    # Write CSV files
    requests_csv = f"{prefix}_requests_timeline.csv"
    errors_csv = f"{prefix}_errors_timeline.csv"
    page_hits_csv = f"{prefix}_page_hits.csv"

    with open(requests_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "hits", "errors"])
        for b in all_buckets:
            writer.writerow([
                b.isoformat(),
                hits_timeline.get(b, 0),
                errors_timeline.get(b, 0),
            ])

    with open(errors_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "error_count"])
        for b in all_buckets:
            writer.writerow([b.isoformat(), errors_timeline.get(b, 0)])

    with open(page_hits_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["path", "hits", "unique_ips"])
        for path, count in sorted(page_hits.items(), key=lambda x: x[1], reverse=True):
            writer.writerow([path, count, len(page_ips[path])])

    # Write text summary
    summary_path = f"{prefix}_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        print("=== Page access statistics ===", file=f)
        for path, count in sorted(page_hits.items(), key=lambda x: x[1], reverse=True):
            print(f"\nPage: {path}", file=f)
            print(f"  Total hits: {count}", file=f)
            print(f"  Unique IPs: {len(page_ips[path])}", file=f)
            print(f"  IP list: {', '.join(sorted(page_ips[path]))}", file=f)
            print("  Browsers:", file=f)
            for browser, bcount in page_browsers[path].most_common():
                print(f"    {browser}: {bcount}", file=f)

        print("\n=== Error statistics ===", file=f)
        for code, count in error_codes.most_common():
            print(f"  {code}: {count}", file=f)

        print("\n=== Sample error entries ===", file=f)
        for entry in sorted(error_entries, key=lambda e: e[0])[:20]:
            dt, ip, code, msg = entry
            print(f"  [{dt.isoformat()}] {ip} {code} {msg}", file=f)

    # Create plots
    if all_buckets:
        # Requests + errors timeline
        times = all_buckets
        hits = [hits_timeline.get(b, 0) for b in times]
        errs = [errors_timeline.get(b, 0) for b in times]

        plt.figure()
        plt.plot(times, hits, marker="o", label="Hits")
        plt.plot(times, errs, marker="x", linestyle="--", label="Errors")
        plt.xlabel("Time (hour)")
        plt.ylabel("Count")
        plt.title("Requests and Errors Over Time")
        plt.legend()
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(f"{prefix}_requests_timeline.png")
        plt.close()

        # Errors only
        plt.figure()
        plt.plot(times, errs, marker="o")
        plt.xlabel("Time (hour)")
        plt.ylabel("Error count")
        plt.title("Errors Over Time")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(f"{prefix}_errors_timeline.png")
        plt.close()

    # Page hits bar chart
    if page_hits:
        paths_sorted = [p for p, _ in sorted(page_hits.items(), key=lambda x: x[1], reverse=True)]
        counts_sorted = [page_hits[p] for p in paths_sorted]

        plt.figure()
        plt.bar(range(len(paths_sorted)), counts_sorted)
        plt.xticks(range(len(paths_sorted)), paths_sorted, rotation=45, ha="right")
        plt.xlabel("Page")
        plt.ylabel("Hits")
        plt.title("Page Hit Counts")
        plt.tight_layout()
        plt.savefig(f"{prefix}_page_hits.png")
        plt.close()

    print(f"Analysis complete. Files written with prefix '{prefix}'.")
    print(f"- Summary: {summary_path}")
    print(f"- Requests timeline CSV: {requests_csv}")
    print(f"- Errors timeline CSV: {errors_csv}")
    print(f"- Page hits CSV: {page_hits_csv}")
    print(f"- Timeline plot: {prefix}_requests_timeline.png")
    print(f"- Error timeline plot: {prefix}_errors_timeline.png")
    print(f"- Page hits plot: {prefix}_page_hits.png")


def main():
    parser = argparse.ArgumentParser(description="Analyze Apache access and error logs.")
    parser.add_argument("--access", required=True, help="Path to Apache access log")
    parser.add_argument("--error", default="", help="Path to Apache error log")
    parser.add_argument("--prefix", default="report", help="Prefix for output files")
    args = parser.parse_args()

    analyze_logs(args.access, args.error, args.prefix)


if __name__ == "__main__":
    main()
