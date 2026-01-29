# -*- coding: utf-8 -*-


from .base import BaseCommand
from checkmate.lib.models import Snapshot
from checkmate.contrib.plugins.git.models import GitSnapshot
import logging
import datetime

"""
$ checkmate stats python:metrics -- --hierarchy

"""

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def run(self):
        snapshots = []
        DiskSnapshot = getattr(self.project, "DiskSnapshot", None)
        if DiskSnapshot is not None:
            try:
                snapshots.extend(list(self.backend.filter(DiskSnapshot, {})))
            except Exception:
                pass
        try:
            snapshots.extend(list(self.backend.filter(GitSnapshot, {})))
        except Exception:
            pass
        try:
            snapshots.extend(list(self.backend.filter(Snapshot, {})))
        except Exception:
            pass

        if not snapshots:
            try:
                import sqlite3
                engine = getattr(self.backend, "engine", None) or getattr(self.backend.backend, "engine", None)
                db_path = None
                if engine and engine.url and engine.url.database:
                    db_path = engine.url.database
                if db_path:
                    conn = sqlite3.connect(db_path)
                    cur = conn.cursor()
                    rows = cur.execute("select pk, created_at from snapshot order by created_at desc").fetchall()
                    conn.close()
                    for pk, created_at in rows:
                        print(f"{pk}\t{created_at}")
                    if rows:
                        return 0
            except Exception:
                pass
            print("No snapshots found.")
            return 0

        snapshots = sorted(
            snapshots,
            key=lambda s: getattr(s, 'created_at', 0),
            reverse=True,
        )

        def _format_time(value):
            if isinstance(value, (datetime.datetime, datetime.date)):
                return value.strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(value, (int, float)):
                if 1900 <= value <= 3000:
                    return f"{int(value):04d}-01-01 00:00:00"
                try:
                    return datetime.datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    return str(value)
            return str(value) if value is not None else ""

        for snap in snapshots:
            snap_id = getattr(snap, 'pk', None)
            snap_time = getattr(snap, 'created_at', None) or getattr(snap, 'committer_date', None)
            print(f"{snap_id}\t{_format_time(snap_time)}")

        return 0
