# -*- coding: utf-8 -*-


from checkmate.lib.analysis.base import BaseAnalyzer
from pathlib import Path
import logging
import os
import tempfile
import json
import subprocess

logger = logging.getLogger(__name__)


class Text4shellAnalyzer(BaseAnalyzer):

    def __init__(self, *args, **kwargs):
        super(Text4shellAnalyzer, self).__init__(*args, **kwargs)

    def summarize(self, items):
        pass

    def analyze(self, file_revision):
        issues = []
        base_dir = Path(__file__).resolve().parents[5]
        scanner = str(base_dir / "bin/text4shell-ce/scan_commons_text_versions.py")

        tmpdir = Path("/tmp") / file_revision.project.pk
        tmpdir.mkdir(parents=True, exist_ok=True)
        target_path = tmpdir / file_revision.path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        f = open(target_path, "wb")
        try:
            with f:
                f.write(file_revision.get_file_content())
            try:
                result = subprocess.check_output(
                    ["python3", scanner, str(target_path), "-quiet"]
                )
            except subprocess.CalledProcessError as e:
                result = e.output or b""

            try:
                json_result = json.loads(result)
            except ValueError:
                json_result = {}
                pass

            try:
                line = "1"
                line = int(line)
                location = (((line, line),
                             (line, None)),)

                issues.append({
                    'code': "I001",
                    'location': location,
                    'data': json_result["I001"],
                    'file': file_revision.path,
                    'line': line,
                    'fingerprint': self.get_fingerprint_from_code(file_revision, location, extra_data=json_result["I001"])
                })

            except KeyError:
                pass

        finally:
            os.unlink(f.name)
        return {'issues': issues}
