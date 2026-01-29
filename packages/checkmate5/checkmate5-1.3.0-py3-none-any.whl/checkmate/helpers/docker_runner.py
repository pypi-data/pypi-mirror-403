import os
import subprocess
import json
from typing import List, Dict, Optional


_pulled_images = set()


def get_image(env_var: str, default: str) -> str:
    return os.environ.get(env_var, default)


def ensure_image(image: str):
    if image in _pulled_images:
        return
    subprocess.run(["docker", "pull", image], check=False)
    _pulled_images.add(image)


def run_in_docker(
    image: str,
    command: List[str],
    mount_path: Optional[str] = None,
    workdir: str = "/workspace",
    env: Optional[Dict[str, str]] = None,
) -> bytes:
    """
    Run a command in a docker container, mounting mount_path at /workspace (read-only).
    Returns stdout as bytes.
    """
    ensure_image(image)
    mounts = []
    if mount_path:
        mounts.extend(["-v", f"{mount_path}:/workspace:ro"])
    env_args = []
    if env:
        for k, v in env.items():
            env_args.extend(["-e", f"{k}={v}"])
    cmd = ["docker", "run", "--rm"] + mounts + env_args + ["-w", workdir, image] + command
    return subprocess.check_output(cmd, stderr=subprocess.DEVNULL)


def run_json_tool(image: str, command: List[str], mount_path: str) -> Dict:
    """
    Convenience wrapper for tools that emit JSON to stdout.
    """
    raw = run_in_docker(image, command, mount_path=mount_path)
    try:
        return json.loads(raw)
    except Exception:
        return {}


