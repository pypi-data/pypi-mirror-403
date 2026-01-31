"""Server registry for tracking active GDSFactory+ instances.

This module manages a registry of running GDSFactory+ servers to enable
multi-project support with dynamic port assignment.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psutil

__all__ = ["ServerRegistry", "ServerInfo", "get_registry_path"]


def get_registry_path() -> Path:
    """Get the path to the server registry file.

    Returns:
        Path to ~/.gdsfactory/server-registry.json
    """
    gdsfactory_dir = Path.home() / ".gdsfactory"
    gdsfactory_dir.mkdir(parents=True, exist_ok=True)
    return gdsfactory_dir / "server-registry.json"


class ServerInfo:
    """Information about a running GDSFactory+ server."""

    def __init__(
        self,
        port: int,
        pid: int,
        project_path: str,
        project_name: str,
        pdk: str | None = None,
        started_at: str | None = None,
        last_heartbeat: str | None = None,
    ) -> None:
        """Initialize server info.

        Args:
            port: HTTP server port
            pid: Process ID
            project_path: Absolute path to project directory
            project_name: Human-readable project name
            pdk: PDK name (optional)
            started_at: ISO timestamp when server started
            last_heartbeat: ISO timestamp of last heartbeat
        """
        self.port = port
        self.pid = pid
        self.project_path = project_path
        self.project_name = project_name
        self.pdk = pdk
        self.started_at = started_at or datetime.now(UTC).isoformat()
        self.last_heartbeat = last_heartbeat or datetime.now(UTC).isoformat()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "port": self.port,
            "pid": self.pid,
            "project_path": self.project_path,
            "project_name": self.project_name,
            "pdk": self.pdk,
            "started_at": self.started_at,
            "last_heartbeat": self.last_heartbeat,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ServerInfo:
        """Create from dictionary."""
        return cls(
            port=data["port"],
            pid=data["pid"],
            project_path=data["project_path"],
            project_name=data["project_name"],
            pdk=data.get("pdk"),
            started_at=data.get("started_at"),
            last_heartbeat=data.get("last_heartbeat"),
        )

    def is_alive(self) -> bool:
        """Check if the server process is still running.

        Returns:
            True if process exists, False otherwise
        """
        try:
            process = psutil.Process(self.pid)
            return process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False


class ServerRegistry:
    """Registry for tracking active GDSFactory+ servers."""

    def __init__(self, registry_path: Path | None = None) -> None:
        """Initialize registry.

        Args:
            registry_path: Optional custom path to registry file
        """
        self.registry_path = registry_path or get_registry_path()
        self._ensure_registry_exists()

    def _ensure_registry_exists(self) -> None:
        """Ensure the registry file exists."""
        if not self.registry_path.exists():
            self._write_registry({"servers": {}})

    def _read_registry(self) -> dict[str, Any]:
        """Read the registry file.

        Returns:
            Registry data as dictionary
        """
        try:
            with self.registry_path.open() as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"servers": {}}

    def _write_registry(self, data: dict[str, Any]) -> None:
        """Write the registry file.

        Args:
            data: Registry data to write
        """
        with self.registry_path.open("w") as f:
            json.dump(data, f, indent=2)

    def register_server(self, server_info: ServerInfo) -> None:
        """Register a new server or update existing entry.

        Args:
            server_info: Server information to register
        """
        data = self._read_registry()
        port_key = str(server_info.port)
        data["servers"][port_key] = server_info.to_dict()
        self._write_registry(data)

    def unregister_server(self, port: int) -> None:
        """Unregister a server by port.

        Args:
            port: Port of server to unregister
        """
        data = self._read_registry()
        port_key = str(port)
        if port_key in data["servers"]:
            del data["servers"][port_key]
            self._write_registry(data)

    def get_server(self, port: int) -> ServerInfo | None:
        """Get server info by port.

        Args:
            port: Port number

        Returns:
            ServerInfo if found and alive, None otherwise
        """
        data = self._read_registry()
        port_key = str(port)

        if port_key not in data["servers"]:
            return None

        server_info = ServerInfo.from_dict(data["servers"][port_key])

        # Check if process is still alive
        if not server_info.is_alive():
            # Clean up stale entry
            self.unregister_server(port)
            return None

        return server_info

    def get_server_by_project(self, project_name: str) -> ServerInfo | None:
        """Get server info by project name.

        Args:
            project_name: Project name or path

        Returns:
            ServerInfo if found and alive, None otherwise
        """
        for server in self.list_servers():
            if project_name in {
                server.project_name,
                server.project_path,
                Path(server.project_path).name,
            }:
                return server
        return None

    def list_servers(self, *, include_dead: bool = False) -> list[ServerInfo]:
        """List all registered servers.

        Args:
            include_dead: Include servers with dead processes

        Returns:
            List of ServerInfo objects
        """
        data = self._read_registry()
        servers = []
        stale_ports = []

        for port_key, server_data in data["servers"].items():
            server_info = ServerInfo.from_dict(server_data)

            if server_info.is_alive() or include_dead:
                servers.append(server_info)
            else:
                # Mark for cleanup
                stale_ports.append(int(port_key))

        # Clean up stale entries
        for port in stale_ports:
            self.unregister_server(port)

        return servers

    def update_heartbeat(self, port: int) -> None:
        """Update the last heartbeat timestamp for a server.

        Args:
            port: Port of server to update
        """
        data = self._read_registry()
        port_key = str(port)

        if port_key in data["servers"]:
            data["servers"][port_key]["last_heartbeat"] = datetime.now(UTC).isoformat()
            self._write_registry(data)
