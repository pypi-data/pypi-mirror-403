"""Unified daemon state model for synchronization between daemon and TUI."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from enum import Enum


class DaemonPhase(str, Enum):
    """Daemon lifecycle phases (simplified state machine).

    Phases represent daemon's overall state, NOT UI loading states.
    Use SystemStatus enums to determine specific loading messages.
    """

    INITIALIZING = "initializing"
    RUNNING = "running"
    ERROR = "error"


class DatMountStatus(str, Enum):
    """Data crypt mount status (replaces ad-hoc status_message)."""

    PENDING = "pending"
    MOUNTING = "mounting"
    DELAYED = "delayed"
    FAILED = "failed"
    COMPLETE = "complete"


class ConnectivityStatus(str, Enum):
    """Network connectivity status."""

    UNKNOWN = "unknown"
    CHECKING = "checking"
    VALIDATED = "validated"
    FAILED = "failed"


@dataclass
class InitializationStatus:
    """Tracks initialization progress without ad-hoc strings."""

    completed_milestones: set[str] = field(default_factory=set)
    current_operation: str | None = None
    current_operation_started_at: float | None = None
    blocked_on: list[str] = field(default_factory=list)

    def is_complete(self) -> bool:
        """Check if all key milestones are complete."""
        key_milestones = {"dat_mounted", "db_state_populated", "connectivity_validated"}
        return key_milestones.issubset(self.completed_milestones)


@dataclass
class SystemStatus:
    """System readiness status using enums (replaces status_message + fatal_error)."""

    dat_mount_status: DatMountStatus = DatMountStatus.PENDING
    dat_mount_error: str | None = None

    connectivity_status: ConnectivityStatus = ConnectivityStatus.UNKNOWN
    connectivity_error: str | None = None
    connectivity_checked_at: float | None = None

    db_populated: bool = False
    db_error: str | None = None

    fatal_error: dict[str, str] | None = None


@dataclass
class ServiceStates:
    """Service running states."""

    fluxd_started: bool = False
    fluxbenchd_started: bool = False
    fluxos_started: bool = False
    syncthing_started: bool = False
    flux_watchdog_started: bool = False


@dataclass
class NetworkInfo:
    """Network information."""

    public_ip: str | None = None
    local_ip: str | None = None
    connected: bool = False


@dataclass
class BlockchainInfo:
    """Blockchain information."""

    height: int | None = None


@dataclass
class SystemInfo:
    """System information."""

    secureboot_enforced: bool = False


@dataclass
class WebserverInfo:
    """Webserver state."""

    host: str | None = None
    port: int | None = None
    token: str | None = None


@dataclass
class ConfigInfo:
    """Configuration state."""

    installer_config: dict | None = None
    user_config: dict | None = None


@dataclass
class DaemonState:
    """Complete daemon state - single source of truth."""

    phase: DaemonPhase = DaemonPhase.INITIALIZING

    install_state: str = "UNKNOWN"
    reconfigure_mode: str | None = None

    initialization: InitializationStatus = field(default_factory=InitializationStatus)

    system_status: SystemStatus = field(default_factory=SystemStatus)

    services: ServiceStates = field(default_factory=ServiceStates)

    network: NetworkInfo = field(default_factory=NetworkInfo)

    blockchain: BlockchainInfo = field(default_factory=BlockchainInfo)

    system: SystemInfo = field(default_factory=SystemInfo)

    webserver: WebserverInfo = field(default_factory=WebserverInfo)

    tunnel: dict = field(default_factory=dict)

    config: ConfigInfo = field(default_factory=ConfigInfo)

    active_tasks: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result["phase"] = self.phase.value
        result["system_status"]["dat_mount_status"] = (
            self.system_status.dat_mount_status.value
        )
        result["system_status"]["connectivity_status"] = (
            self.system_status.connectivity_status.value
        )
        return result
