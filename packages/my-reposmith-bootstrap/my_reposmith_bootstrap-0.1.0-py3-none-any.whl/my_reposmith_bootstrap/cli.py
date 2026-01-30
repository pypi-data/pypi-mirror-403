from __future__ import annotations

import subprocess
import sys

# RepoSmith (Forgejo) package index (simple)
FORGEJO_SIMPLE = "https://git.mystrotamer.com/api/packages/reposmith/pypi/simple"
PYPI_SIMPLE = "https://pypi.org/simple"

# LOCKED VERSIONS (Governed)
CORE_VERSION = "1.0.0"
EXT_VERSION = "0.1.0"
CLI_VERSION = "0.0.1"

def _run_pip(*pip_args: str) -> None:
    """
    Execute a pip command with the specified arguments.

    Args:
        *pip_args (str): Arguments to pass to pip.

    Raises:
        subprocess.CalledProcessError: If the pip command fails.
    """
    subprocess.check_call([sys.executable, "-m", "pip", *pip_args])

def main() -> int:
    """
    Install the RepoSmith packages with pinned versions using pip.

    Returns:
        int: 0 if the installation was successful, otherwise the error code.
    """
    try:
        # Upgrade pip within the current environment only
        _run_pip("install", "-U", "pip", "--disable-pip-version-check", "--no-input")

        # Install core package with locked version
        _run_pip(
            "install",
            f"reposmith-core=={CORE_VERSION}",
            "--index-url", FORGEJO_SIMPLE,
            "--extra-index-url", PYPI_SIMPLE,
            "--disable-pip-version-check",
            "--no-input",
        )

        # Install extensions package with locked version
        _run_pip(
            "install",
            f"reposmith-extensions=={EXT_VERSION}",
            "--index-url", FORGEJO_SIMPLE,
            "--extra-index-url", PYPI_SIMPLE,
            "--disable-pip-version-check",
            "--no-input",
        )

        # Install CLI package with locked version and no dependencies
        _run_pip(
            "install",
            f"reposmith-cli=={CLI_VERSION}",
            "--no-deps",
            "--index-url", FORGEJO_SIMPLE,
            "--extra-index-url", PYPI_SIMPLE,
            "--disable-pip-version-check",
            "--no-input",
        )

        print("RepoSmith bootstrap complete.")
        print("Try: reposmith version | reposmith --help")
        return 0

    except subprocess.CalledProcessError as e:
        print("RepoSmith bootstrap failed.")
        print(f"Exit code: {e.returncode}")
        print(f"Index: {FORGEJO_SIMPLE}")
        return int(e.returncode)