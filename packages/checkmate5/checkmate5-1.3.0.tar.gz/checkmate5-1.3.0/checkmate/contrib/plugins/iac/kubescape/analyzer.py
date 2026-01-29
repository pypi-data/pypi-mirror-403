# -*- coding: utf-8 -*-


from checkmate.lib.analysis.base import BaseAnalyzer
from checkmate.helpers.docker_runner import get_image, run_json_tool

import logging
import os

logger = logging.getLogger(__name__)


class KubescapeAnalyzer(BaseAnalyzer):

    def summarize(self, items):
        pass

    def analyze(self, file_revision):
        issues = []
        code_dir = os.environ.get("CODE_DIR", os.getcwd())
        image = get_image("CHECKMATE_IMAGE_KUBESCAPE", "quay.io/armosec/kubescape:latest")

        try:
            json_result = run_json_tool(image, ["kubescape", "scan", "/workspace", "--format", "json"], mount_path=code_dir)
        except Exception:
            json_result = {}

        for result in json_result.get('results', []):
            for control in result.get('controls', []):
                controlkey = control.get('controlID')
                sev = json_result.get('summaryDetails', {}).get('controls', {}).get(controlkey, {}).get('scoreFactor', 0)
                if sev >= 7:
                    severity = "High"
                elif sev >= 4:
                    severity = "Medium"
                else:
                    severity = "Warning"

                line = 1
                location = (((line, None),
                             (line, None)),)

                issues.append({
                    'code': control.get('controlID'),
                    'severity': severity,
                    'location': location,
                    'data': control.get('name'),
                    'file': file_revision.path,
                    'line': line,
                    'fingerprint': self.get_fingerprint_from_code(file_revision, location, extra_data=control.get('name'))
                })

        return {'issues': issues}
