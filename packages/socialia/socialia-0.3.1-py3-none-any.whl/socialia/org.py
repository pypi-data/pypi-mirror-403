#!/usr/bin/env python3
"""Org mode integration for managing social media drafts."""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class OrgDraft:
    """Represents a social media draft from an org file."""

    headline: str
    status: str  # TODO, DONE, CANCELLED
    priority: Optional[str]  # A, B, C
    scheduled: Optional[datetime]
    platform: str
    draft_id: Optional[str]
    content: str
    line_number: int  # For updating the file

    @property
    def is_pending(self) -> bool:
        return self.status == "TODO"

    @property
    def is_due(self) -> bool:
        if not self.scheduled or not self.is_pending:
            return False
        return self.scheduled <= datetime.now()


class OrgParser:
    """Parse org files for social media drafts."""

    # Regex patterns - only match level 2+ headings (** or deeper)
    HEADLINE_RE = re.compile(
        r"^\*{2,}\s+"
        r"(TODO|DONE|CANCELLED)?\s*"
        r"(?:\[#([ABC])\])?\s*"
        r"(.+?)\s*$"
    )
    SCHEDULED_RE = re.compile(
        r"SCHEDULED:\s*<(\d{4}-\d{2}-\d{2})"
        r"(?:\s+\w+)?"
        r"(?:\s+(\d{2}:\d{2}))?"
        r">"
    )
    PROPERTY_RE = re.compile(r":(\w+):\s*(.+)")
    PROPERTY_DRAWER_START = ":PROPERTIES:"
    PROPERTY_DRAWER_END = ":END:"

    def __init__(self, filepath: Path | str):
        self.filepath = Path(filepath)
        self.content = self.filepath.read_text()
        self.lines = self.content.split("\n")

    def parse(self) -> list[OrgDraft]:
        """Parse org file and extract drafts."""
        drafts = []
        i = 0

        while i < len(self.lines):
            line = self.lines[i]
            match = self.HEADLINE_RE.match(line)

            if match:
                status = match.group(1) or "TODO"
                priority = match.group(2)
                headline = match.group(3)
                line_number = i

                # Parse following lines for properties and content
                i += 1
                scheduled = None
                platform = "twitter"  # default
                draft_id = None
                content_lines = []
                in_properties = False

                while i < len(self.lines):
                    curr_line = self.lines[i]

                    # Check for next headline
                    if curr_line.startswith("*"):
                        break

                    # Check for SCHEDULED
                    sched_match = self.SCHEDULED_RE.search(curr_line)
                    if sched_match:
                        date_str = sched_match.group(1)
                        time_str = sched_match.group(2) or "00:00"
                        scheduled = datetime.strptime(
                            f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
                        )
                        i += 1
                        continue

                    # Property drawer
                    if self.PROPERTY_DRAWER_START in curr_line:
                        in_properties = True
                        i += 1
                        continue

                    if self.PROPERTY_DRAWER_END in curr_line:
                        in_properties = False
                        i += 1
                        continue

                    if in_properties:
                        prop_match = self.PROPERTY_RE.match(curr_line.strip())
                        if prop_match:
                            key, value = prop_match.groups()
                            if key.upper() == "PLATFORM":
                                platform = value.lower()
                            elif key.upper() == "ID":
                                draft_id = value
                        i += 1
                        continue

                    # Content (skip empty lines at start)
                    stripped = curr_line.strip()
                    if stripped or content_lines:
                        # Skip org-mode directives
                        if not stripped.startswith("#+"):
                            content_lines.append(curr_line)

                    i += 1

                # Clean up content
                content = "\n".join(content_lines).strip()

                if content:  # Only add if there's actual content
                    drafts.append(
                        OrgDraft(
                            headline=headline,
                            status=status,
                            priority=priority,
                            scheduled=scheduled,
                            platform=platform,
                            draft_id=draft_id,
                            content=content,
                            line_number=line_number,
                        )
                    )
            else:
                i += 1

        return drafts

    def update_status(self, draft: OrgDraft, new_status: str) -> None:
        """Update the status of a draft in the org file."""
        line = self.lines[draft.line_number]
        # Replace TODO/DONE/CANCELLED with new status
        if draft.status:
            new_line = line.replace(draft.status, new_status, 1)
        else:
            # Insert status after asterisks
            new_line = re.sub(r"^(\*+\s+)", rf"\1{new_status} ", line)
        self.lines[draft.line_number] = new_line
        self.content = "\n".join(self.lines)
        self.filepath.write_text(self.content)

    def add_property(self, draft: OrgDraft, key: str, value: str) -> None:
        """Add or update a property in the draft's property drawer."""
        # Find property drawer or create one
        i = draft.line_number + 1
        in_properties = False
        property_end = -1

        while i < len(self.lines) and not self.lines[i].startswith("*"):
            if self.PROPERTY_DRAWER_START in self.lines[i]:
                in_properties = True
            elif self.PROPERTY_DRAWER_END in self.lines[i]:
                property_end = i
                break
            elif in_properties:
                # Check if property already exists
                prop_match = self.PROPERTY_RE.match(self.lines[i].strip())
                if prop_match and prop_match.group(1).upper() == key.upper():
                    # Update existing
                    self.lines[i] = f"   :{key}: {value}"
                    self.content = "\n".join(self.lines)
                    self.filepath.write_text(self.content)
                    return
            i += 1

        if property_end > 0:
            # Insert before :END:
            self.lines.insert(property_end, f"   :{key}: {value}")
        else:
            # No property drawer, create one after SCHEDULED line or headline
            insert_pos = draft.line_number + 1
            # Skip SCHEDULED line if present
            if insert_pos < len(self.lines) and "SCHEDULED:" in self.lines[insert_pos]:
                insert_pos += 1
            self.lines.insert(insert_pos, "   :PROPERTIES:")
            self.lines.insert(insert_pos + 1, f"   :{key}: {value}")
            self.lines.insert(insert_pos + 2, "   :END:")

        self.content = "\n".join(self.lines)
        self.filepath.write_text(self.content)


