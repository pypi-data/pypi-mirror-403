import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

from checkmate.management.commands.issues import Command as IssuesCommand
from checkmate.settings import Settings


class _StubBackend:
    def __init__(self, issues):
        self._issues = issues

    def filter(self, cls, query, **kwargs):
        return self._issues if cls.__name__ == "Issue" else []


class IssuesCommandTests(unittest.TestCase):
    def test_issues_json_includes_plugin_and_dedupes(self):
        settings = Settings()
        issues = [
            {"data": "one", "file": "a.js", "line": 10, "analyzer": "opengrep", "severity": "Medium"},
            {"data": "two", "file": "a.js", "line": 10, "analyzer": "bandit", "severity": "Low"},
        ]
        backend = _StubBackend(issues)

        with tempfile.TemporaryDirectory() as tmpdir:
            cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                cmd = IssuesCommand(project=None, settings=settings, backend=backend, args=["--json-output"])
                with redirect_stdout(StringIO()):
                    cmd.run()
                report = json.loads(open(os.path.join(tmpdir, "report.json"), "r").read())
                self.assertEqual(len(report), 1)
                self.assertIn("plugin", report[0])
                self.assertEqual(report[0]["file"], "a.js")
                self.assertEqual(report[0]["line"], 10)
            finally:
                os.chdir(cwd)
