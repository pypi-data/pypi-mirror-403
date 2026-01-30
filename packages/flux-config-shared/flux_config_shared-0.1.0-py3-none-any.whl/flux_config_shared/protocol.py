"""JSON-RPC 2.0 protocol definitions for daemon/client communication."""

from __future__ import annotations

from enum import Enum, auto
from typing import Any

from pydantic import BaseModel, Field


class InstallState(Enum):
    """Overall installation state of the system."""

    NEW = auto()  # First-time installation
    RESUMING = auto()  # Resuming incomplete installation
    COMPLETE = auto()  # All tasks finished
    CANCELLED = auto()  # Installation was cancelled by user
    SCHEMA_MIGRATION = auto()  # Schema was updated, some tasks done
    RECONFIGURING_NOW = auto()  # User chose to reconfigure now
    RECONFIGURING_LATER = auto()  # User chose to reconfigure later
    UNKNOWN = auto()  # Initial state before loading from DB


class MethodName(str, Enum):
    """RPC method names (Client → Daemon)."""

    # Subscriptions (topic-based event streaming)
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"

    # Configuration
    CONFIG_GET_USER = "config.get_user"
    CONFIG_SET_USER = "config.set_user"
    CONFIG_GET_INSTALLER = "config.get_installer"
    CONFIG_GET_APP = "config.get_app"
    CONFIG_UPDATE_APP = "config.update_app"
    CONFIG_VALIDATE_PUBKEY = "config.validate_pubkey"
    CONFIG_WRITE_FLUXD_GENERIC = "config.write_fluxd_generic"
    CONFIG_CREATE_FLUXD = "config.create_fluxd"
    CONFIG_REMOVE = "config.remove"
    CONFIG_GET_SHAPING_POLICY = "config.get_shaping_policy"

    # State Management
    STATE_POPULATE = "state.populate"
    STATE_GET_RECONFIGURE = "state.get_reconfigure"
    STATE_CREATE_MARKER = "state.create_marker"
    STATE_REMOVE_MARKER = "state.remove_marker"
    STATE_MARKER_EXISTS = "state.marker_exists"

    # Service Management
    SERVICE_START = "service.start"
    SERVICE_STOP = "service.stop"
    SERVICE_RESTART = "service.restart"
    SERVICE_ENABLE = "service.enable"
    SERVICE_DISABLE = "service.disable"
    SERVICE_GET_STATUS = "service.get_status"
    SERVICE_LIST = "service.list"
    SERVICE_SUBSCRIBE = "service.subscribe"
    SERVICE_UNSUBSCRIBE = "service.unsubscribe"

    # System
    SYSTEM_REBOOT = "system.reboot"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_FIRMWARE_REBOOT = "system.firmware_reboot"
    SYSTEM_DAEMON_RELOAD = "system.daemon_reload"
    SYSTEM_SYNC = "system.sync"
    SYSTEM_DROP_CACHES = "system.drop_caches"
    SYSTEM_GET_PUBLIC_IP = "system.get_public_ip"
    SYSTEM_CHECK_UEFI = "system.check_uefi"
    SYSTEM_CHECK_LUKS = "system.check_luks"
    SYSTEM_CHECK_CONNECTIVITY = "system.check_connectivity"
    SYSTEM_GET_LOCAL_IP = "system.get_local_ip"

    # Firewall
    FIREWALL_ADD_RULE = "firewall.add_rule"
    FIREWALL_REMOVE_RULE = "firewall.remove_rule"
    FIREWALL_GET_RULES = "firewall.get_rules"

    # Installation
    INSTALL_START = "install.start"
    INSTALL_GET_STATE = "install.get_state"
    INSTALL_ABORT = "install.abort"
    INSTALL_CANCEL = "install.cancel"

    # Reinstall (post-installation)
    REINSTALL_START = "reinstall.start"

    # FluxD
    FLUXD_GET_STATUS = "fluxd.get_status"
    FLUXD_GET_BLOCK_HEIGHT = "fluxd.get_block_height"
    FLUXD_GET_BLOCK_HEIGHT_API = "fluxd.get_block_height_api"
    FLUXD_GET_INFO = "fluxd.get_info"
    FLUXD_CALL_RPC = "fluxd.call_rpc"
    FLUXD_TEST_DBS = "fluxd.test_dbs"
    FLUXD_GET_BLOCKHEIGHT_FROM_DB = "fluxd.get_blockheight_from_db"
    FLUXD_GET_BLOCK_COUNT = "fluxd.get_block_count"
    FLUXD_ZMQ_STATUS = "fluxd.zmq_status"

    # FluxBenchD
    FLUXBENCHD_GET_STATUS = "fluxbenchd.get_status"
    FLUXBENCHD_GET_BENCHMARKS = "fluxbenchd.get_benchmarks"
    FLUXBENCHD_CALL_RPC = "fluxbenchd.call_rpc"

    # Delegate Node Starting
    DELEGATE_CHECK_READINESS = "delegate.check_readiness"
    DELEGATE_VALIDATE_PASSWORD = "delegate.validate_password"
    DELEGATE_START_NODE = "delegate.start_node"

    # Node Operations
    NODE_CLONE_REPO = "node.clone_repo"
    NODE_NPM_INSTALL = "node.npm_install"
    NODE_DOWNLOAD_CHAIN = "node.download_chain"
    NODE_VERIFY_CHAIN = "node.verify_chain"
    NODE_FETCH_PARAMS = "node.fetch_params"
    NODE_GET_CHAIN_PROGRESS = "node.get_chain_progress"

    # Bootstrap Operations
    BOOTSTRAP_GET_FASTEST_CDN = "bootstrap.get_fastest_cdn"

    # Upgrade Operations
    UPGRADE_CHECK = "upgrade.check"
    UPGRADE_START = "upgrade.start"
    UPGRADE_GET_STATE = "upgrade.get_state"
    UPGRADE_DEFER_REBOOT = "upgrade.defer_reboot"

    # Reconfiguration
    RECONFIGURE_SET_MODE = "reconfigure.set_mode"
    RECONFIGURE_GET_STATE = "reconfigure.get_state"
    RECONFIGURE_SERVICES = "reconfigure.services"
    RECONFIGURE_START = "reconfigure.start"

    # Display / X11
    DISPLAY_SET_RESOLUTION = "display.set_resolution"
    DISPLAY_SET_DPMS = "display.set_dpms"
    DISPLAY_GET_RESOLUTIONS = "display.get_resolutions"

    # Web API / Webserver
    WEB_GET_TOKEN = "web.get_token"  # noqa: S105
    WEB_CONFIGURE = "web.configure"
    WEBSERVER_START = "webserver.start"
    WEBSERVER_STOP = "webserver.stop"
    WEBSERVER_GET_STATUS = "webserver.get_status"

    # Tunnel Management
    TUNNEL_START = "tunnel.start"
    TUNNEL_STOP = "tunnel.stop"
    TUNNEL_GET_STATUS = "tunnel.get_status"

    # System Metrics
    METRICS_GET_SYSTEM_LOAD = "metrics.get_system_load"
    METRICS_GET_MEMORY = "metrics.get_memory"
    METRICS_GET_DISK = "metrics.get_disk"
    METRICS_GET_CPU = "metrics.get_cpu"
    METRICS_GET_NETWORK = "metrics.get_network"
    METRICS_GET_PROCESS_MEMORY = "metrics.get_process_memory"

    # Logs
    LOGS_GET_SERVICE = "logs.get_service"
    LOGS_GET_JOURNAL = "logs.get_journal"
    LOGS_GET_AVAILABLE_SERVICES = "logs.get_available_services"

    # Filesystem
    FILESYSTEM_CREATE_DIRECTORIES = "filesystem.create_directories"
    FILESYSTEM_REMOVE_DIRECTORIES = "filesystem.remove_directories"
    FILESYSTEM_HASH_FILE = "filesystem.hash_file"

    # Task Management (async operations)
    TASK_GET_STATUS = "task.get_status"
    TASK_LIST = "task.list"

    # Network Interface Management
    NETWORK_GET_INTERFACES = "network.get_interfaces"
    NETWORK_SET_STATIC_IP = "network.set_static_ip"
    NETWORK_SET_DHCP = "network.set_dhcp"
    NETWORK_SET_DISABLED = "network.set_disabled"
    NETWORK_CREATE_VLAN = "network.create_vlan"
    NETWORK_DELETE_VLAN = "network.delete_vlan"
    NETWORK_RESTART_NETWORKD = "network.restart_networkd"

    # Network DNS
    NETWORK_GET_DNS = "network.get_dns"
    NETWORK_TEST_DNS = "network.test_dns"

    # Network Routing
    NETWORK_GET_ROUTES = "network.get_routes"
    NETWORK_TEST_CONNECTIVITY = "network.test_connectivity"

    # Network UPnP
    NETWORK_UPNP_GET_STATUS = "network.upnp.get_status"
    NETWORK_UPNP_GET_MAPPINGS = "network.upnp.get_mappings"
    NETWORK_UPNP_ADD_MAPPING = "network.upnp.add_mapping"
    NETWORK_UPNP_REMOVE_MAPPING = "network.upnp.remove_mapping"

    # Network Traffic Shaping
    NETWORK_SHAPING_GET_POLICY = "network.shaping.get_policy"
    NETWORK_SHAPING_SET_POLICY = "network.shaping.set_policy"


