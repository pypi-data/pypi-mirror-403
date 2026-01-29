# -*- coding: utf-8 -*-


from checkmate.lib.analysis.base import BaseAnalyzer
from checkmate.helpers.docker_runner import get_image, run_json_tool

import logging
import os

logger = logging.getLogger(__name__)


class BanditAnalyzer(BaseAnalyzer):
    _cache = {}

    def summarize(self, items):
        pass

    def analyze(self, file_revision):
        issues = []
        code_dir = os.environ.get("CODE_DIR", os.getcwd())
        image = get_image("CHECKMATE_IMAGE_BANDIT", "pycqa/bandit:latest")

        cache_key = (code_dir, image)
        if cache_key in self._cache:
            json_result = self._cache[cache_key]
        else:
            try:
                json_result = run_json_tool(
                    image,
                    ["bandit", "-r", "/workspace", "-f", "json", "-x", "/workspace/.git,/workspace/.checkmate"],
                    mount_path=code_dir,
                )
            except Exception:
                json_result = {}
            self._cache[cache_key] = json_result

        for issue in json_result.get('results', []):
            location = (((issue.get('line_number'), None),
                         (issue.get('line_number'), None)),)
            if file_revision.path.endswith(".py") and issue.get('filename', '').endswith(file_revision.path):
                issues.append({
                    'code': issue.get('test_id'),
                    'location': location,
                    'data': issue.get('issue_text'),
                    'file': file_revision.path,
                    'line': issue.get('line_number'),
                    'fingerprint': self.get_fingerprint_from_code(file_revision, location, extra_data=issue.get('issue_text'))
                })

        return {'issues': issues}
