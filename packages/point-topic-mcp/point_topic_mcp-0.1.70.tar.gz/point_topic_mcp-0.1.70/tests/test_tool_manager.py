"""Unit tests for ToolManager."""

import pytest
from point_topic_mcp.core.tool_manager import ToolManager, RegisteredTool
from mcp.server.fastmcp import FastMCP


class TestToolManager:
    """Tests for ToolManager."""

    def test_initialization(self):
        """Test ToolManager initializes correctly."""
        mcp = FastMCP(name="Test")
        tm = ToolManager(mcp)

        assert tm.mcp == mcp
        assert len(tm.list_tools()) == 0

    def test_register_tool(self):
        """Test registering a tool."""
        mcp = FastMCP(name="Test")
        tm = ToolManager(mcp)

        def my_tool(param: str) -> str:
            """A test tool."""
            return f"Result: {param}"

        tm.register_tool(name="my_tool", description="A test tool", function=my_tool)

        # Check tool is registered
        assert tm.is_registered("my_tool")
        assert "my_tool" in tm.list_tools()

        # Check tool info
        tool = tm.get_tool("my_tool")
        assert tool is not None
        assert tool.name == "my_tool"
        assert tool.description == "A test tool"
        assert tool.function == my_tool

    def test_unregister_tool(self):
        """Test unregistering a tool."""
        mcp = FastMCP(name="Test")
        tm = ToolManager(mcp)

        def my_tool():
            pass

        # Register
        tm.register_tool("my_tool", "Test", my_tool)
        assert tm.is_registered("my_tool")

        # Unregister
        tm.unregister_tool("my_tool")
        assert not tm.is_registered("my_tool")
        assert "my_tool" not in tm.list_tools()

    def test_duplicate_registration_error(self):
        """Test error on duplicate tool registration."""
        mcp = FastMCP(name="Test")
        tm = ToolManager(mcp)

        def my_tool():
            pass

        # First registration should succeed
        tm.register_tool("my_tool", "Test", my_tool)

        # Second registration should fail
        with pytest.raises(ValueError, match="already registered"):
            tm.register_tool("my_tool", "Test", my_tool)

    def test_unregister_nonexistent_tool(self):
        """Test error on unregistering nonexistent tool."""
        mcp = FastMCP(name="Test")
        tm = ToolManager(mcp)

        with pytest.raises(ValueError, match="not registered"):
            tm.unregister_tool("nonexistent")

    def test_get_nonexistent_tool(self):
        """Test getting nonexistent tool returns None."""
        mcp = FastMCP(name="Test")
        tm = ToolManager(mcp)

        assert tm.get_tool("nonexistent") is None

    def test_list_tools(self):
        """Test listing multiple tools."""
        mcp = FastMCP(name="Test")
        tm = ToolManager(mcp)

        def tool1():
            pass

        def tool2():
            pass

        def tool3():
            pass

        tm.register_tool("tool1", "First tool", tool1)
        tm.register_tool("tool2", "Second tool", tool2)
        tm.register_tool("tool3", "Third tool", tool3)

        tools = tm.list_tools()
        assert len(tools) == 3
        assert set(tools.keys()) == {"tool1", "tool2", "tool3"}

    def test_register_with_annotations(self):
        """Test registering tool with annotations."""
        mcp = FastMCP(name="Test")
        tm = ToolManager(mcp)

        def my_tool():
            pass

        annotations = {"category": "data", "stability": "experimental"}
        tm.register_tool("my_tool", "Test tool", my_tool, annotations=annotations)

        tool = tm.get_tool("my_tool")
        assert tool.annotations == annotations


class TestRegisteredTool:
    """Tests for RegisteredTool dataclass."""

    def test_creation(self):
        """Test creating RegisteredTool."""

        def my_func():
            pass

        tool = RegisteredTool(name="test", description="Test tool", function=my_func)

        assert tool.name == "test"
        assert tool.description == "Test tool"
        assert tool.function == my_func
        assert tool.annotations is None

    def test_with_annotations(self):
        """Test RegisteredTool with annotations."""

        def my_func():
            pass

        annots = {"key": "value"}
        tool = RegisteredTool(
            name="test", description="Test tool", function=my_func, annotations=annots
        )

        assert tool.annotations == annots


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