class EventType(str, Enum):
    """Event types (Daemon → Client)."""

    # Service State
    SERVICE_STATE_CHANGED = "service.state_changed"
    SERVICE_STATES_READY = "service.states_ready"
    SERVICE_STARTED = "service.started"
    SERVICE_STOPPED = "service.stopped"

    # Installation Progress
    INSTALL_TASK_STARTED = "install.task_started"
    INSTALL_TASK_COMPLETED = "install.task_completed"
    INSTALL_TASK_CANCELLED = "install.task_cancelled"
    INSTALL_TASK_FAILED = "install.task_failed"
    INSTALL_PROGRESS = "install.progress"
    INSTALL_STATE_CHANGED = "install.state_changed"

    # Download Progress (chain, params)
    DOWNLOAD_PROGRESS = "download.progress"
    DOWNLOAD_COMPLETED = "download.completed"
    DOWNLOAD_FAILED = "download.failed"

    # Upgrade Events
    UPGRADE_STARTED = "upgrade.started"
    UPGRADE_IN_PROGRESS = "upgrade.in_progress"  # Alias for UPGRADE_STARTED
    UPGRADE_AVAILABLE = "upgrade.available"
    UPGRADE_PROGRESS = "upgrade.progress"
    UPGRADE_PROPERTY_CHANGED = "upgrade.property_changed"
    UPGRADE_COMPLETED = "upgrade.completed"
    UPGRADE_FAILED = "upgrade.failed"

    # System Events
    SYSTEM_CONNECTIVITY = "system.connectivity"
    SYSTEM_PUBLIC_IP = "system.public_ip"
    SYSTEM_ERROR = "system.error"
    SYSTEM_METRICS_UPDATE = "system.metrics_update"  # Periodic metrics (every 5s)
    NETWORK_CONFIG_REQUIRED = "network.config_required"
    INSUFFICIENT_SPACE = "system.insufficient_space"

    # Network Events
    NETWORK_INTERFACE_CHANGED = "network.interface_changed"
    NETWORK_ROUTES_CHANGED = "network.routes_changed"
    NETWORK_DNS_CHANGED = "network.dns_changed"
    NETWORK_UPNP_STATUS_CHANGED = "network.upnp_status_changed"

    # Network Monitoring Events (subscription-triggered)
    CONNECTIVITY_UPDATE = "network.connectivity_update"
    DNS_RESOLUTION_UPDATE = "network.dns_resolution_update"

    # Fluxd Events
    FLUXD_RPC_ONLINE = "fluxd.rpc_online"
    FLUXD_RPC_OFFLINE = "fluxd.rpc_offline"
    FLUXD_BLOCK_HEIGHT = "fluxd.block_height"
    FLUXD_ZMQ_CONNECTED = "fluxd.zmq_connected"
    FLUXD_ZMQ_DISCONNECTED = "fluxd.zmq_disconnected"
    FLUXD_ZMQ_NEW_BLOCK = "fluxd.zmq_new_block"
    FLUXD_STATUS_CHANGED = "fluxd.status_changed"
    FLUXBENCHD_STATUS_CHANGED = "fluxbenchd.status_changed"

    # Web Configuration
    WEBSERVER_STARTED = "webserver.started"
    WEBSERVER_STOPPED = "webserver.stopped"

    # Tunnel Events
    TUNNEL_CONNECTING = "tunnel.connecting"
    TUNNEL_STARTED = "tunnel.started"
    TUNNEL_STOPPED = "tunnel.stopped"
    TUNNEL_ERROR = "tunnel.error"

    # Log/Activity Messages
    LOG_MESSAGE = "log.message"

    # State Synchronization
    STATE_UPDATE = "state.update"  # Unified state update event
    INITIAL_STATE = "state.initial"  # Complete state sent to new clients

    # Async Task Events (for long-running operations)
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"


