# -*- coding: utf-8 -*-


from checkmate.lib.models import Snapshot, FileRevision, Issue, IssueOccurrence
from checkmate.lib.code import CodeEnvironment
from .base import BaseCommand

from collections import defaultdict

import sys
import os
import random
import os.path
import copy
import json
import time
import datetime
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    options = BaseCommand.options + [
        {
            'name': '--debug-tools',
            'action': 'store_true',
            'dest': 'debug_tools',
            'default': False,
            'help': 'print raw tool JSON output for debugging.',
        }
    ]

    def run(self):

        settings = self.project.settings
        if self.opts.get('debug_tools'):
            os.environ["CHECKMATE_DEBUG_TOOL_OUTPUT"] = "1"

        logger.info("Getting file revisions...")
        file_revisions = self.project.get_disk_file_revisions()
        logger.info("%d file revisions" % len(file_revisions))

        snapshot_class = getattr(self.project, "GitSnapshot", Snapshot)
        snapshot = snapshot_class({'created_at': datetime.datetime.now()})

        try:
            code_environment = CodeEnvironment(self.project,
                                               global_settings=self.settings,
                                               project_settings=settings,
                                               file_revisions=file_revisions)
            code_environment.analyze(file_revisions,
                                     snapshot=snapshot,
                                     save_if_empty=False)
        except KeyboardInterrupt:
            raise
