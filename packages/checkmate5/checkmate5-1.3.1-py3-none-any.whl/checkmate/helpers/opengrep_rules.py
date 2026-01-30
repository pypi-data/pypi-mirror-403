import logging
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request

logger = logging.getLogger(__name__)

_RULES_SOURCES = [
    ("opengrep", "https://github.com/opengrep/opengrep-rules/archive/refs/heads/main.tar.gz"),
    ("aikido", "https://github.com/AikidoSec/opengrep-rules/archive/refs/heads/main.tar.gz"),
    ("amplify", "https://github.com/amplify-security/opengrep-rules/archive/refs/heads/main.tar.gz"),
]

_OPENGREP_INSTALL_SCRIPT = "https://raw.githubusercontent.com/opengrep/opengrep/main/install.sh"


def ensure_opengrep_rules(dest_root=None):
    """
    Ensure OpenGrep rules are available locally.
    Returns the local rules directory.
    """
    base_dir = dest_root or os.path.expanduser("~/.opengrep/rules")
    os.makedirs(base_dir, exist_ok=True)

    config_paths = []

    def _has_rules(path):
        for root, _, files in os.walk(path):
            for name in files:
                if name.endswith((".yml", ".yaml")):
                    return True
        return False

    for name, url in _RULES_SOURCES:
        rules_dir = os.path.join(base_dir, f"{name}-rules")
        rules_path = os.path.join(rules_dir, "rules")

        if os.path.isdir(rules_path) or os.path.isdir(rules_dir):
            candidate = rules_path if os.path.isdir(rules_path) else rules_dir
            if _has_rules(candidate):
                config_paths.append(candidate)
            else:
                logger.warning("OpenGrep rules dir has no YAML rules: %s", candidate)
            continue

        with tempfile.TemporaryDirectory() as tmpdir:
            archive_path = os.path.join(tmpdir, f"{name}-rules.tar.gz")
            try:
                urllib.request.urlretrieve(url, archive_path)
            except Exception as exc:
                logger.error("Failed to download OpenGrep rules (%s): %s", name, exc)
                continue

            try:
                with tarfile.open(archive_path, "r:gz") as tar:
                    tar.extractall(tmpdir)
            except Exception as exc:
                logger.error("Failed to extract OpenGrep rules (%s): %s", name, exc)
                continue

            extracted_root = os.path.join(tmpdir, f"{name}-rules-main")
            if not os.path.isdir(extracted_root):
                # Fallback to first extracted directory if the name doesn't match
                extracted_root = None
                for entry in os.listdir(tmpdir):
                    candidate = os.path.join(tmpdir, entry)
                    if os.path.isdir(candidate):
                        extracted_root = candidate
                        break
                if extracted_root is None:
                    logger.error("OpenGrep rules archive missing expected root folder (%s).", name)
                    continue

            if os.path.isdir(rules_dir):
                shutil.rmtree(rules_dir, ignore_errors=True)
            shutil.move(extracted_root, rules_dir)

        candidate = rules_path if os.path.isdir(rules_path) else rules_dir
        if _has_rules(candidate):
            config_paths.append(candidate)
        else:
            logger.warning("OpenGrep rules dir has no YAML rules: %s", candidate)

    return config_paths or None


def ensure_opengrep_cli():
    """
    Ensure OpenGrep CLI is installed locally.
    Returns the resolved CLI path if available.
    """
    if os.environ.get("CHECKMATE_OPENGREP_AUTO_INSTALL") == "0":
        return None

    cli_path = os.environ.get(
        "OPENGREP_BIN",
        os.path.expanduser("~/.opengrep/cli/latest/opengrep"),
    )

    if os.path.isfile(cli_path):
        return cli_path

    logger.info("OpenGrep CLI not found; attempting auto-install.")
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "opengrep-install.sh")
        try:
            urllib.request.urlretrieve(_OPENGREP_INSTALL_SCRIPT, script_path)
        except Exception as exc:
            logger.error("Failed to download OpenGrep install script: %s", exc)
            return None

        try:
            os.chmod(script_path, 0o755)
        except Exception:
            pass

        try:
            result = subprocess.run(
                ["bash", script_path],
                check=False,
                capture_output=True,
                text=True,
            )
        except Exception as exc:
            logger.error("Failed to run OpenGrep install script: %s", exc)
            return None

        if result.returncode != 0:
            logger.error("OpenGrep install failed: %s", result.stderr.strip())
            return None

    if os.path.isfile(cli_path):
        return cli_path

    logger.error("OpenGrep CLI install completed but binary not found.")
    return None
