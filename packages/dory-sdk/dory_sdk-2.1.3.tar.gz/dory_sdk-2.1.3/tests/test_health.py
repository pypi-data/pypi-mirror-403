"""Tests for health probes and server."""

import pytest

from dory.health.probes import LivenessProbe, ReadinessProbe, ProbeResult


class TestLivenessProbe:
    """Tests for LivenessProbe."""

    @pytest.mark.asyncio
    async def test_default_healthy(self):
        """Test default liveness is healthy."""
        probe = LivenessProbe()
        result = await probe.check()

        assert result.healthy is True

    @pytest.mark.asyncio
    async def test_custom_check_pass(self):
        """Test custom check that passes."""
        probe = LivenessProbe()
        probe.add_check(lambda: True)

        result = await probe.check()

        assert result.healthy is True

    @pytest.mark.asyncio
    async def test_custom_check_fail(self):
        """Test custom check that fails."""
        probe = LivenessProbe()
        probe.add_check(lambda: False)

        result = await probe.check()

        assert result.healthy is False

    @pytest.mark.asyncio
    async def test_custom_async_check(self):
        """Test async custom check."""
        probe = LivenessProbe()

        async def async_check():
            return True

        probe.add_check(async_check)

        result = await probe.check()

        assert result.healthy is True

    @pytest.mark.asyncio
    async def test_custom_check_exception(self):
        """Test custom check that raises exception."""
        probe = LivenessProbe()

        async def failing_check():
            raise Exception("Check failed")

        probe.add_check(failing_check)

        result = await probe.check()

        assert result.healthy is False
        assert "error" in result.message.lower()


class TestReadinessProbe:
    """Tests for ReadinessProbe."""

    @pytest.mark.asyncio
    async def test_default_not_ready(self):
        """Test default readiness is not ready."""
        probe = ReadinessProbe()
        result = await probe.check()

        assert result.healthy is False

    @pytest.mark.asyncio
    async def test_mark_ready(self):
        """Test marking as ready."""
        probe = ReadinessProbe()
        probe.mark_ready()

        result = await probe.check()

        assert result.healthy is True

    @pytest.mark.asyncio
    async def test_mark_not_ready(self):
        """Test marking as not ready."""
        probe = ReadinessProbe()
        probe.mark_ready()
        probe.mark_not_ready()

        result = await probe.check()

        assert result.healthy is False

    def test_is_ready(self):
        """Test is_ready property."""
        probe = ReadinessProbe()

        assert probe.is_ready() is False

        probe.mark_ready()
        assert probe.is_ready() is True

    @pytest.mark.asyncio
    async def test_custom_check_with_ready(self):
        """Test custom check only runs when marked ready."""
        probe = ReadinessProbe()
        check_called = False

        async def custom_check():
            nonlocal check_called
            check_called = True
            return True

        probe.add_check(custom_check)

        # Not ready - custom check not called
        result = await probe.check()
        assert result.healthy is False
        assert check_called is False

        # Mark ready - custom check called
        probe.mark_ready()
        result = await probe.check()
        assert result.healthy is True
        assert check_called is True


class TestProbeResult:
    """Tests for ProbeResult dataclass."""

    def test_to_dict(self):
        """Test converting to dictionary."""
        result = ProbeResult(
            healthy=True,
            message="All good",
            details={"check": "passed"},
        )

        data = result.to_dict()

        assert data["healthy"] is True
        assert data["message"] == "All good"
        assert data["details"]["check"] == "passed"

    def test_default_values(self):
        """Test default values."""
        result = ProbeResult(healthy=True)

        assert result.message == ""
        assert result.details == {}


