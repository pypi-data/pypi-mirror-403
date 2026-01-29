import os
import stat
import tarfile
import logging
import subprocess
import atexit
import time
from typing import List, Optional

from go_judge.utils import ResourceManager
from go_judge.image import RootfsBuilder
from go_judge.client import RemoteSandbox

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("go-judge")


class Sandbox(RemoteSandbox):
    """
    Manages a local go-judge instance (download, environment build, process execution).
    Inherits run() from RemoteSandbox.
    """
    GO_JUDGE_REPO = "criyle/go-judge"
    DEFAULT_PORT = 5050

    def __init__(
        self,
        name: str,
        distribution: str = "alpine",
        release: str = None,
        packages: List[str] = None,
        init_command: str = None,
        port: int = DEFAULT_PORT,
        custom_languages: dict = None,
        max_workers: int = 16
    ):
        super().__init__(f"http://localhost:{port}", custom_languages, max_workers)

        self.name = name
        self.packages = packages or []
        self.init_command = init_command
        self.port = port

        # 1. Setup Architecture & Paths
        self.arch = ResourceManager.get_system_arch()
        ResourceManager.ensure_dirs()

        self.binary_path = ResourceManager.BIN_DIR / "go-judge"
        # New Env Path: .cache/go-judge/env/{name}/rootfs
        self.env_path = ResourceManager.ENV_DIR / self.name
        self.rootfs_path = self.env_path / "rootfs"

        # 2. Initialize Builder
        self.builder = RootfsBuilder(distribution, self.arch, release=release)
        self.server_process: Optional[subprocess.Popen] = None
        self.api_url = f"http://localhost:{self.port}"

        self._server_stdout = None
        self._server_stderr = None

    def start(self):
        """Prepares binary and environment."""
        self._ensure_binary()
        self.builder.build(self.env_path, self.packages, self.init_command)

        if self.server_process and self.server_process.poll() is None:
            logger.info("Server already running.")
            return

        logger.info(f"Starting go-judge server on port {self.port}...")
        # Start go-judge with the config in the env directory
        self._server_stdout = open(self.env_path / "server.stdout", "w")
        self._server_stderr = open(self.env_path / "server.stderr", "w")
        try:
            self.server_process = subprocess.Popen(
                [
                    str(self.binary_path),
                    "-http-addr", f"127.0.0.1:{self.port}",
                    #"-enable-debug"
                ],
                cwd=str(self.env_path),
                stdout=self._server_stdout,
                stderr=self._server_stderr
            )
            atexit.register(self.stop)
            self._wait_for_server()
        except Exception as e:
            self.stop()
            raise e

    def stop(self):
        """Stops the go-judge server."""
        try:
            atexit.unregister(self.stop)
        except Exception:
            pass
        self.close()

        if self.server_process:
            logger.info("Stopping go-judge server...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.server_process.kill()
            self.server_process = None

        if self._server_stdout:
            self._server_stdout.close()
            self._server_stdout = None
        if self._server_stderr:
            self._server_stderr.close()
            self._server_stderr = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def _wait_for_server(self):
        """Polls localhost:port/version until server is ready."""
        retries = 10
        for _ in range(retries):
            if self.server_process.poll() is not None:
                break
            if self.check_health(): # Uses RemoteSandbox.check_health
                logger.info(f"Server is ready at {self.api_url}")
                return
            time.sleep(0.5)

        # If we get here, server failed to start
        error_msg = "Server failed to start."
        
        # Read the logs we just wrote to find out why
        if (self.env_path / "server.stderr").exists():
            with open(self.env_path / "server.stderr", "r") as f:
                stderr_log = f.read().strip()
                if stderr_log:
                    error_msg += f"\n[STDERR]: {stderr_log}"
                    
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    def _ensure_binary(self):
        if self.binary_path.exists():
            return

        import requests
        logger.info(f"Finding go-judge binary for {self.arch}...")

        api_url = f"https://api.github.com/repos/{self.GO_JUDGE_REPO}/releases/latest"
        resp = requests.get(api_url)
        resp.raise_for_status()
        assets = resp.json()['assets']

        search_patterns = []
        if self.arch == "amd64":
            search_patterns = [
                "linux_amd64v2.tar.gz",
                "linux_amd64v3.tar.gz",
            ]
        elif self.arch == "arm64":
            search_patterns = [
                "linux_arm64.tar.gz",
            ]

        download_url = None
        found_name = None

        for pattern in search_patterns:
            for asset in assets:
                # Case insensitive match ensures we catch 'go-judge_X.Y.Z_linux_amd64.tar.gz'
                if pattern in asset['name'].lower():
                    download_url = asset['browser_download_url']
                    found_name = asset['name']
                    break
            if download_url:
                break

        if not download_url:
            raise RuntimeError(
                f"Binary not found for {self.arch}. "
                f"Searched for patterns: {search_patterns} in release assets."
            )

        logger.info(f"Downloading {found_name}...")

        self.binary_path.parent.mkdir(parents=True, exist_ok=True)
        temp_tar = self.binary_path.with_suffix(".tar.gz")

        ResourceManager.download_file(download_url, temp_tar)

        # Extract
        logger.info("Extracting binary...")
        with tarfile.open(temp_tar) as tar:
            found_bin = False
            for member in tar.getmembers():
                # The binary is usually named 'go-judge' inside the tar
                if member.name.endswith("go-judge"):
                    member.name = os.path.basename(member.name)  # Flatten path
                    tar.extract(member, path=self.binary_path.parent)
                    found_bin = True
                    break

            if not found_bin:
                # Fallback: Sometimes it might be named differently?
                # Extract all and let user deal with it? No, fail safe.
                raise RuntimeError(
                    "Could not find 'go-judge' executable inside the downloaded archive.")

        temp_tar.unlink()
        self.binary_path.chmod(self.binary_path.stat().st_mode | stat.S_IEXEC)
