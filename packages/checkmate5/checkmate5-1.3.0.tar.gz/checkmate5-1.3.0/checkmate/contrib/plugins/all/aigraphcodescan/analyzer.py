# -*- coding: utf-8 -*-


from checkmate.lib.analysis.base import BaseAnalyzer
from checkmate.helpers.docker_runner import get_image, run_json_tool

import logging
import os
import re


logger = logging.getLogger(__name__)


class AiGraphCodeScanAnalyzer(BaseAnalyzer):

    def __init__(self, *args, **kwargs):
        super(AiGraphCodeScanAnalyzer, self).__init__(*args, **kwargs)

    def summarize(self, items):
        pass

    def analyze(self, file_revision):
        issues = []
        code_dir = os.environ.get("CODE_DIR", os.getcwd())
        image = get_image("CHECKMATE_IMAGE_AIGRAPH", "betterscan/aigraphcodescan:latest")

        try:
            json_result = run_json_tool(image, ["aigraphcodescan", "--directory", "/workspace"], mount_path=code_dir)
        except Exception:
            json_result = []

        for issue in json_result or []:
            value = issue.get('line')
            location = (((value, None),
                         (value, None)),)

            string = issue.get("description", "")
            string = string.replace("'", "").replace("`", "").replace("\"", "").strip()
            string = re.sub('[^A-Za-z0-9 ]+', '', string)

            issues.append({
                'code': "I001",
                'location': location,
                'data': string,
                'file': file_revision.path,
                'line': value,
                'fingerprint': self.get_fingerprint_from_code(file_revision, location, extra_data=string)
            })

        return {'issues': issues}

