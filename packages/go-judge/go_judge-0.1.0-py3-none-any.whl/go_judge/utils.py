import platform
import logging
import requests
from pathlib import Path
from tqdm import tqdm

logger = logging.getLogger("go-judge.utils")


class ResourceManager:
    """Shared utilities for path management and downloads."""

    # Centralized Cache Path: ~/.cache/go-judge/
    BASE_DIR = Path.home() / ".cache" / "go-judge"
    BIN_DIR = BASE_DIR / "bin"
    ENV_DIR = BASE_DIR / "env"

    @staticmethod
    def get_system_arch() -> str:
        """Normalize platform.machine() to 'amd64' or 'arm64'."""
        machine = platform.machine().lower()
        if machine in ["x86_64", "amd64"]:
            return "amd64"
        elif machine in ["aarch64", "arm64"]:
            return "arm64"
        else:
            raise RuntimeError(f"Unsupported architecture: {machine}")

    @staticmethod
    def ensure_dirs():
        ResourceManager.BIN_DIR.mkdir(parents=True, exist_ok=True)
        ResourceManager.ENV_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def download_file(url: str, dest: Path):
        """Downloads a file with a progress bar."""
        logger.info(f"Downloading {url}...")
        dest.parent.mkdir(parents=True, exist_ok=True)

        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                total = int(r.headers.get('content-length', 0))
                with open(dest, 'wb') as f, tqdm(
                    desc=dest.name,
                    total=total,
                    unit='iB',
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for chunk in r.iter_content(chunk_size=8192):
                        bar.update(f.write(chunk))
        except Exception as e:
            # Clean up partial download on failure
            if dest.exists():
                dest.unlink()
            raise e