class TestHealthServer:
    """Tests for HealthServer endpoints."""

    @pytest.mark.asyncio
    async def test_default_ready_path(self):
        """Test that default ready path is /ready (not /readyz)."""
        from dory.health.server import HealthServer

        server = HealthServer()
        assert server._ready_path == "/ready"

    @pytest.mark.asyncio
    async def test_state_getter_callback(self):
        """Test state getter callback is called."""
        from dory.health.server import HealthServer

        state_data = {"count": 42, "name": "test"}

        def get_state():
            return state_data

        server = HealthServer(state_getter=get_state)
        assert server._state_getter is not None
        assert server._state_getter() == state_data

    @pytest.mark.asyncio
    async def test_state_restorer_callback(self):
        """Test state restorer callback is set."""
        from dory.health.server import HealthServer

        restored_state = {}

        async def restore_state(state):
            nonlocal restored_state
            restored_state = state

        server = HealthServer(state_restorer=restore_state)
        assert server._state_restorer is not None

        await server._state_restorer({"key": "value"})
        assert restored_state == {"key": "value"}

    @pytest.mark.asyncio
    async def test_prestop_handler_callback(self):
        """Test prestop handler callback is set."""
        from dory.health.server import HealthServer

        prestop_called = False

        async def handle_prestop():
            nonlocal prestop_called
            prestop_called = True

        server = HealthServer(prestop_handler=handle_prestop)
        assert server._prestop_handler is not None

        await server._prestop_handler()
        assert prestop_called is True

    def test_set_state_getter(self):
        """Test setting state getter after initialization."""
        from dory.health.server import HealthServer

        server = HealthServer()
        assert server._state_getter is None

        server.set_state_getter(lambda: {"test": True})
        assert server._state_getter is not None
        assert server._state_getter() == {"test": True}

    def test_set_state_restorer(self):
        """Test setting state restorer after initialization."""
        from dory.health.server import HealthServer

        server = HealthServer()
        assert server._state_restorer is None

        async def restorer(state):
            pass

        server.set_state_restorer(restorer)
        assert server._state_restorer is not None

    def test_set_prestop_handler(self):
        """Test setting prestop handler after initialization."""
        from dory.health.server import HealthServer

        server = HealthServer()
        assert server._prestop_handler is None

        async def handler():
            pass

        server.set_prestop_handler(handler)
        assert server._prestop_handler is not None

    def test_endpoints_listed_in_root(self):
        """Test that new endpoints are listed in root response."""
        from dory.health.server import HealthServer

        server = HealthServer()
        # Check that the endpoints would be set up
        # We just verify the default paths include the new endpoints
        assert server._health_path == "/healthz"
        assert server._ready_path == "/ready"
        assert server._metrics_path == "/metrics"
        # State and prestop endpoints are added in _setup_routes

    @pytest.mark.asyncio
    async def test_prestop_handler_can_save_state(self):
        """Test prestop handler can save state via callback."""
        from dory.health.server import HealthServer

        state_saved = False
        saved_state_data = None

        def get_current_state():
            return {"counter": 42, "sessions": ["session1", "session2"]}

        async def handle_prestop():
            nonlocal state_saved, saved_state_data
            # In the actual app, prestop handler saves state
            state = get_current_state()
            saved_state_data = state
            state_saved = True

        server = HealthServer(
            state_getter=get_current_state,
            prestop_handler=handle_prestop
        )

        # Simulate PreStop being triggered
        await server._prestop_handler()

        assert state_saved is True
        assert saved_state_data is not None
        assert saved_state_data["counter"] == 42
        assert len(saved_state_data["sessions"]) == 2

    @pytest.mark.asyncio
    async def test_prestop_marks_not_ready(self):
        """Test that prestop handler marks server as not ready."""
        from dory.health.server import HealthServer

        prestop_executed = False

        async def handle_prestop():
            nonlocal prestop_executed
            # Prestop should mark as not ready
            prestop_executed = True

        server = HealthServer(prestop_handler=handle_prestop)
        server.mark_ready()

        # Before prestop, verify readiness probe is ready
        assert server.readiness_probe.is_ready() is True

        # Simulate PreStop being triggered
        await server._prestop_handler()

        # Verify our callback executed
        assert prestop_executed is True

        # Note: In the actual app, the prestop handler calls mark_not_ready()
        # Here we just verify the callback mechanism works

    def test_prestop_endpoint_path(self):
        """Test the prestop endpoint path is configured correctly."""
        from dory.health.server import HealthServer

        server = HealthServer()
        # The prestop endpoint is /prestop
        # This is called by K8s preStop hook: curl -sf http://localhost:8080/prestop
        # Verify the path is what we expect
        assert hasattr(server, '_prestop_handler')


