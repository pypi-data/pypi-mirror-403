"""Tests for MCP change notifications support."""

import pytest
from mcp.server import NotificationOptions
from point_topic_mcp.server_local import mcp, _enable_notifications
from point_topic_mcp.tools import register_tools
from point_topic_mcp.prompts import register_prompts


class TestNotificationsConfiguration:
    """Test that change notifications are properly configured."""

    def test_notifications_enabled_in_server(self):
        """Test that notifications are enabled when _enable_notifications is called."""
        # Register tools and prompts
        register_tools(mcp)
        register_prompts(mcp)
        
        # Enable notifications
        _enable_notifications(mcp)
        
        # Get initialization options
        init_options = mcp._mcp_server.create_initialization_options()
        
        # Verify capabilities
        assert init_options.capabilities is not None
        assert init_options.capabilities.tools is not None
        assert init_options.capabilities.tools.listChanged is True
        assert init_options.capabilities.prompts is not None
        assert init_options.capabilities.prompts.listChanged is True

    def test_tools_capability_listchanged(self):
        """Test that tools capability advertises listChanged support."""
        register_tools(mcp)
        _enable_notifications(mcp)
        
        init_options = mcp._mcp_server.create_initialization_options()
        
        assert init_options.capabilities.tools is not None
        assert init_options.capabilities.tools.listChanged is True

    def test_prompts_capability_listchanged(self):
        """Test that prompts capability advertises listChanged support."""
        register_prompts(mcp)
        _enable_notifications(mcp)
        
        init_options = mcp._mcp_server.create_initialization_options()
        
        assert init_options.capabilities.prompts is not None
        assert init_options.capabilities.prompts.listChanged is True

    def test_resources_capability_listchanged_disabled(self):
        """Test that resources capability has listChanged disabled (not yet implemented)."""
        _enable_notifications(mcp)
        
        init_options = mcp._mcp_server.create_initialization_options()
        
        # Resources may not exist yet, but if they do, listChanged should be False
        if init_options.capabilities.resources is not None:
            assert init_options.capabilities.resources.listChanged is False

    def test_server_name_and_version(self):
        """Test that server name and version are properly set."""
        _enable_notifications(mcp)
        
        init_options = mcp._mcp_server.create_initialization_options()
        
        assert init_options.server_name == "Point Topic MCP"
        assert init_options.server_version is not None
        assert len(init_options.server_version) > 0

    def test_instructions_present(self):
        """Test that server instructions are included."""
        init_options = mcp._mcp_server.create_initialization_options()
        
        assert init_options.instructions is not None
        assert "broadband" in init_options.instructions.lower()


class TestNotificationBehavior:
    """Test the behavior of notifications when capabilities change."""

    def test_tools_registered_before_notifications_enabled(self):
        """Test that tools are registered before notifications are enabled."""
        # This test ensures the initialization order is correct
        # Tools should be available in the initial list even with notifications enabled
        register_tools(mcp)
        register_prompts(mcp)
        _enable_notifications(mcp)
        
        # Verify that the server is properly configured for notifications
        # (list_tools and list_prompts are async, so we can't call them directly here)
        init_options = mcp._mcp_server.create_initialization_options()
        assert init_options.capabilities.tools is not None
        assert init_options.capabilities.prompts is not None

    def test_server_has_prompts_decorator(self):
        """Test that server has prompts capability through the decorator."""
        # Check that FastMCP has the prompt decorator
        assert hasattr(mcp, 'prompt')
        assert callable(mcp.prompt)


class TestNotificationOptionsIntegration:
    """Test that NotificationOptions integrate correctly with the server."""

    def test_notification_options_creation(self):
        """Test that NotificationOptions can be created with correct parameters."""
        options = NotificationOptions(
            prompts_changed=True,
            tools_changed=True,
            resources_changed=False,
        )
        
        assert options.prompts_changed is True
        assert options.tools_changed is True
        assert options.resources_changed is False

    def test_notification_options_defaults(self):
        """Test that NotificationOptions defaults to all False."""
        options = NotificationOptions()
        
        assert options.prompts_changed is False
        assert options.tools_changed is False
        assert options.resources_changed is False

    def test_get_capabilities_with_notifications(self):
        """Test that get_capabilities correctly uses notification options."""
        register_tools(mcp)
        register_prompts(mcp)
        
        # Create notification options with all notifications enabled
        notification_options = NotificationOptions(
            prompts_changed=True,
            tools_changed=True,
            resources_changed=False,
        )
        
        # Get capabilities with these options
        capabilities = mcp._mcp_server.get_capabilities(
            notification_options,
            {}  # experimental_capabilities
        )
        
        assert capabilities.tools is not None
        assert capabilities.tools.listChanged is True
        assert capabilities.prompts is not None
        assert capabilities.prompts.listChanged is True


class TestInitializationSequence:
    """Test the proper sequence of server initialization."""

    def test_full_initialization_with_notifications(self):
        """Test full server initialization with tools, prompts, and notifications."""
        # This mirrors what happens in main()
        register_tools(mcp)
        register_prompts(mcp)
        _enable_notifications(mcp)
        
        # Verify complete initialization
        init_options = mcp._mcp_server.create_initialization_options()
        
        assert init_options.server_name == "Point Topic MCP"
        assert init_options.capabilities.tools is not None
        assert init_options.capabilities.tools.listChanged is True
        assert init_options.capabilities.prompts is not None
        assert init_options.capabilities.prompts.listChanged is True

    def test_tools_available_after_registration(self):
        """Test that tools are properly registered after being added."""
        register_tools(mcp)
        
        # Verify tools are available by checking if the tool request handler is registered
        from mcp.types import ListToolsRequest
        assert ListToolsRequest in mcp._mcp_server.request_handlers

    def test_prompts_available_after_registration(self):
        """Test that prompts are properly registered after being added."""
        register_prompts(mcp)
        
        # Verify prompts are available by checking if the prompt request handler is registered
        from mcp.types import ListPromptsRequest
        assert ListPromptsRequest in mcp._mcp_server.request_handlers
