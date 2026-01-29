# -*- coding: utf-8 -*-


from checkmate.lib.analysis.base import BaseAnalyzer

import logging
import os
import tempfile
import json
import subprocess

logger = logging.getLogger(__name__)


class GrauditAnalyzer(BaseAnalyzer):

    def __init__(self, *args, **kwargs):
        super(GrauditAnalyzer, self).__init__(*args, **kwargs)

    def summarize(self, items):
        pass

    def analyze(self, file_revision):
        issues = []
        result = ""
        # Write in binary mode; normalize string content to bytes and suppress write errors.
        f = tempfile.NamedTemporaryFile(delete=False, mode="wb")
        try:
            with f:
                try:
                    content = file_revision.get_file_content()
                    if isinstance(content, str):
                        content = content.encode("utf-8", "ignore")
                    f.write(content)
                except (UnicodeDecodeError, TypeError, ValueError):
                    # If content is not writable, skip gracefully.
                    pass
            try:
                result = subprocess.check_output(["/root/graudit/graudit",
                                                  "-d",
                                                  "/root/graudit/signatures/perl.db",
                                                  f.name],
                                                  stderr=subprocess.DEVNULL).strip()
            except subprocess.CalledProcessError as e:
                pass
            try:
                json_result = json.loads(result)
            except ValueError:
                json_result = {}
                pass

            try:
                for issue in json_result:
                  line = issue["line"]
                  line = int(line)
                  location = (((line, line),
                             (line, None)),)

                  if ".pl" in file_revision.path:
                    issues.append({
                      'code': "I001",
                      'location': location,
                      'data': issue["data"],
                      'file': file_revision.path,
                      'line': line,
                      'fingerprint': self.get_fingerprint_from_code(file_revision, location, extra_data=issue["data"])
                    })

            except KeyError:
                pass

        finally:
            os.unlink(f.name)
        return {'issues': issues}
