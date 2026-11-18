#!/usr/bin/env python3
"""
Simple repeatable CockroachDB transaction benchmark.
Run once with all nodes online, then again with node3 stopped.
"""
import argparse
import csv
import os
import statistics
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import psycopg

def percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round((pct / 100) * (len(ordered) - 1)))))
    return ordered[index]

def worker(worker_id, deadline, dsn, records, lock):
    conn = None
    iteration = 0

    while time.monotonic() < deadline:
        started = time.perf_counter()
        success = False
        error_text = ""

        try:
            if conn is None or conn.closed:
                conn = psycopg.connect(dsn, connect_timeout=4, autocommit=True)
            account_id = (worker_id * 1000) + (iteration % 1000) + 1

            with conn.transaction():
                conn.execute(
                    "UPDATE accounts SET balance = balance + 1.00 WHERE id = %s",
                    (account_id,),
                )
                conn.execute(
                    "SELECT balance FROM accounts WHERE id = %s",
                    (account_id,),
                ).fetchone()

            success = True
            iteration += 1
        except Exception as exc:
            error_text = f"{type(exc).__name__}: {exc}".replace("\n", " ")[:240]
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
                conn = None
            time.sleep(0.15)

        elapsed_ms = (time.perf_counter() - started) * 1000
        row = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "worker": worker_id,
            "latency_ms": round(elapsed_ms, 3),
            "success": success,
            "error": error_text,
        }
        with lock:
            records.append(row)

    if conn is not None:
        conn.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True, choices=["baseline", "node3_down"])
    parser.add_argument("--duration", type=int, default=60)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--port", type=int, default=26257)
    args = parser.parse_args()

    dsn = (
        f"postgresql://root@localhost:{args.port}/distributed_lab"
        "?sslmode=disable"
    )
    deadline = time.monotonic() + args.duration
    records = []
    lock = threading.Lock()
    threads = [
        threading.Thread(
            target=worker,
            args=(worker_id, deadline, dsn, records, lock),
            daemon=True,
        )
        for worker_id in range(args.workers)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{args.scenario}.csv"

    fields = ["timestamp_utc", "worker", "latency_ms", "success", "error"]
    with output_file.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    successful = [r["latency_ms"] for r in records if r["success"]]
    failures = len(records) - len(successful)
    total = len(records)
    success_rate = (len(successful) / total * 100) if total else 0

    print(f"\nScenario: {args.scenario}")
    print(f"Total attempts: {total}")
    print(f"Successful transactions: {len(successful)}")
    print(f"Failed attempts: {failures}")
    print(f"Success rate: {success_rate:.2f}%")
    if successful:
        print(f"Mean latency: {statistics.mean(successful):.3f} ms")
        print(f"Median latency: {statistics.median(successful):.3f} ms")
        print(f"P95 latency: {percentile(successful, 95):.3f} ms")
    print(f"CSV saved to: {output_file}")

if __name__ == "__main__":
    main()
