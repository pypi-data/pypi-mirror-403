import unittest
from unittest.mock import MagicMock, Mock, patch

import fastmcp.server.dependencies
import fastmcp.tools.tool

from devopness_mcp_server.lib.environment import EnvironmentVariables
from devopness_mcp_server.lib.patch import (
    patch_oauth_middleware_and_routes,
    patch_server_context_injection,
)
from devopness_mcp_server.lib.types import Server, ServerContext


class TestContextInjectionPatch(unittest.TestCase):
    """Test the critical context injection monkey patch."""

    def test_fastmcp_modules_have_get_context_functions(self) -> None:
        """
        CRITICAL: Validate FastMCP still has the internal APIs we patch.

        If this test fails after a FastMCP update, it means they've changed
        their internal module structure and our patches will break.
        """
        # These internal APIs must exist for our patches to work
        self.assertTrue(
            hasattr(fastmcp.tools.tool, "get_context"),
            "fastmcp.tools.tool.get_context no longer exists! "
            "Our context injection patch will fail.",
        )

        self.assertTrue(
            hasattr(fastmcp.server.dependencies, "get_context"),
            "fastmcp.server.dependencies.get_context no longer exists! "
            "Our context injection patch will fail.",
        )

        # They should be callable
        self.assertTrue(
            callable(fastmcp.tools.tool.get_context),  # type: ignore[attr-defined]
            "fastmcp.tools.tool.get_context is not callable",
        )

        self.assertTrue(
            callable(fastmcp.server.dependencies.get_context),
            "fastmcp.server.dependencies.get_context is not callable",
        )

    def test_context_injection_patch_replaces_get_context_functions(self) -> None:
        """
        Test that our patch successfully replaces FastMCP's get_context functions.
        """
        # Store original functions
        original_tool_get_context = fastmcp.tools.tool.get_context  # type: ignore[attr-defined]
        original_deps_get_context = fastmcp.server.dependencies.get_context

        # Create mock server
        mock_server = Mock(spec=Server)
        mock_server.logger = Mock()

        try:
            # Apply our patch
            patch_server_context_injection(mock_server)

            # Verify functions were replaced
            self.assertNotEqual(
                fastmcp.tools.tool.get_context,  # type: ignore[attr-defined]
                original_tool_get_context,
                "fastmcp.tools.tool.get_context was not replaced by our patch",
            )

            self.assertNotEqual(
                fastmcp.server.dependencies.get_context,
                original_deps_get_context,
                "fastmcp.server.dependencies.get_context was not replaced by our patch",
            )

            # Verify logger was called (patch was applied)
            mock_server.logger.info.assert_called_once_with(
                "Custom ServerContext injection patch applied"
            )

        finally:
            # Restore original functions
            fastmcp.tools.tool.get_context = original_tool_get_context  # type: ignore[attr-defined]
            fastmcp.server.dependencies.get_context = original_deps_get_context

    @patch("devopness_mcp_server.lib.patch.ServerContext")
    def test_patched_get_context_returns_server_context(
        self,
        mock_server_context_class: MagicMock,
    ) -> None:
        """
        Test that our patched get_context function returns ServerContext instances.
        """
        # Setup mocks
        mock_original_context = Mock()
        mock_server_context_instance = Mock()
        mock_server_context_class.return_value = mock_server_context_instance

        mock_server = Mock(spec=Server)
        mock_server.logger = Mock()

        # Store original function
        original_get_context = fastmcp.tools.tool.get_context  # type: ignore[attr-defined]

        try:
            # Mock the original get_context to return our mock context
            with patch.object(
                fastmcp.tools.tool, "get_context", return_value=mock_original_context
            ):
                # Apply our patch
                patch_server_context_injection(mock_server)

                # Call the patched function
                result = fastmcp.tools.tool.get_context()  # type: ignore[attr-defined]

                # Verify ServerContext was instantiated with original context
                mock_server_context_class.assert_called_once_with(mock_original_context)

                # Verify it returns our ServerContext instance
                self.assertEqual(result, mock_server_context_instance)

        finally:
            # Restore original function
            fastmcp.tools.tool.get_context = original_get_context  # type: ignore[attr-defined]

    def test_server_context_provides_required_fields(self) -> None:
        """
        Test that ServerContext provides access to all required server fields.
        """
        # Create mock base context
        mock_base_context = Mock()
        mock_fastmcp = Mock(spec=Server)
        mock_devopness = Mock()
        mock_fastmcp.devopness = mock_devopness
        mock_base_context.fastmcp = mock_fastmcp
        mock_base_context._tokens = "mock_tokens"
        mock_base_context._notification_queue = Mock()

        # Create ServerContext
        server_context = ServerContext(mock_base_context)

        # Verify required fields are accessible
        self.assertTrue(
            hasattr(server_context, "server"),
            "ServerContext doesn't provide 'server' field - "
            "tools can't access server instance",
        )

        self.assertTrue(
            hasattr(server_context, "devopness"),
            "ServerContext doesn't provide 'devopness' field - "
            "tools can't access API client",
        )

        # Verify server is properly cast
        self.assertEqual(
            server_context.server,
            mock_fastmcp,
            "ServerContext.server doesn't point to the FastMCP server instance",
        )

        # Verify devopness client is accessible
        self.assertEqual(
            server_context.devopness,
            mock_devopness,
            "ServerContext.devopness doesn't point to the Devopness API client",
        )


