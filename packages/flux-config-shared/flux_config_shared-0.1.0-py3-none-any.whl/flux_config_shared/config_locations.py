"""Configuration file locations for Flux services."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ConfigLocations:
    """Standard configuration file locations for Flux services.

    This matches the original ConfigLocations class from config_builder.py
    """

    # Daemon configs
    fluxd: Path = Path("/dat/var/lib/fluxd/flux.conf")
    fluxd_seed_nodes: Path = Path("/mnt/root/config/seed_nodes.yaml")
    fluxbenchd: Path = Path("/dat/usr/lib/fluxbenchd/fluxbench.conf")
    fluxos: Path = Path("/dat/usr/lib/fluxos/config/userconfig.js")
    flux_watchdog: Path = Path("/dat/usr/lib/fluxwatchdog/config.js")
    syncthing: Path = Path("/dat/usr/lib/syncthing/config.xml")

    # SSH configs
    ssh_auth_flux: Path = Path("/mnt/root/config/ssh/authorized_keys")
    ssh_auth_fs: Path = Path("/home/operator/.ssh/authorized_keys")

    # Systemd configs
    fluxadm_ssh_socket: Path = Path("/etc/systemd/system/fluxadm-ssh.socket.d/override.conf")

    # Firewall configs
    fluxadm_ufw: Path = Path("/etc/ufw/applications.d/fluxadm-ssh")
    fail2ban: Path = Path("/etc/fail2ban/jail.d/defaults-debian.conf")

    # X11/Display configs
    xorg_serverflags: Path = Path("/etc/X11/xorg.conf.d/10-serverflags.conf")
    xorg_serverflags_persistent: Path = Path(
        "/mnt/root/config/etc/X11/xorg.conf.d/10-serverflags.conf"
    )

    # Application configs
    config_dir: Path = Path("/mnt/root/config")
    logs_dir: Path = Path("/var/log/flux_config")
    user_config: Path = Path("/mnt/root/config/flux_user_config.yaml")
    installer_config: Path = Path("/mnt/root/config/flux_config.yaml")
    shaping_policy: Path = Path("/mnt/root/config/shaping_policy.json")
