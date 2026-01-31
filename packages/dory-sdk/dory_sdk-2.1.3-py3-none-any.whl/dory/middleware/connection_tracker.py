"""
Connection Tracker Middleware

Automatically tracks and manages connections (database, HTTP, etc.).
Eliminates manual connection lifecycle management.

Features:
- Automatic connection registration
- Health checking
- Auto-close on shutdown
- Connection pooling awareness
- Leak detection
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, List, Callable, Set
from functools import wraps

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """Connection status."""
    CONNECTING = "connecting"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"


class ConnectionType(Enum):
    """Type of connection."""
    DATABASE = "database"
    HTTP = "http"
    WEBSOCKET = "websocket"
    QUEUE = "queue"
    CACHE = "cache"
    CUSTOM = "custom"


@dataclass
class ConnectionInfo:
    """
    Information about a tracked connection.
    """
    connection_id: str
    connection_type: ConnectionType
    name: str
    status: ConnectionStatus
    created_at: float
    last_used: float
    use_count: int = 0
    health_check_count: int = 0
    last_health_check: Optional[float] = None
    health_status: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "connection_id": self.connection_id,
            "connection_type": self.connection_type.value,
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "use_count": self.use_count,
            "health_check_count": self.health_check_count,
            "last_health_check": self.last_health_check,
            "health_status": self.health_status,
            "error": self.error,
            "age_seconds": time.time() - self.created_at,
            "idle_seconds": time.time() - self.last_used,
            "metadata": self.metadata,
        }

    def is_idle(self, idle_threshold: float = 300.0) -> bool:
        """
        Check if connection is idle.

        Args:
            idle_threshold: Idle threshold in seconds

        Returns:
            True if idle for more than threshold
        """
        return (time.time() - self.last_used) > idle_threshold

    def is_healthy(self) -> bool:
        """Check if connection is healthy."""
        return self.health_status and self.status == ConnectionStatus.OPEN


@dataclass
class ConnectionMetrics:
    """Connection metrics."""
    total_connections: int = 0
    open_connections: int = 0
    closed_connections: int = 0
    failed_connections: int = 0
    total_health_checks: int = 0
    failed_health_checks: int = 0
    total_use_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_connections": self.total_connections,
            "open_connections": self.open_connections,
            "closed_connections": self.closed_connections,
            "failed_connections": self.failed_connections,
            "total_health_checks": self.total_health_checks,
            "failed_health_checks": self.failed_health_checks,
            "total_use_count": self.total_use_count,
        }


class ConnectionTracker:
    """
    Tracks and manages connections automatically.

    Features:
    - Auto-register connections
    - Health checking
    - Auto-close on shutdown
    - Idle connection detection
    - Connection metrics

    Usage:
        tracker = ConnectionTracker()

        # Register connection
        conn_id = await tracker.register_connection(
            db_connection,
            name="database",
            connection_type=ConnectionType.DATABASE,
        )

        # Use connection (auto-tracked)
        async with tracker.use_connection(conn_id):
            result = await db_connection.execute(query)

        # Health check
        healthy = await tracker.health_check(conn_id)

        # Auto-close on shutdown
        await tracker.close_all_connections()
    """

    def __init__(
        self,
        enable_health_checks: bool = True,
        health_check_interval: float = 60.0,
        idle_timeout: float = 300.0,
        auto_close_on_idle: bool = True,
        on_connection_open: Optional[Callable] = None,
        on_connection_close: Optional[Callable] = None,
    ):
        """
        Initialize connection tracker.

        Args:
            enable_health_checks: Enable automatic health checks
            health_check_interval: Interval between health checks (seconds)
            idle_timeout: Timeout for idle connections (seconds)
            auto_close_on_idle: Automatically close idle connections
            on_connection_open: Callback when connection opens
            on_connection_close: Callback when connection closes
        """
        self.enable_health_checks = enable_health_checks
        self.health_check_interval = health_check_interval
        self.idle_timeout = idle_timeout
        self.auto_close_on_idle = auto_close_on_idle
        self.on_connection_open = on_connection_open
        self.on_connection_close = on_connection_close

        # Tracked connections
        self._connections: Dict[str, ConnectionInfo] = {}

        # Connection objects
        self._connection_objects: Dict[str, Any] = {}

        # Health check functions
        self._health_check_funcs: Dict[str, Callable] = {}

        # Close functions
        self._close_funcs: Dict[str, Callable] = {}

        # Metrics
        self._metrics = ConnectionMetrics()

        # Health check task
        self._health_check_task: Optional[asyncio.Task] = None

        # Counter
        self._connection_counter = 0

        # Lock
        self._lock = asyncio.Lock()

        logger.info(
            f"ConnectionTracker initialized: health_checks={enable_health_checks}, "
            f"health_interval={health_check_interval}s, idle_timeout={idle_timeout}s"
        )

        # Start health check loop
        if enable_health_checks:
            self._start_health_check_loop()

    def _generate_connection_id(self, name: str) -> str:
        """Generate unique connection ID."""
        self._connection_counter += 1
        timestamp = int(time.time() * 1000)
        return f"{name}_{timestamp}_{self._connection_counter}"

    async def register_connection(
        self,
        connection: Any,
        name: str,
        connection_type: ConnectionType = ConnectionType.CUSTOM,
        health_check_func: Optional[Callable] = None,
        close_func: Optional[Callable] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Register a connection for tracking.

        Args:
            connection: Connection object
            name: Connection name
            connection_type: Type of connection
            health_check_func: Optional health check function
            close_func: Optional close function
            metadata: Optional metadata

        Returns:
            Connection ID

        Example:
            conn_id = await tracker.register_connection(
                db_connection,
                name="postgres",
                connection_type=ConnectionType.DATABASE,
                health_check_func=lambda conn: conn.is_alive(),
                close_func=lambda conn: conn.close(),
            )
        """
        async with self._lock:
            connection_id = self._generate_connection_id(name)

            # Create connection info
            conn_info = ConnectionInfo(
                connection_id=connection_id,
                connection_type=connection_type,
                name=name,
                status=ConnectionStatus.OPEN,
                created_at=time.time(),
                last_used=time.time(),
                metadata=metadata or {},
            )

            # Store
            self._connections[connection_id] = conn_info
            self._connection_objects[connection_id] = connection

            if health_check_func:
                self._health_check_funcs[connection_id] = health_check_func
            if close_func:
                self._close_funcs[connection_id] = close_func

            # Update metrics
            self._metrics.total_connections += 1
            self._metrics.open_connections += 1

        # Call open callback
        if self.on_connection_open:
            try:
                if asyncio.iscoroutinefunction(self.on_connection_open):
                    await self.on_connection_open(conn_info)
                else:
                    self.on_connection_open(conn_info)
            except Exception as e:
                logger.error(f"Connection open callback failed: {e}")

        logger.info(f"Connection registered: {connection_id} ({name})")

        return connection_id

    async def use_connection(self, connection_id: str):
        """
        Context manager to use a connection.

        Updates last_used timestamp and use_count.

        Args:
            connection_id: Connection ID

        Example:
            async with tracker.use_connection(conn_id):
                result = await connection.execute(query)
        """
        if connection_id not in self._connections:
            raise ValueError(f"Connection not found: {connection_id}")

        conn_info = self._connections[connection_id]

        # Update usage
        conn_info.last_used = time.time()
        conn_info.use_count += 1
        self._metrics.total_use_count += 1

        try:
            yield self._connection_objects[connection_id]
        except Exception as e:
            logger.error(f"Error using connection {connection_id}: {e}")
            conn_info.error = str(e)
            conn_info.health_status = False
            raise

    async def health_check(self, connection_id: str) -> bool:
        """
        Perform health check on a connection.

        Args:
            connection_id: Connection ID

        Returns:
            True if healthy
        """
        if connection_id not in self._connections:
            return False

        conn_info = self._connections[connection_id]
        conn_info.health_check_count += 1
        conn_info.last_health_check = time.time()
        self._metrics.total_health_checks += 1

        # Get health check function
        health_check_func = self._health_check_funcs.get(connection_id)
        if not health_check_func:
            # No health check function, assume healthy if open
            conn_info.health_status = conn_info.status == ConnectionStatus.OPEN
            return conn_info.health_status

        # Run health check
        try:
            connection = self._connection_objects[connection_id]
            if asyncio.iscoroutinefunction(health_check_func):
                healthy = await health_check_func(connection)
            else:
                healthy = health_check_func(connection)

            conn_info.health_status = bool(healthy)

            if not healthy:
                self._metrics.failed_health_checks += 1
                logger.warning(f"Health check failed: {connection_id}")

            return conn_info.health_status

        except Exception as e:
            logger.error(f"Health check error for {connection_id}: {e}")
            conn_info.health_status = False
            conn_info.error = str(e)
            self._metrics.failed_health_checks += 1
            return False

    async def close_connection(self, connection_id: str) -> bool:
        """
        Close a connection.

        Args:
            connection_id: Connection ID

        Returns:
            True if closed successfully
        """
        if connection_id not in self._connections:
            logger.warning(f"Connection not found: {connection_id}")
            return False

        conn_info = self._connections[connection_id]
        conn_info.status = ConnectionStatus.CLOSING

        try:
            # Get close function
            close_func = self._close_funcs.get(connection_id)
            if close_func:
                connection = self._connection_objects[connection_id]
                if asyncio.iscoroutinefunction(close_func):
                    await close_func(connection)
                else:
                    close_func(connection)

            # Update status
            conn_info.status = ConnectionStatus.CLOSED

            # Update metrics
            async with self._lock:
                self._metrics.open_connections -= 1
                self._metrics.closed_connections += 1

                # Remove from tracking
                del self._connections[connection_id]
                del self._connection_objects[connection_id]
                self._health_check_funcs.pop(connection_id, None)
                self._close_funcs.pop(connection_id, None)

            # Call close callback
            if self.on_connection_close:
                try:
                    if asyncio.iscoroutinefunction(self.on_connection_close):
                        await self.on_connection_close(conn_info)
                    else:
                        self.on_connection_close(conn_info)
                except Exception as e:
                    logger.error(f"Connection close callback failed: {e}")

            logger.info(f"Connection closed: {connection_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to close connection {connection_id}: {e}")
            conn_info.status = ConnectionStatus.ERROR
            conn_info.error = str(e)
            self._metrics.failed_connections += 1
            return False

    async def close_all_connections(self) -> int:
        """
        Close all tracked connections.

        Returns:
            Number of connections closed
        """
        logger.info("Closing all connections")

        # Get list of connection IDs
        connection_ids = list(self._connections.keys())

        closed_count = 0
        for conn_id in connection_ids:
            if await self.close_connection(conn_id):
                closed_count += 1

        logger.info(f"Closed {closed_count} connections")
        return closed_count

    def get_connections(
        self,
        connection_type: Optional[ConnectionType] = None,
        only_open: bool = False,
    ) -> List[ConnectionInfo]:
        """
        Get tracked connections.

        Args:
            connection_type: Optional filter by type
            only_open: Only return open connections

        Returns:
            List of connection info
        """
        connections = list(self._connections.values())

        if connection_type:
            connections = [c for c in connections if c.connection_type == connection_type]

        if only_open:
            connections = [c for c in connections if c.status == ConnectionStatus.OPEN]

        return connections

    def get_idle_connections(self, idle_threshold: Optional[float] = None) -> List[ConnectionInfo]:
        """
        Get idle connections.

        Args:
            idle_threshold: Optional threshold (uses default if None)

        Returns:
            List of idle connection info
        """
        threshold = idle_threshold or self.idle_timeout
        return [
            conn for conn in self._connections.values()
            if conn.is_idle(threshold)
        ]

    def get_metrics(self) -> ConnectionMetrics:
        """Get connection metrics."""
        return self._metrics

    def get_stats(self) -> Dict[str, Any]:
        """
        Get tracker statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "total_tracked": len(self._connections),
            "metrics": self._metrics.to_dict(),
            "health_checks_enabled": self.enable_health_checks,
            "auto_close_on_idle": self.auto_close_on_idle,
        }

    def _start_health_check_loop(self) -> None:
        """Start health check background loop."""
        if self._health_check_task and not self._health_check_task.done():
            return

        self._health_check_task = asyncio.create_task(self._health_check_loop())

    async def _health_check_loop(self) -> None:
        """Background health check loop."""
        logger.info("Starting health check loop")

        while True:
            try:
                await asyncio.sleep(self.health_check_interval)

                # Health check all connections
                connection_ids = list(self._connections.keys())
                for conn_id in connection_ids:
                    await self.health_check(conn_id)

                # Auto-close idle connections
                if self.auto_close_on_idle:
                    idle_connections = self.get_idle_connections()
                    for conn_info in idle_connections:
                        logger.info(
                            f"Closing idle connection: {conn_info.connection_id} "
                            f"(idle for {conn_info.idle_seconds:.1f}s)"
                        )
                        await self.close_connection(conn_info.connection_id)

            except asyncio.CancelledError:
                logger.info("Health check loop cancelled")
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")

    async def stop(self) -> None:
        """Stop tracker and close all connections."""
        logger.info("Stopping connection tracker")

        # Stop health check loop
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        await self.close_all_connections()


# Decorator for automatic connection tracking

def track_connection(
    tracker: ConnectionTracker,
    name: str,
    connection_type: ConnectionType = ConnectionType.CUSTOM,
):
    """
    Decorator to automatically track connections.

    Args:
        tracker: ConnectionTracker instance
        name: Connection name
        connection_type: Type of connection

    Example:
        tracker = ConnectionTracker()

        @track_connection(tracker, "database", ConnectionType.DATABASE)
        async def create_db_connection():
            return await create_connection()

        # Connection automatically tracked
        conn = await create_db_connection()
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create connection
            connection = await func(*args, **kwargs)

            # Register with tracker
            await tracker.register_connection(
                connection,
                name=name,
                connection_type=connection_type,
            )

            return connection

        return wrapper

    return decorator
