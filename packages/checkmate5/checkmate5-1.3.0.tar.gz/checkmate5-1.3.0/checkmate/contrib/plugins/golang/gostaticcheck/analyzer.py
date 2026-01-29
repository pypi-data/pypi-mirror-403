# -*- coding: utf-8 -*-


from checkmate.lib.analysis.base import BaseAnalyzer
from checkmate.helpers.docker_runner import get_image, run_in_docker

import logging
import os
import json


logger = logging.getLogger(__name__)


class GostaticcheckAnalyzer(BaseAnalyzer):
    _cache = {}

    def __init__(self, *args, **kwargs):
        super(GostaticcheckAnalyzer, self).__init__(*args, **kwargs)

    def summarize(self, items):
        pass

    def analyze(self, file_revision):
        issues = []
        code_dir = os.environ.get("CODE_DIR", os.getcwd())
        image = get_image("CHECKMATE_IMAGE_STATICCHECK", "ghcr.io/dominikh/staticcheck:latest")

        cache_key = (code_dir, image)
        if cache_key in self._cache:
            raw = self._cache[cache_key]
        else:
            try:
                raw = run_in_docker(image, ["staticcheck", "-f", "json", "./..."], mount_path=code_dir)
            except Exception:
                raw = b""
            self._cache[cache_key] = raw

        for line in raw.splitlines():
            try:
                issue = json.loads(line)
            except ValueError:
                continue
            try:
                value = issue['location']['line']
                location = (((value, None),
                             (value, None)),)

                if file_revision.path.endswith(".go") and issue.get('location', {}).get('file', '').endswith(file_revision.path):
                    issues.append({
                        'code': issue.get('code'),
                        'location': location,
                        'data': issue.get('message'),
                        'file': file_revision.path,
                        'line': value,
                        'fingerprint': self.get_fingerprint_from_code(file_revision, location, extra_data=issue.get('message'))
                    })
            except Exception:
                continue

        return {'issues': issues}

