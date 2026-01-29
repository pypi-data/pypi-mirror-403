#!/usr/bin/env python3
"""Schedule CLI command handlers for socialia."""

import json
import sys


def cmd_schedule(args, output_json: bool = False) -> int:
    """Handle schedule command."""
    from ..scheduler import (
        list_scheduled,
        cancel_scheduled,
        run_due_jobs,
        run_daemon,
        SCHEDULE_FILE,
    )

    cmd = getattr(args, "schedule_command", None)

    if cmd == "list":
        full = getattr(args, "full", False)
        jobs = list_scheduled(full=full)
        if output_json:
            print(json.dumps({"file": str(SCHEDULE_FILE), "jobs": jobs}, indent=2))
        elif not jobs:
            msg = "No jobs" if full else "No scheduled posts"
            print(f"{msg} ({SCHEDULE_FILE})")
        else:
            # Group by source file
            source_files = set(
                j.get("source_file") for j in jobs if j.get("source_file")
            )
            title = "All jobs" if full else "Scheduled posts"
            print(f"{title} ({len(jobs)}) - {SCHEDULE_FILE}")
            if source_files:
                print(f"Source: {', '.join(source_files)}")
            print("─" * 50)
            for job in jobs:
                scheduled = job.get("scheduled_for", "")[:16].replace("T", " ")
                status = job.get("status", "pending")
                headline = job.get("headline", "")

                # Status indicator
                status_icon = {
                    "pending": "⏳",
                    "completed": "✅",
                    "cancelled": "❌",
                    "failed": "💥",
                }.get(status, "❓")

                if headline:
                    print(
                        f"  {status_icon} [{job['id']}] {job['platform']} @ {scheduled}"
                    )
                    print(f"         {headline}")
                else:
                    print(
                        f"  {status_icon} [{job['id']}] {job['platform']} @ {scheduled}"
                    )
                    text = job.get("text", "")[:60]
                    if len(job.get("text", "")) > 60:
                        text += "..."
                    print(f"         {text}")

                # Show cancel reason if any
                if full and job.get("cancel_reason"):
                    print(f"         Reason: {job['cancel_reason']}")
                print()
        return 0

    elif cmd == "cancel":
        result = cancel_scheduled(args.job_id)
        if output_json:
            print(json.dumps(result, indent=2))
        elif result["success"]:
            print(f"Cancelled job: {args.job_id}")
        else:
            print(f"Error: {result['error']}", file=sys.stderr)
            return 1
        return 0

    elif cmd == "run":
        results = run_due_jobs()
        if output_json:
            print(json.dumps(results, indent=2))
        elif not results:
            print("No jobs due")
        else:
            for r in results:
                status = "✅" if r.get("success") else "❌"
                print(f"{status} Job {r['job_id']}")
                if r.get("url"):
                    print(f"   URL: {r['url']}")
                if r.get("error"):
                    print(f"   Error: {r['error']}")
        return 0

    elif cmd == "daemon":
        print(f"Schedule file: {SCHEDULE_FILE}")
        run_daemon(interval=args.interval)
        return 0

    elif cmd == "update-source":
        from ..scheduler import update_source_path

        result = update_source_path(args.old_path, args.new_path)
        if output_json:
            print(json.dumps(result, indent=2))
        elif result["updated"] > 0:
            print(f"Updated {result['updated']} job(s) to: {result['new_path']}")
        else:
            print(f"No jobs found with source: {args.old_path}")
        return 0

    else:
        print(
            "Usage: socialia schedule {list|cancel|run|daemon|update-source}",
            file=sys.stderr,
        )
        return 1
