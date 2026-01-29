# -*- coding: utf-8 -*-

from checkmate.lib.analysis.base import BaseAnalyzer
from checkmate.helpers.opengrep_rules import ensure_opengrep_rules, ensure_opengrep_cli

import json
import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)


def _get_opengrep_bin():
    return os.environ.get(
        "OPENGREP_BIN",
        os.path.expanduser("~/.opengrep/cli/latest/opengrep"),
    )


def _run_opengrep_json(args, code_dir):
    cli_path = _get_opengrep_bin()
    if not os.path.isfile(cli_path):
        cli_path = ensure_opengrep_cli() or cli_path
    cmd = [cli_path] + args
    if os.environ.get("CHECKMATE_DEBUG_TOOL_OUTPUT") == "1":
        logger.info("OpenGrep command: %s", " ".join(cmd))
    env = os.environ.copy()
    env.setdefault("SEMGREP_LOG_FILE", os.path.join(tempfile.gettempdir(), "opengrep.log"))
    try:
        result = subprocess.run(
            cmd,
            cwd=code_dir,
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
    except subprocess.TimeoutExpired:
        logger.error("OpenGrep timed out after 120s: %s", " ".join(cmd))
        return {}
    except FileNotFoundError:
        logger.error("OpenGrep binary not found. Install it or set OPENGREP_BIN.")
        return {}

    if result.returncode != 0:
        if os.environ.get("CHECKMATE_DEBUG_TOOL_OUTPUT") == "1":
            logger.warning("OpenGrep failed (%s): %s", result.returncode, result.stderr.strip())
            if result.stdout:
                logger.info("OpenGrep stdout: %s", result.stdout.strip())
        else:
            logger.debug("OpenGrep failed: %s", result.stderr.strip())
        return {}

    try:
        parsed = json.loads(result.stdout or "{}")
        if os.environ.get("CHECKMATE_DEBUG_TOOL_OUTPUT") == "1":
            logger.info("OpenGrep raw output: %s", json.dumps(parsed, indent=2))
        return parsed
    except Exception:
        if os.environ.get("CHECKMATE_DEBUG_TOOL_OUTPUT") == "1":
            logger.warning("OpenGrep output was not valid JSON. stderr: %s", result.stderr.strip())
            if result.stdout:
                logger.info("OpenGrep stdout: %s", result.stdout.strip())
        else:
            logger.debug("OpenGrep output was not valid JSON. stderr: %s", result.stderr.strip())
        return {}


def _merge_results(base, extra):
    if not isinstance(base, dict):
        base = {}
    if not isinstance(extra, dict):
        return base
    base_results = base.get("results", []) or []
    extra_results = extra.get("results", []) or []
    base["results"] = base_results + extra_results
    return base


class OpengrepAnalyzer(BaseAnalyzer):
    def summarize(self, items):
        pass

    def analyze(self, file_revision):
        issues = []
        code_dir = os.environ.get("CODE_DIR", os.getcwd())
        rules_dirs = ensure_opengrep_rules() or []
        config = os.environ.get("CHECKMATE_OPENGREP_CONFIG")
        target = os.path.join(code_dir, file_revision.path.lstrip("/"))
        config_args = []
        if config:
            config_args = ["--config", config]
        else:
            ext = os.path.splitext(file_revision.path)[1].lower()
            lang_dirs = {
                ".bash": ["bash", "generic"],
                ".php": ["php", "generic"],
                ".js": ["javascript", "generic"],
                ".ts": ["typescript", "generic"],
                ".java": ["java", "generic"],
                ".jsp": ["java", "generic"],
                ".scala": ["scala", "generic"],
                ".py": ["python", "generic"],
                ".rb": ["ruby", "generic"],
                ".go": ["go", "generic"],
                ".yml": ["yaml", "generic"],
                ".yaml": ["yaml", "generic"],
                ".tf": ["terraform", "generic"],
                ".cs": ["csharp", "generic"],
                ".c": ["c/lang", "generic"],
                ".h": ["c/lang", "generic"],
                ".cc": ["c/lang", "generic"],
                ".cpp": ["c/lang", "generic"],
                ".cxx": ["c/lang", "generic"],
                ".hh": ["c/lang", "generic"],
                ".hpp": ["c/lang", "generic"],
                ".html": ["html", "generic"],
                ".htm": ["html", "generic"],
                ".json": ["json", "generic"],
                ".kt": ["kotlin", "generic"],
                ".kts": ["kotlin", "generic"],
                ".clj": ["clojure", "generic"],
                ".cljs": ["clojure", "generic"],
                ".cljc": ["clojure", "generic"],
                ".ml": ["ocaml/lang", "generic"],
                ".mli": ["ocaml/lang", "generic"],
                ".rs": ["rust/lang/security", "generic"],
                ".swift": ["swift", "generic"],
                ".sol": ["solidity", "generic"],
            }.get(ext, ["generic"])

            for rules_dir in rules_dirs:
                for lang_dir in lang_dirs:
                    candidate = os.path.join(rules_dir, lang_dir)
                    if os.path.isdir(candidate):
                        config_args.extend(["--config", candidate])
                if not config_args and os.path.isdir(rules_dir):
                    # fallback to entire rules dir if no specific match
                    config_args.extend(["--config", rules_dir])

        if os.environ.get("CHECKMATE_DEBUG_TOOL_OUTPUT") == "1":
            logger.info(
                "OpenGrep config for %s: %s",
                file_revision.path,
                [arg for arg in config_args if arg != "--config"],
            )

        # First run OpenGrep auto-detection
        json_result = _run_opengrep_json(
            ["scan", "--config", "auto", "--exclude", ".git/**", "--exclude", ".checkmate/**", "--no-git-ignore", "--json", target],
            code_dir,
        )

        # Then run repo rule sets if available or explicitly configured
        if config_args:
            json_result = _merge_results(
                json_result,
                _run_opengrep_json(
                    ["scan", *config_args, "--exclude", ".git/**", "--exclude", ".checkmate/**", "--no-git-ignore", "--json", target],
                    code_dir,
                ),
            )

        for issue in json_result.get("results", []):
            location = (
                ((issue.get("start", {}).get("line"), None), (issue.get("start", {}).get("line"), None)),
            )
            val = (issue.get("check_id") or "").replace("root.", "")
            val = val.title().replace("_", "")

            issues.append(
                {
                    "code": val,
                    "location": location,
                    "data": issue.get("extra", {}).get("message"),
                    "file": file_revision.path,
                    "line": issue.get("start", {}).get("line"),
                    "fingerprint": self.get_fingerprint_from_code(
                        file_revision, location, extra_data=issue.get("extra", {}).get("message")
                    ),
                }
            )

        return {"issues": issues}