class OrgDraftManager:
    """Manage social media drafts from org files."""

    def __init__(self, filepath: Path | str):
        self.parser = OrgParser(filepath)
        self.filepath = Path(filepath)

    def list_drafts(self, status: str | None = None) -> list[OrgDraft]:
        """List drafts, optionally filtered by status."""
        drafts = self.parser.parse()
        if status:
            drafts = [d for d in drafts if d.status == status.upper()]
        return drafts

    def get_pending(self) -> list[OrgDraft]:
        """Get all pending (TODO) drafts."""
        return self.list_drafts("TODO")

    def get_due(self) -> list[OrgDraft]:
        """Get drafts that are due for posting."""
        return [d for d in self.get_pending() if d.is_due]

    def get_scheduled(self) -> list[OrgDraft]:
        """Get drafts with future scheduled times."""
        now = datetime.now()
        return [d for d in self.get_pending() if d.scheduled and d.scheduled > now]

    def post_draft(self, draft: OrgDraft, dry_run: bool = False) -> dict:
        """Post a single draft."""
        from .twitter import Twitter
        from .linkedin import LinkedIn
        from .reddit import Reddit

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "platform": draft.platform,
                "content": draft.content[:100] + "..."
                if len(draft.content) > 100
                else draft.content,
            }

        # Get appropriate client
        if draft.platform == "twitter":
            client = Twitter()
        elif draft.platform == "linkedin":
            client = LinkedIn()
        elif draft.platform == "reddit":
            client = Reddit()
        else:
            return {"success": False, "error": f"Unknown platform: {draft.platform}"}

        # Post
        result = client.post(draft.content)

        if result.get("success"):
            # Update org file
            self.parser.update_status(draft, "DONE")
            self.parser.add_property(draft, "POSTED_AT", datetime.now().isoformat())
            if result.get("id"):
                self.parser.add_property(draft, "POST_ID", str(result["id"]))
            if result.get("url"):
                self.parser.add_property(draft, "POST_URL", result["url"])

        return result

    def schedule_draft(
        self,
        draft: OrgDraft,
        fluctuation: int = 0,
        fluctuation_bias: str = "none",
    ) -> dict:
        """Schedule a draft using the existing scheduler.

        Args:
            draft: The draft to schedule
            fluctuation: Max random fluctuation in minutes (0=disabled)
            fluctuation_bias: "early", "late", or "none"
        """
        from .scheduler import schedule_post

        if not draft.scheduled:
            return {"success": False, "error": "No scheduled time set"}

        return schedule_post(
            platform=draft.platform,
            text=draft.content,
            schedule_time=draft.scheduled.strftime("%Y-%m-%d %H:%M"),
            fluctuation=fluctuation,
            fluctuation_bias=fluctuation_bias,
            source_file=str(self.filepath),
            headline=draft.headline,
        )

    def post_due(self, dry_run: bool = False) -> list[dict]:
        """Post all drafts that are due."""
        results = []
        for draft in self.get_due():
            result = self.post_draft(draft, dry_run=dry_run)
            result["headline"] = draft.headline
            results.append(result)
        return results

    def schedule_all(
        self,
        dry_run: bool = False,
        fluctuation: int = 0,
        fluctuation_bias: str = "none",
        auto_move: bool = True,
    ) -> list[dict]:
        """Schedule all pending drafts with scheduled times.

        Args:
            dry_run: Preview without actually scheduling
            fluctuation: Max random fluctuation in minutes (0=disabled)
            fluctuation_bias: "early", "late", or "none"
            auto_move: Move file from drafts/ to scheduled/ directory
        """
        from .org_files import move_to_scheduled

        results = []
        scheduled_drafts = self.get_scheduled()

        if not scheduled_drafts:
            return results

        for draft in scheduled_drafts:
            if dry_run:
                result = {
                    "success": True,
                    "dry_run": True,
                    "headline": draft.headline,
                    "platform": draft.platform,
                    "scheduled_for": draft.scheduled.strftime("%Y-%m-%d %H:%M"),
                }
                if fluctuation > 0:
                    result["fluctuation"] = f"±{fluctuation}min"
            else:
                result = self.schedule_draft(
                    draft,
                    fluctuation=fluctuation,
                    fluctuation_bias=fluctuation_bias,
                )
                result["headline"] = draft.headline
            results.append(result)

        # Move file to scheduled/ directory if auto_move enabled
        if not dry_run and auto_move and results:
            all_success = all(r.get("success") for r in results)
            if all_success:
                new_path = move_to_scheduled(self.filepath)
                if new_path and new_path != self.filepath:
                    # Update source_file in scheduler jobs
                    from .scheduler import update_source_path

                    update_source_path(str(self.filepath), str(new_path))
                    for r in results:
                        r["moved_to"] = str(new_path)

        return results

    def status_report(self) -> dict:
        """Generate status report for all drafts."""
        drafts = self.parser.parse()
        pending = [d for d in drafts if d.status == "TODO"]
        done = [d for d in drafts if d.status == "DONE"]
        due = [d for d in pending if d.is_due]
        scheduled = [d for d in pending if d.scheduled and not d.is_due]

        return {
            "file": str(self.filepath),
            "total": len(drafts),
            "pending": len(pending),
            "done": len(done),
            "due_now": len(due),
            "scheduled": len(scheduled),
            "drafts": [
                {
                    "headline": d.headline,
                    "status": d.status,
                    "platform": d.platform,
                    "scheduled": d.scheduled.strftime("%Y-%m-%d %H:%M")
                    if d.scheduled
                    else None,
                    "is_due": d.is_due,
                    "char_count": len(d.content),
                }
                for d in drafts
            ],
        }

    def sync_with_scheduler(
        self,
        fluctuation: int = 0,
        fluctuation_bias: str = "none",
    ) -> dict:
        """Sync org file with scheduler - org file is the source of truth.

        This will:
        1. Cancel jobs that no longer exist in org (removed or marked DONE)
        2. Add new scheduled drafts that aren't in scheduler yet
        3. Update existing jobs if schedule time changed

        Args:
            fluctuation: Max random fluctuation in minutes (0=disabled)
            fluctuation_bias: "early", "late", or "none"

        Returns:
            dict with sync results (added, cancelled, unchanged)
        """
        from .scheduler import _load_schedule, _save_schedule, schedule_post

        # Get org drafts that should be scheduled (by headline as key)
        org_scheduled = {d.headline: d for d in self.get_scheduled()}

        # Get current scheduler jobs for this file (by headline as key)
        jobs = _load_schedule()
        file_jobs = {
            j.get("headline", j.get("id")): j
            for j in jobs
            if j.get("source_file") == str(self.filepath)
            and j.get("status") == "pending"
        }

        added = []
        cancelled = []
        unchanged = []

        # Cancel jobs not in org anymore (or marked DONE)
        for headline, job in file_jobs.items():
            if headline not in org_scheduled:
                job["status"] = "cancelled"
                cancelled.append(job["id"])

        # Add/check org drafts
        for headline, draft in org_scheduled.items():
            if headline in file_jobs:
                # Already scheduled
                unchanged.append(headline)
            else:
                # New - add to scheduler
                result = schedule_post(
                    platform=draft.platform,
                    text=draft.content,
                    schedule_time=draft.scheduled.strftime("%Y-%m-%d %H:%M"),
                    fluctuation=fluctuation,
                    fluctuation_bias=fluctuation_bias,
                    source_file=str(self.filepath),
                    headline=headline,
                    draft_id=draft.draft_id,
                )
                if result.get("success"):
                    added.append(headline)

        # Save cancelled jobs
        if cancelled:
            _save_schedule(jobs)

        return {
            "success": True,
            "file": str(self.filepath),
            "added": added,
            "cancelled": cancelled,
            "unchanged": unchanged,
        }
