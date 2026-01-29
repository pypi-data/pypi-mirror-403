import os
import tempfile
import unittest

from checkmate.helpers.opengrep_rules import ensure_opengrep_cli


class OpenGrepCliTests(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_auto_install_disabled_returns_none(self):
        os.environ["CHECKMATE_OPENGREP_AUTO_INSTALL"] = "0"
        os.environ.pop("OPENGREP_BIN", None)
        self.assertIsNone(ensure_opengrep_cli())

    def test_existing_cli_path_is_used(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cli_path = os.path.join(tmpdir, "opengrep")
            with open(cli_path, "w") as handle:
                handle.write("#!/bin/sh\n")
            os.chmod(cli_path, 0o755)
            os.environ["OPENGREP_BIN"] = cli_path
            os.environ.pop("CHECKMATE_OPENGREP_AUTO_INSTALL", None)
            self.assertEqual(ensure_opengrep_cli(), cli_path)
