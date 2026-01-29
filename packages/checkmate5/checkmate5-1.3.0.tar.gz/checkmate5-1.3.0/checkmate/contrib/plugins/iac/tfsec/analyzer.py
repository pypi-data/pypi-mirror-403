# -*- coding: utf-8 -*-


from checkmate.lib.analysis.base import BaseAnalyzer
from checkmate.helpers.docker_runner import get_image, run_json_tool

import logging
import os

logger = logging.getLogger(__name__)


class TfsecAnalyzer(BaseAnalyzer):

    def summarize(self, items):
        pass

    def analyze(self, file_revision):
        issues = []
        code_dir = os.environ.get("CODE_DIR", os.getcwd())
        image = get_image("CHECKMATE_IMAGE_TFSEC", "aquasec/tfsec:latest")

        try:
            json_result = run_json_tool(image, ["tfsec", "--format", "json", "/workspace"], mount_path=code_dir)
        except Exception:
            json_result = {}

        for issue in json_result.get('results', []):
            line = issue.get('location', {}).get('start_line')
            location = (((line, None),
                         (line, None)),)
            issues.append({
                'code': issue.get('rule_id'),
                'location': location,
                'data': issue.get('rule_description'),
                'file': issue.get('location', {}).get('filename', file_revision.path),
                'line': line,
                'fingerprint': self.get_fingerprint_from_code(file_revision, location, extra_data=issue.get('rule_description'))
            })

        return {'issues': issues}
