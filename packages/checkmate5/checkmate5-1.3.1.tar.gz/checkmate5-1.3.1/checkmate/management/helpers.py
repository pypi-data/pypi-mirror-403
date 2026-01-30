# -*- coding: utf-8 -*-

import os
import re
import json
import yaml
import fnmatch
from functools import reduce
import argparse
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from checkmate.lib.backend import SQLBackend
from checkmate.helpers.hashing import Hasher

logger = logging.getLogger(__name__)

def get_project_path(path=None):
    if not path:
        path = os.getcwd()
    while path != "/":
        config_path = os.path.join(path, '.checkmate')
        if os.path.exists(config_path) and os.path.isdir(config_path):
            return path
        path = os.path.dirname(path)
    return None

def get_project_config(path):
    with open(os.path.join(path, ".checkmate/config.json"), "r") as config_file:
        return json.loads(config_file.read())

def save_project_config(path, config):
    with open(os.path.join(path, ".checkmate/config.json"), "w") as config_file:
        config_file.write(json.dumps(config))

def get_files_list(path, with_sha=False):
    files = []
    for (dirpath, dirnames, filenames) in os.walk(path):
        for filename in filenames:
            rel_path = (os.path.join(dirpath, filename))[len(path):]
            rel_path = rel_path.lstrip(os.sep)
            if rel_path.startswith(".checkmate" + os.sep) or rel_path == ".checkmate":
                continue
            files.append(rel_path)
    return files

def apply_filter(filename, patterns):
    return reduce(lambda x, y: x or y, [bool(re.search(pattern, filename)) for pattern in patterns], False)

def filter_filenames_by_analyzers(filenames, analyzers, language_patterns):
    filtered_filenames = []
    for filename in filenames:
        for analyzer_params in analyzers:
            if analyzer_params['language'] not in language_patterns:
                continue
            language_pattern = language_patterns[analyzer_params['language']]
            if 'patterns' not in language_pattern or not apply_filter(filename, language_pattern['patterns']):
                continue
            filtered_filenames.append(filename)
            break
    return filtered_filenames

def filter_filenames_by_checkignore(file_paths, checkignore_patterns):
    filtered_file_paths = []
    for file_path in file_paths:
        excluded = False
        always_included = False
        for pattern in checkignore_patterns:
            if pattern.startswith("!") and fnmatch.fnmatch(file_path, pattern[1:]):
                always_included = True
                break
            elif fnmatch.fnmatch(file_path, pattern):
                excluded = True
        if not excluded or always_included:
            filtered_file_paths.append(file_path)
    return filtered_file_paths

def parse_checkmate_settings(content):
    """Parse .yml content and return a dictionary."""
    return yaml.safe_load(content)

def parse_checkignore(content):
    lines = [l for l in (s.strip() for s in content.split("\n")) if l and not l.startswith("#")]
    return lines

def get_project_and_backend(path, settings, echo=False, initialize_db=True):
    project_path = get_project_path(path)
    project_config = get_project_config(project_path)
    backend = get_backend(project_path, project_config, settings, echo=echo, initialize_db=initialize_db)
    project = get_project(project_path, project_config, settings, backend)
    return project, backend

def get_backend(project_path, project_config, settings, echo=False):
    """Return the appropriate backend instance based on the project configuration and settings."""
    backend_config = project_config.get('backend', {})
    backend_type = backend_config.get('driver')
    connection_string = backend_config.get('connection_string', None)

    if backend_type == "sql":
        if not connection_string:
            raise ValueError("Connection string is required for the 'sql' backend.")
        try:
            engine = create_engine(connection_string, echo=echo)
            backend = SQLBackend(engine)
        except ModuleNotFoundError as exc:
            if "psycopg2" in str(exc) or "psycopg" in str(exc):
                fallback_connection = f"sqlite:///{project_path}/database.db"
                logger.warning(
                    "Postgres driver missing; falling back to SQLite at %s",
                    fallback_connection,
                )
                engine = create_engine(fallback_connection, echo=echo)
                backend = SQLBackend(engine)
            else:
                raise
    elif backend_type == "sqlite":
        if not connection_string:
            connection_string = f"sqlite:///{project_path}/database.db"
        engine = create_engine(connection_string, echo=echo)
        backend = SQLBackend(engine)
    else:
        raise ValueError("Unsupported backend type specified.")

    return backend

def get_project(project_path, project_config, settings, backend):
    project_class = project_config.get('project_class', 'Project')
    ProjectClass = settings.models[project_class]

    def _fetch_project():
        project = backend.get(ProjectClass, {'pk': project_config['project_id']})
        if project is None:
            raise ProjectClass.DoesNotExist()
        return project

    try:
        # Try to get the project using its primary key
        project = _fetch_project()

    except ProjectClass.DoesNotExist:
        # If the project doesn't exist, create a new one
        # Create a new instance of ProjectClass.
        # It's good practice to set the 'pk' explicitly if it's derived from your config,
        # otherwise BlitzDB will generate one. Here, we're using project_id as pk.
        project = ProjectClass(project_config)
        project.pk = project_config['project_id'] # Ensure the PK is set to your project_id

        # Save the newly created project
        backend.save(project)

        # If needed, ensure that the project is persisted
        # (Crucial for FileBackend, optional/less critical for MongoBackend as it auto-persists)
        backend.commit()
    except Exception as exc:
        if "fromisoformat" in str(exc) or "argument must be str" in str(exc):
            logger.warning("Detected incompatible datetime serialization; attempting sqlite repair.")
            try:
                if hasattr(backend, "_coerce_datetime_columns"):
                    backend._coerce_datetime_columns(ProjectClass)
            except Exception:
                pass
            try:
                project = _fetch_project()
            except ProjectClass.DoesNotExist:
                project = ProjectClass(project_config)
                project.pk = project_config['project_id']
                backend.save(project)
                backend.commit()
            except Exception:
                raise
        else:
            raise
    
    except ProjectClass.MultipleDocumentsReturned:
        # This case should ideally not happen if 'pk' is truly unique.
        # It means you have multiple documents with the same generated PK (a severe data integrity issue)
        # or you're querying on non-unique fields with get().
        raise # Re-raise the exception or handle appropriately

    if not getattr(project, "configuration", None):
        def _safe_default(value):
            module_name = getattr(value.__class__, "__module__", "")
            if module_name.startswith("blitzdb."):
                return f"{value.__class__.__name__}:<lazy>"
            if hasattr(value, "__dict__"):
                return f"{value.__class__.__name__}"
            return str(value)
        try:
            config_str = json.dumps(project_config, sort_keys=True, default=_safe_default)
        except Exception:
            config_str = str(project_config)
        hasher = Hasher()
        hasher.add(config_str)
        project.configuration = hasher.digest.hexdigest()
        try:
            with backend.transaction():
                backend.update(project, ["configuration"])
        except Exception:
            try:
                backend.save(project)
            except Exception:
                pass

    project.backend = backend
    return project
