import datetime
import unittest
from contextlib import redirect_stdout
from io import StringIO

from checkmate.management.commands.snapshots import Command as SnapshotsCommand
from checkmate.settings import Settings


class _StubBackend:
    def __init__(self, snapshots):
        self._snapshots = snapshots

    def filter(self, cls, query, **kwargs):
        if cls.__name__ in ("Snapshot", "GitSnapshot"):
            return self._snapshots
        return []


class _Snapshot:
    def __init__(self, pk, created_at):
        self.pk = pk
        self.created_at = created_at


class SnapshotsCommandTests(unittest.TestCase):
    def test_snapshot_datetime_formatting(self):
        settings = Settings()
        snapshots = [
            _Snapshot("a1", datetime.datetime(2026, 1, 2, 3, 4, 5)),
            _Snapshot("b2", 2026),
        ]
        backend = _StubBackend(snapshots)
        cmd = SnapshotsCommand(project=None, settings=settings, backend=backend, args=[])
        out = StringIO()
        with redirect_stdout(out):
            cmd.run()
        output = out.getvalue()
        self.assertIn("a1\t2026-01-02 03:04:05", output)
        self.assertIn("b2\t2026-01-01 00:00:00", output)