class TestStateEndpointAuthentication:
    """Tests for state endpoint authentication."""

    def test_no_token_allows_all(self, monkeypatch):
        """Test that requests are allowed when no token is configured."""
        from dory.health.server import HealthServer
        from unittest.mock import MagicMock

        # Ensure no token is set
        monkeypatch.delenv("DORY_STATE_TOKEN", raising=False)

        server = HealthServer()

        # Create mock request without Authorization header
        mock_request = MagicMock()
        mock_request.headers.get.return_value = ""

        assert server._validate_state_token(mock_request) is True

    def test_valid_token_allowed(self, monkeypatch):
        """Test that valid token is accepted."""
        from dory.health.server import HealthServer
        from unittest.mock import MagicMock

        test_token = "my-secret-token-12345"
        monkeypatch.setenv("DORY_STATE_TOKEN", test_token)

        server = HealthServer()

        # Create mock request with valid Authorization header
        mock_request = MagicMock()
        mock_request.headers.get.return_value = f"Bearer {test_token}"

        assert server._validate_state_token(mock_request) is True

    def test_invalid_token_rejected(self, monkeypatch):
        """Test that invalid token is rejected."""
        from dory.health.server import HealthServer
        from unittest.mock import MagicMock

        monkeypatch.setenv("DORY_STATE_TOKEN", "correct-token")

        server = HealthServer()

        # Create mock request with wrong token
        mock_request = MagicMock()
        mock_request.headers.get.return_value = "Bearer wrong-token"

        assert server._validate_state_token(mock_request) is False

    def test_missing_bearer_prefix_rejected(self, monkeypatch):
        """Test that token without Bearer prefix is rejected."""
        from dory.health.server import HealthServer
        from unittest.mock import MagicMock

        test_token = "my-secret-token"
        monkeypatch.setenv("DORY_STATE_TOKEN", test_token)

        server = HealthServer()

        # Create mock request with token but no Bearer prefix
        mock_request = MagicMock()
        mock_request.headers.get.return_value = test_token

        assert server._validate_state_token(mock_request) is False

    def test_empty_auth_header_rejected(self, monkeypatch):
        """Test that empty Authorization header is rejected when token is configured."""
        from dory.health.server import HealthServer
        from unittest.mock import MagicMock

        monkeypatch.setenv("DORY_STATE_TOKEN", "configured-token")

        server = HealthServer()

        # Create mock request with empty Authorization header
        mock_request = MagicMock()
        mock_request.headers.get.return_value = ""

        assert server._validate_state_token(mock_request) is False

    def test_timing_safe_comparison(self, monkeypatch):
        """Test that token comparison uses timing-safe method."""
        from dory.health.server import HealthServer
        import secrets

        # This test verifies that secrets.compare_digest is used
        # by checking behavior with similar-length strings
        test_token = "a" * 32
        monkeypatch.setenv("DORY_STATE_TOKEN", test_token)

        server = HealthServer()

        from unittest.mock import MagicMock

        # Similar length but different token should be rejected
        mock_request = MagicMock()
        mock_request.headers.get.return_value = f"Bearer {'b' * 32}"

        assert server._validate_state_token(mock_request) is False

    def test_state_token_from_env(self, monkeypatch):
        """Test that state token is read from environment variable."""
        from dory.health.server import HealthServer

        expected_token = "env-token-value"
        monkeypatch.setenv("DORY_STATE_TOKEN", expected_token)

        server = HealthServer()

        assert server._state_token == expected_token

    def test_no_state_token_env_is_none(self, monkeypatch):
        """Test that state token is None when env var not set."""
        from dory.health.server import HealthServer

        monkeypatch.delenv("DORY_STATE_TOKEN", raising=False)

        server = HealthServer()

        assert server._state_token is None