class TestOAuthMiddlewarePatch(unittest.TestCase):
    """Test the critical OAuth middleware and routes patch."""

    @patch("devopness_mcp_server.lib.patch.create_introspection_verifier")
    def test_oauth_patch_creates_token_verifier(
        self,
        mock_create_verifier: MagicMock,
    ) -> None:
        """
        Test that OAuth patch successfully creates token verifier with routes.
        """
        # Setup mocks
        mock_token_verifier = Mock()
        mock_create_verifier.return_value = mock_token_verifier

        mock_server = Mock(spec=Server)
        mock_server.logger = Mock()
        mock_server.env = Mock(spec=EnvironmentVariables)
        mock_server.env.DEVOPNESS_MCP_AUTH_SERVER_INTROSPECTION_URL = (
            "https://test.introspect"
        )
        mock_server.env.DEVOPNESS_MCP_SERVER_URL = "https://test.server"

        # Apply patch
        patch_oauth_middleware_and_routes(mock_server)

        # Verify token verifier was created
        mock_create_verifier.assert_called_once()
        call_args = mock_create_verifier.call_args

        # Verify endpoint parameter
        self.assertEqual(call_args.kwargs["endpoint"], "https://test.introspect")
        self.assertEqual(call_args.kwargs["server_url"], "https://test.server")

        # Verify routes handler was provided
        self.assertIn("get_routes_handler", call_args.kwargs)
        self.assertTrue(callable(call_args.kwargs["get_routes_handler"]))

        # Verify middleware handler was provided
        self.assertIn("get_middleware_handler", call_args.kwargs)
        self.assertTrue(callable(call_args.kwargs["get_middleware_handler"]))

        # Verify server.auth was set
        self.assertEqual(mock_server.auth, mock_token_verifier)

    @patch("devopness_mcp_server.lib.patch.create_introspection_verifier")
    def test_oauth_routes_are_properly_configured(
        self,
        mock_create_verifier: MagicMock,
    ) -> None:
        """
        Test that OAuth routes are properly configured with correct paths and methods.
        """
        mock_server = Mock(spec=Server)
        mock_server.logger = Mock()
        mock_server.env = Mock(spec=EnvironmentVariables)
        mock_server.env.DEVOPNESS_MCP_AUTH_SERVER_INTROSPECTION_URL = (
            "https://test.introspect"
        )
        mock_server.env.DEVOPNESS_MCP_SERVER_URL = "https://test.server"

        # Apply patch
        patch_oauth_middleware_and_routes(mock_server)

        # Get the routes handler
        call_args = mock_create_verifier.call_args
        routes_handler = call_args.kwargs["get_routes_handler"]

        # Call the routes handler to get routes
        routes = routes_handler("/test")

        # Verify we have the expected OAuth routes
        expected_paths = [
            "/.well-known/oauth-protected-resource",
            "/.well-known/oauth-authorization-server",
            "/register",
            "/authorize",
            "/token",
        ]

        actual_paths = [route.path for route in routes]

        for expected_path in expected_paths:
            self.assertIn(
                expected_path,
                actual_paths,
                f"Missing required OAuth route: {expected_path}",
            )

        # Verify route count (should be exactly 5 routes)
        self.assertEqual(
            len(routes),
            5,
            f"Expected 5 OAuth routes, got {len(routes)}: {actual_paths}",
        )

    @patch("devopness_mcp_server.lib.patch.create_introspection_verifier")
    def test_oauth_middleware_is_properly_configured(
        self,
        mock_create_verifier: MagicMock,
    ) -> None:
        """
        Test that OAuth middleware is properly configured.
        """
        mock_server = Mock(spec=Server)
        mock_server.logger = Mock()
        mock_server.env = Mock(spec=EnvironmentVariables)
        mock_server.env.DEVOPNESS_MCP_AUTH_SERVER_INTROSPECTION_URL = (
            "https://test.introspect"
        )
        mock_server.env.DEVOPNESS_MCP_SERVER_URL = "https://test.server"

        # Apply patch
        patch_oauth_middleware_and_routes(mock_server)

        # Get the middleware handler
        call_args = mock_create_verifier.call_args
        middleware_handler = call_args.kwargs["get_middleware_handler"]

        # Call the middleware handler to get middleware
        middleware_stack = middleware_handler()

        # Verify we have middleware
        self.assertGreater(
            len(middleware_stack), 0, "No middleware was configured for OAuth"
        )

        # Should have AuthenticationMiddleware and AuthContextMiddleware
        middleware_names = [mw.cls.__name__ for mw in middleware_stack]

        self.assertIn(
            "AuthenticationMiddleware",
            middleware_names,
            "AuthenticationMiddleware not found in OAuth middleware stack",
        )

        self.assertIn(
            "AuthContextMiddleware",
            middleware_names,
            "AuthContextMiddleware not found in OAuth middleware stack",
        )


