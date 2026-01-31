"""Graph connection for MCP server - supports HTTP proxy or direct DB access."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import Optional

# Lazy imports
kuzu = None
httpx = None
KUZU_AVAILABLE = False
HTTPX_AVAILABLE = False


def _init_kuzu():
    """Initialize kuzu module."""
    global kuzu, KUZU_AVAILABLE
    if kuzu is None:
        try:
            import kuzu as _kuzu
            kuzu = _kuzu
            KUZU_AVAILABLE = True
        except ImportError:
            KUZU_AVAILABLE = False


def _init_httpx():
    """Initialize httpx module."""
    global httpx, HTTPX_AVAILABLE
    if httpx is None:
        try:
            import httpx as _httpx
            httpx = _httpx
            HTTPX_AVAILABLE = True
        except ImportError:
            HTTPX_AVAILABLE = False


class GraphConnection:
    """Graph connection that proxies through emdash server or falls back to direct DB.

    This connection attempts to use the emdash server's HTTP API first, which avoids
    KuzuDB lock conflicts when the server is holding a write connection. If the server
    is not available, it falls back to direct read-only database access.
    """

    SERVERS_DIR = Path.home() / ".emdash" / "servers"

    def __init__(self, db_path: str, server_url: Optional[str] = None):
        """Initialize connection.

        Args:
            db_path: Path to the Kuzu database directory.
            server_url: Optional emdash server URL. If not provided, will attempt
                       to discover from port file.
        """
        self.db_path = Path(db_path)
        self._server_url = server_url
        self._db = None
        self._conn = None
        self._use_http: Optional[bool] = None  # None = not yet determined
        self._http_client = None

    def _get_repo_root(self) -> Optional[Path]:
        """Get repo root from db_path.

        The db_path is typically {repo_root}/.emdash/index/kuzu_db
        """
        # Walk up from db_path to find .emdash directory
        path = self.db_path
        for _ in range(5):
            if path.name == ".emdash":
                return path.parent
            if (path / ".emdash").exists():
                return path
            path = path.parent
        return None

    def _discover_server_url(self) -> Optional[str]:
        """Discover emdash server URL from port file."""
        repo_root = self._get_repo_root()
        if not repo_root:
            return None

        # Compute repo hash (same algorithm as ServerManager)
        path_str = str(repo_root.resolve())
        repo_hash = hashlib.sha256(path_str.encode()).hexdigest()[:12]

        port_file = self.SERVERS_DIR / f"{repo_hash}.port"
        if not port_file.exists():
            return None

        try:
            port = int(port_file.read_text().strip())
            return f"http://localhost:{port}"
        except (ValueError, IOError):
            return None

    def _check_server_health(self, url: str) -> bool:
        """Check if server is healthy."""
        _init_httpx()
        if not HTTPX_AVAILABLE:
            return False

        try:
            response = httpx.get(f"{url}/api/graph/health", timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False

    def _determine_connection_mode(self) -> bool:
        """Determine whether to use HTTP or direct DB access.

        Returns:
            True if should use HTTP, False for direct DB access.
        """
        # Try server URL if provided
        if self._server_url:
            if self._check_server_health(self._server_url):
                return True

        # Try to discover server
        discovered_url = self._discover_server_url()
        if discovered_url and self._check_server_health(discovered_url):
            self._server_url = discovered_url
            return True

        # Fall back to direct DB access
        return False

    def _execute_http(self, query: str, params: Optional[dict] = None) -> list[dict]:
        """Execute query via HTTP proxy."""
        _init_httpx()
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx is required for HTTP proxy mode")

        if self._http_client is None:
            self._http_client = httpx.Client(timeout=30.0)

        response = self._http_client.post(
            f"{self._server_url}/api/graph/query",
            json={"query": query, "params": params or {}},
        )

        if response.status_code != 200:
            error_detail = response.json().get("detail", response.text)
            raise RuntimeError(f"Query failed: {error_detail}")

        result = response.json()
        return result.get("rows", [])

    def _execute_direct(self, query: str, params: Optional[dict] = None) -> list[dict]:
        """Execute query directly against database."""
        conn = self.connect()
        result = conn.execute(query, params or {})
        columns = result.get_column_names()
        rows = []
        while result.has_next():
            values = result.get_next()
            rows.append(dict(zip(columns, values)))
        return rows

    def connect(self):
        """Establish read-only connection to the database (for direct mode)."""
        _init_kuzu()
        if not KUZU_AVAILABLE:
            raise ImportError(
                "Kuzu graph database is not installed. "
                "Install with: pip install 'emdash-ai[graph]'\n"
                "Or: pip install kuzu"
            )

        if self._conn is None:
            if not self.db_path.exists():
                raise FileNotFoundError(f"Database not found at {self.db_path}")
            self._db = kuzu.Database(str(self.db_path), read_only=True)
            self._conn = kuzu.Connection(self._db)
        return self._conn

    def execute(self, query: str, params: Optional[dict] = None) -> list[dict]:
        """Execute a Cypher query and return results as list of dicts.

        First attempts to use HTTP proxy through emdash server. If server is not
        available, falls back to direct read-only database access.

        Args:
            query: Cypher query string.
            params: Query parameters.

        Returns:
            List of result dictionaries.
        """
        # Determine connection mode on first query
        if self._use_http is None:
            self._use_http = self._determine_connection_mode()
            if self._use_http:
                # Log to stderr so it doesn't interfere with MCP stdio
                print(f"[graph-mcp] Using HTTP proxy: {self._server_url}", file=sys.stderr)
            else:
                print(f"[graph-mcp] Using direct DB: {self.db_path}", file=sys.stderr)

        # Try HTTP first if enabled
        if self._use_http:
            try:
                return self._execute_http(query, params)
            except Exception as e:
                # If HTTP fails, try direct access as fallback
                print(f"[graph-mcp] HTTP proxy failed ({e}), trying direct DB", file=sys.stderr)
                self._use_http = False

        return self._execute_direct(query, params)

    def close(self):
        """Close connection and release resources."""
        self._conn = None
        self._db = None
        if self._http_client:
            self._http_client.close()
            self._http_client = None
