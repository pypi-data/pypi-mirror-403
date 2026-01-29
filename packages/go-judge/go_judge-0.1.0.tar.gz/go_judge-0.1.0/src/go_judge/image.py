import shutil
import tarfile
import logging
import subprocess
from pathlib import Path
from typing import List
import requests

from go_judge.utils import ResourceManager

logger = logging.getLogger("go-judge.image")


class RootfsBuilder:
    """Manages the creation and initialization of root filesystems."""

    DISTRO_CONFIG = {
        "alpine": {
            "lxc_params": {"distro": "alpine", "release": "3.23", "variant": "default"},
            "install_cmd": "apk add --no-cache {packages}",
            "init_shell": "/bin/sh",
        },
        "arch": {
            "lxc_params": {"distro": "archlinux", "release": "current", "variant": "default"},
            # Arch requires keyring initialization before installing packages
            "install_cmd": (
                "pacman-key --init && "
                "pacman-key --populate archlinux && "
                "pacman -Sy --noconfirm {packages}"
            ),
            "init_shell": "/bin/bash",
        },
        "debian": {
            "lxc_params": {"distro": "debian", "release": "trixie", "variant": "default"},
            "install_cmd": (
                "export DEBIAN_FRONTEND=noninteractive && "
                "apt-get update && "
                "apt-get install -y {packages}"
            ),
            "init_shell": "/bin/bash",
        },
        "fedora": {
            "lxc_params": {"distro": "fedora", "release": "43", "variant": "default"},
            "install_cmd": "dnf install -y {packages}",
            "init_shell": "/bin/bash",
        }
    }

    def __init__(self, distro: str, arch: str, release: str = None):
        """
        Args:
            distro: "alpine", "debian", "fedora", "arch"
            arch: "amd64" or "arm64"
            release: Specific release version (e.g., "bookworm", "3.21"). 
                     If None, uses the default from DISTRO_CONFIG.
        """
        self.distro = distro.lower()
        self.arch = arch
        if self.distro not in self.DISTRO_CONFIG:
            raise ValueError(f"Unsupported distribution: {distro}")
        self.config = self.DISTRO_CONFIG[self.distro].copy()
        # Override release if provided
        if release:
            self.config["lxc_params"] = self.config["lxc_params"].copy()
            self.config["lxc_params"]["release"] = release

    def build(self, env_path: Path, packages: List[str] = None, post_init_cmd: str = None):
        """
        Orchestrates the build process: Download -> Extract -> Configure -> Install.
        """
        target_rootfs = env_path / "rootfs"
        if (env_path / "mount.yaml").exists():
            logger.info(f"Environment ready at {env_path}")
            return

        logger.info(f"Building {self.distro}/{self.arch} environment...")

        # 1. Download Base Image
        tar_path = self._get_base_image()

        # 2. Extract
        if not target_rootfs.exists():
            logger.info(f"Extracting to {target_rootfs}...")
            target_rootfs.mkdir(parents=True, exist_ok=True)
            with tarfile.open(tar_path) as tar:
                tar.extractall(path=target_rootfs)

        # 3. System Config (DNS, APT/Pacman fixes)
        self._configure_system(target_rootfs)

        # 4. Install Packages (Moved from Sandbox)
        if packages:
            logger.info(f"Installing packages: {packages}")
            cmd = self.config["install_cmd"].format(
                packages=" ".join(packages))
            self._exec_in_unshare(target_rootfs, cmd)

        # 5. User Init (Moved from Sandbox)
        if post_init_cmd:
            logger.info("Running init command...")
            self._exec_in_unshare(target_rootfs, post_init_cmd)

        # 6. Create Configuration
        self._create_mount_config(env_path)

    def _create_mount_config(self, env_path: Path):
        """Generates the mount.yaml for go-judge."""
        content = """mount:
  # Basic binaries and libraries
  - type: bind
    source: rootfs/bin
    target: /bin
    readonly: true
  - type: bind
    source: rootfs/lib
    target: /lib
    readonly: true
  - type: bind
    source: rootfs/lib64
    target: /lib64
    readonly: true
  - type: bind
    source: rootfs/usr
    target: /usr
    readonly: true
  - type: bind
    source: rootfs/etc
    target: /etc
    readonly: true
  - type: bind
    source: rootfs/var
    target: /var
    readonly: true
  # devices
  - type: bind
    source: /dev/null
    target: /dev/null
  - type: bind
    source: /dev/urandom
    target: /dev/urandom
  - type: bind
    source: /dev/random
    target: /dev/random
  - type: bind
    source: /dev/zero
    target: /dev/zero
  - type: bind
    source: /dev/full
    target: /dev/full
  # work dir
  - type: tmpfs
    target: /w
    data: size=128m,nr_inodes=4k
  # tmp dir
  - type: tmpfs
    target: /tmp
    data: size=128m,nr_inodes=4k
proc: true
workDir: /w
hostName: go-judge
domainName: go-judge
uid: 1536
gid: 1536"""
        (env_path / "mount.yaml").write_text(content)

    def _exec_in_unshare(self, rootfs_path: Path, cmd: str):
        """Executes a shell command INSIDE the rootless container."""
        real_cmd = [
            "unshare", "-r", "--fork", "--pid", "--mount-proc",
            "-R", str(rootfs_path.absolute()),
            "/bin/sh", "-c"
        ]

        inner_script = f"""
        export HOME=/root
        export USER=root
        export LOGNAME=root
        export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

        {cmd}
        """
        real_cmd.append(inner_script)
        process = subprocess.Popen(
            real_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout so we see errors in-line
            text=True,                 # Auto-decode bytes to string
            bufsize=1                  # Line buffered
        )

        # Read the stream line-by-line
        for line in process.stdout:
            # We strip() because logger adds its own newline
            logger.info(f"  [build] {line.strip()}")

        # Wait for exit
        return_code = process.wait()
        
        if return_code != 0:
            logger.error(f"❌ Command failed with exit code {return_code}")
            raise RuntimeError(f"Sandbox command failed: {cmd}")

    def get_setup_commands(self, packages: List[str], custom_cmd: str) -> List[str]:
        """Returns the list of shell commands to run inside unshare to finalize setup."""
        cmds = []
        if packages:
            install_cmd = self.config["install_cmd"].format(
                packages=" ".join(packages))
            cmds.append(install_cmd)
        if custom_cmd:
            cmds.append(custom_cmd)
        return cmds

    def _get_base_image(self) -> Path:
        """Resolves URL and downloads the base image tarball."""
        params = self.config["lxc_params"]
        # Check cache for base image (e.g., ~/.cache/go-judge/debian_amd64.tar.xz)
        base_name = f"{self.distro}_{params['release']}_{self.arch}_base.tar.xz"
        cache_path = ResourceManager.BASE_DIR / base_name

        if cache_path.exists():
            return cache_path

        params = self.config["lxc_params"]
        # Resolve URL
        url = self._resolve_lxc_url(
            distro=params["distro"], 
            release=params["release"], 
            arch=self.arch, # LXC server uses standardized 'amd64'/'arm64' for all distros
            variant=params["variant"]
        )

        ResourceManager.download_file(url, cache_path)
        return cache_path

    def _resolve_lxc_url(self, distro: str, release: str, arch: str, variant: str) -> str:
        """
        Fetches the lightweight LXC metadata index to find the image URL.
        Endpoint: https://images.linuxcontainers.org/meta/1.0/index-system
        Format: distro;version;arch;variant;build_id;path
        """
        META_URL = "https://images.linuxcontainers.org/meta/1.0/index-system"
        BASE_URL = "https://images.linuxcontainers.org"

        logger.info(f"Fetching image index from {META_URL}...")
        resp = requests.get(META_URL)
        resp.raise_for_status()

        # Parse the CSV-like content
        # We want to find the *latest* build for our target.
        # The list is usually sorted, but we should parse carefully.

        matching_builds = []

        for line in resp.text.splitlines():
            parts = line.strip().split(";")
            if len(parts) < 6:
                continue

            p_distro, p_rel, p_arch, p_variant, p_build, p_path = parts[:6]

            if (p_distro == distro and
                p_rel == release and
                p_arch == arch and
                    p_variant == variant):
                matching_builds.append((p_build, p_path))

        if not matching_builds:
            raise RuntimeError(
                f"No image found for {distro}/{release}/{arch}/{variant}")

        # Sort by build ID (date string) descending to get the latest
        # Build IDs are YYYYMMDD_HH:MM, so string sort works perfectly.
        latest_build = sorted(matching_builds, key=lambda x: x[0])[-1]

        # The path in the index usually points to the directory, not the file.
        # e.g., /images/debian/bookworm/amd64/default/20250124_07:42/
        # We need to append 'rootfs.tar.xz'
        rel_path = latest_build[1]
        full_url = f"{BASE_URL}/{rel_path.strip('/')}/rootfs.tar.xz"

        logger.info(f"Resolved latest build: {latest_build[0]}")
        return full_url

    def _configure_system(self, rootfs: Path):
        # DNS
        resolv = rootfs / "etc" / "resolv.conf"
        if resolv.is_symlink() or resolv.exists():
            resolv.unlink()
        try:
            shutil.copy("/etc/resolv.conf", resolv)
        except FileNotFoundError:
            with open(resolv, "w") as f:
                f.write("nameserver 8.8.8.8\n")

        # Distro Specifics
        if self.distro == "debian":
            apt_conf = rootfs / "etc" / "apt" / "apt.conf.d"
            apt_conf.mkdir(parents=True, exist_ok=True)
            (apt_conf / "01sandbox").write_text('APT::Sandbox::User "root";')
        elif self.distro == "arch":
            # [NEW] Arch Linux Fixes
            pac_conf = rootfs / "etc" / "pacman.conf"
            if pac_conf.exists():
                content = pac_conf.read_text()
                content = content.replace("#DisableSandbox", "DisableSandbox")
                content = content.replace("CheckSpace", "#CheckSpace")
                pac_conf.write_text(content)
                logger.info("Applied Arch Linux pacman.conf fixes")
        
        mask_targets = ["usr/bin/chown", "bin/chown", "usr/sbin/chown", "sbin/chown"]
        
        for t in mask_targets:
            target_path = rootfs / t
            if target_path.parent.is_symlink():
                logger.debug(f"Skipping mask for {t} because parent dir is a symlink (Host Protection).")
                continue

            # Handle UsrMerge (bin -> usr/bin) by resolving, or just overwrite if it exists
            if target_path.exists() or target_path.is_symlink():
                try:
                    # Remove original binary/link
                    target_path.unlink()
                    
                    # Write no-op script
                    with open(target_path, "w") as f:
                        f.write("#!/bin/sh\n# Masked by go-judge-py\nexit 0\n")
                    
                    # Make executable
                    target_path.chmod(0o755)
                    logger.info(f"Permanently masked {t}")
                except Exception as e:
                    logger.warning(f"Failed to mask {t}: {e}")