class RPCErrorCode(int, Enum):
    """JSON-RPC 2.0 error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603

    # Custom error codes
    UNAUTHORIZED = -32000
    SERVICE_NOT_FOUND = -32001
    INSTALLATION_IN_PROGRESS = -32002
    INSTALLATION_FAILED = -32003
    PRIVILEGE_ERROR = -32004


class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request message."""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    method: str = Field(description="Method name")
    params: dict[str, Any] | list[Any] | None = Field(default=None, description="Method parameters")
    id: str | int | None = Field(default=None, description="Request ID")


class JsonRpcError(BaseModel):
    """JSON-RPC 2.0 error object."""

    code: int = Field(description="Error code")
    message: str = Field(description="Error message")
    data: Any | None = Field(default=None, description="Additional error data")


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response message."""

    jsonrpc: str = Field(default="2.0", description="JSON-RPC version")
    result: Any | None = Field(default=None, description="Method result")
    error: JsonRpcError | None = Field(default=None, description="Error object")
    id: str | int | None = Field(default=None, description="Request ID")


class Event(BaseModel):
    """Event message (Daemon → Client)."""

    type: str = Field(description="Event type")
    data: dict[str, Any] = Field(description="Event data")
    timestamp: float = Field(description="Event timestamp (Unix time)")


# --- Data Models ---


class ServiceStatusData(BaseModel):
    """Service status data."""

    name: str
    active: bool
    running: bool
    enabled: bool
    pid: int | None = None
    error: str | None = None


class InstallStateData(BaseModel):
    """Installation state data."""

    in_progress: bool
    current_task: str | None = None
    completed_tasks: list[str]
    failed_task: str | None = None
    error: str | None = None


class UpgradeStateData(BaseModel):
    """Upgrade state data - maps to D-Bus FluxUpgrade1 properties."""

    validating: bool = False
    available: bool = False
    in_progress: bool = False
    bytes_complete: int = 0
    bytes_total: int = 0
    start_time: float = 0.0
    finish_time: float = 0.0
    attempts: int = 0
    reboot_deferred: bool = False
    reboot_timer: int = 0
    current_version: str | None = None
    new_version: str | None = None

    @property
    def in_flight(self) -> bool:
        """Check if any upgrade activity is in progress."""
        return self.validating or self.available or self.in_progress

    @property
    def progress(self) -> float | None:
        """Calculate progress as a percentage (0.0 to 1.0)."""
        if self.bytes_total > 0:
            return self.bytes_complete / self.bytes_total
        return None


class DownloadProgressData(BaseModel):
    """Download progress data."""

    file: str
    bytes_downloaded: int
    total_bytes: int | None = None
    percent: float | None = None
    speed_mbps: float | None = None


class FluxdStatusData(BaseModel):
    """Fluxd RPC status data."""

    online: bool
    block_height: int | None = None
    connections: int | None = None
    synced: bool | None = None