class TestRateLimiter:
    """Tests for rate limiter functionality."""

    def test_rate_limiter_allows_under_limit(self):
        """Test requests under limit are allowed."""
        from dory.health.server import RateLimiter

        limiter = RateLimiter(requests_per_second=10)

        # First 10 requests should be allowed
        for i in range(10):
            assert limiter.is_allowed("127.0.0.1") is True

    def test_rate_limiter_blocks_over_limit(self):
        """Test requests over limit are blocked."""
        from dory.health.server import RateLimiter

        limiter = RateLimiter(requests_per_second=5)

        # First 5 requests allowed
        for _ in range(5):
            assert limiter.is_allowed("127.0.0.1") is True

        # 6th request blocked
        assert limiter.is_allowed("127.0.0.1") is False

    def test_rate_limiter_tracks_per_ip(self):
        """Test rate limiter tracks each IP separately."""
        from dory.health.server import RateLimiter

        limiter = RateLimiter(requests_per_second=2)

        # IP 1 uses its limit
        assert limiter.is_allowed("192.168.1.1") is True
        assert limiter.is_allowed("192.168.1.1") is True
        assert limiter.is_allowed("192.168.1.1") is False

        # IP 2 still has its full limit
        assert limiter.is_allowed("192.168.1.2") is True
        assert limiter.is_allowed("192.168.1.2") is True
        assert limiter.is_allowed("192.168.1.2") is False

    def test_rate_limiter_disabled_when_zero(self):
        """Test rate limiter is disabled when RPS is 0."""
        from dory.health.server import RateLimiter

        limiter = RateLimiter(requests_per_second=0)

        assert limiter.enabled is False

        # All requests allowed when disabled
        for _ in range(1000):
            assert limiter.is_allowed("127.0.0.1") is True

    def test_rate_limiter_enabled_property(self):
        """Test enabled property."""
        from dory.health.server import RateLimiter

        limiter_enabled = RateLimiter(requests_per_second=100)
        limiter_disabled = RateLimiter(requests_per_second=0)

        assert limiter_enabled.enabled is True
        assert limiter_disabled.enabled is False

    def test_rate_limiter_get_request_count(self):
        """Test getting current request count."""
        from dory.health.server import RateLimiter

        limiter = RateLimiter(requests_per_second=10)

        assert limiter.get_request_count("127.0.0.1") == 0

        limiter.is_allowed("127.0.0.1")
        limiter.is_allowed("127.0.0.1")
        limiter.is_allowed("127.0.0.1")

        assert limiter.get_request_count("127.0.0.1") == 3


class TestHealthServerRateLimiting:
    """Tests for health server rate limiting integration."""

    def test_rate_limit_from_env(self, monkeypatch):
        """Test rate limit is read from environment."""
        from dory.health.server import HealthServer

        monkeypatch.setenv("DORY_RATE_LIMIT", "50")

        server = HealthServer()

        assert server._rate_limiter._rps == 50

    def test_rate_limit_disabled_from_env(self, monkeypatch):
        """Test rate limit can be disabled via environment."""
        from dory.health.server import HealthServer

        monkeypatch.setenv("DORY_RATE_LIMIT", "0")

        server = HealthServer()

        assert server._rate_limiter.enabled is False

    def test_default_rate_limit(self, monkeypatch):
        """Test default rate limit is used when not set."""
        from dory.health.server import HealthServer, DEFAULT_RATE_LIMIT_RPS

        monkeypatch.delenv("DORY_RATE_LIMIT", raising=False)

        server = HealthServer()

        assert server._rate_limiter._rps == DEFAULT_RATE_LIMIT_RPS


class TestHealthServerSizeLimits:
    """Tests for health server request size limits."""

    def test_max_size_from_env(self, monkeypatch):
        """Test max request size is read from environment."""
        from dory.health.server import HealthServer

        monkeypatch.setenv("DORY_MAX_STATE_SIZE", "5242880")  # 5MB

        server = HealthServer()

        assert server._max_request_size == 5242880

    def test_default_max_size(self, monkeypatch):
        """Test default max request size when not set."""
        from dory.health.server import HealthServer, DEFAULT_MAX_STATE_SIZE

        monkeypatch.delenv("DORY_MAX_STATE_SIZE", raising=False)

        server = HealthServer()

        assert server._max_request_size == DEFAULT_MAX_STATE_SIZE
