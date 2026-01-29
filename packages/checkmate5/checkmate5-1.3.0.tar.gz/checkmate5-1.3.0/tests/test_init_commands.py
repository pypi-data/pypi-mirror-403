import json
import os
import tempfile
import unittest

from sqlalchemy import create_engine

from checkmate.lib.backend import SQLBackend
from checkmate.lib.models import Project
from checkmate.settings import Settings
from checkmate.management.commands.init import Command as InitCommand
from checkmate.contrib.plugins.git.commands.init import Command as GitInitCommand
from checkmate.contrib.plugins.git.models import GitRepository


class InitCommandTests(unittest.TestCase):
    def test_init_default_sqlite_creates_config(self):
        settings = Settings()
        with tempfile.TemporaryDirectory() as tmpdir:
            cmd = InitCommand(project=None, settings=settings, backend=None, args=["--path", tmpdir])
            result = cmd.run()
            self.assertEqual(result, 0)

            config_path = os.path.join(tmpdir, ".checkmate", "config.json")
            self.assertTrue(os.path.exists(config_path))
            config = json.loads(open(config_path, "r").read())
            self.assertEqual(config["backend"]["driver"], "sqlite")
            self.assertIn(".checkmate/database.db", config["backend"]["connection_string"])

    def test_init_sql_backend_creates_config(self):
        settings = Settings()
        with tempfile.TemporaryDirectory() as tmpdir:
            conn = "postgresql+psycopg2://user:pass@localhost/db"
            cmd = InitCommand(
                project=None,
                settings=settings,
                backend=None,
                args=["--path", tmpdir, "--backend", "sql", "--backend-opts", conn],
            )
            result = cmd.run()
            self.assertEqual(result, 0)

            config_path = os.path.join(tmpdir, ".checkmate", "config.json")
            config = json.loads(open(config_path, "r").read())
            self.assertEqual(config["backend"]["driver"], "sql")
            self.assertEqual(config["backend"]["connection_string"], conn)

    def test_git_init_saves_repository(self):
        settings = Settings()
        with tempfile.TemporaryDirectory() as tmpdir:
            os.makedirs(os.path.join(tmpdir, ".git"))
            db_path = os.path.join(tmpdir, "test.db")
            backend = SQLBackend(create_engine(f"sqlite:///{db_path}"))

            project = Project({"project_id": "test"})
            project.pk = "test"
            backend.save(project)
            backend.commit()
            project.backend = backend

            cmd = GitInitCommand(project=project, settings=settings, backend=backend, args=["--path", tmpdir])
            result = cmd.run()
            self.assertIsNone(result)

            repos = list(backend.filter(GitRepository, {}))
            self.assertEqual(len(repos), 1)
            self.assertEqual(repos[0].path, tmpdir)