class TestPatchSystemIntegration(unittest.TestCase):
    """Integration tests for the complete patch system."""

    def test_both_patches_can_be_applied_together(self) -> None:
        """
        Test that both patches can be applied without conflicts.
        """
        # Store original functions
        original_tool_get_context = fastmcp.tools.tool.get_context  # type: ignore[attr-defined]
        original_deps_get_context = fastmcp.server.dependencies.get_context

        try:
            # Create mock server with all required fields
            mock_server = Mock(spec=Server)
            mock_server.logger = Mock()
            mock_server.env = Mock(spec=EnvironmentVariables)
            mock_server.env.DEVOPNESS_MCP_AUTH_SERVER_INTROSPECTION_URL = (
                "https://test.introspect"
            )
            mock_server.env.DEVOPNESS_MCP_SERVER_URL = "https://test.server"

            # Apply both patches
            with patch(
                "devopness_mcp_server.lib.patch.create_introspection_verifier"
            ) as mock_verifier:
                mock_verifier.return_value = Mock()

                # Should not raise any exceptions
                patch_server_context_injection(mock_server)
                patch_oauth_middleware_and_routes(mock_server)

            # Verify both patches were applied
            self.assertEqual(mock_server.logger.info.call_count, 3)
            self.assertIsNotNone(mock_server.auth)

        finally:
            # Restore original functions
            fastmcp.tools.tool.get_context = original_tool_get_context  # type: ignore[attr-defined]
            fastmcp.server.dependencies.get_context = original_deps_get_context

    def test_patch_system_resilience_to_fastmcp_changes(self) -> None:
        """
        Test scenarios that would break our patch system if FastMCP changes.

        This test documents the specific FastMCP dependencies we rely on.
        If FastMCP changes these, our patches will break and need updates.
        """
        # Critical dependencies that could break:

        # 1. Internal module structure
        self.assertTrue(hasattr(fastmcp, "tools"), "fastmcp.tools module missing")
        self.assertTrue(
            hasattr(fastmcp.tools, "tool"), "fastmcp.tools.tool module missing"
        )
        self.assertTrue(hasattr(fastmcp, "server"), "fastmcp.server module missing")
        self.assertTrue(
            hasattr(fastmcp.server, "dependencies"),
            "fastmcp.server.dependencies module missing",
        )

        # 2. get_context function signatures
        import inspect  # noqa: PLC0415

        tool_get_context_sig = inspect.signature(fastmcp.tools.tool.get_context)  # type: ignore[attr-defined]
        deps_get_context_sig = inspect.signature(
            fastmcp.server.dependencies.get_context
        )

        self.assertEqual(
            len(tool_get_context_sig.parameters),
            0,
            "fastmcp.tools.tool.get_context signature changed: "
            f"{tool_get_context_sig}.",
        )

        self.assertEqual(
            len(deps_get_context_sig.parameters),
            2,  # *args, **kwargs
            "fastmcp.server.dependencies.get_context signature changed: "
            f"{deps_get_context_sig}.",
        )
