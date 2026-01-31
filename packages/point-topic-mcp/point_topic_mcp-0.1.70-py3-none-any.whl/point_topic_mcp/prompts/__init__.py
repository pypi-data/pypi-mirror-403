"""MCP prompts module with auto-discovery and registration.

Provides reusable message templates and workflows for MCP clients.
Automatically discovers and registers prompt functions.
"""

import importlib
import pkgutil
import inspect
from pathlib import Path


def register_prompts(mcp):
    """Register all MCP prompts by auto-discovering functions in prompt modules.

    Automatically finds all Python modules in the prompts directory and registers
    every public function (not starting with _) as an MCP prompt.

    Just create a .py file with prompt functions - no wrapper functions or decorators needed!

    Args:
        mcp: FastMCP instance to register prompts with
    """
    # Get the prompts package directory
    prompts_dir = Path(__file__).parent

    # Discover all Python modules in this directory
    for module_info in pkgutil.iter_modules([str(prompts_dir)]):
        # Skip __init__ and any private modules
        if module_info.name.startswith("_"):
            continue

        try:
            # Import the module
            module = importlib.import_module(
                f".{module_info.name}", package="point_topic_mcp.prompts"
            )

            # Find all functions defined in this module (not imported from elsewhere)
            prompt_count = 0
            for name, obj in inspect.getmembers(module, inspect.isfunction):
                # Skip private functions
                if name.startswith("_"):
                    continue

                # Only register functions actually defined in this module (not imported)
                if obj.__module__ == module.__name__:
                    mcp.prompt()(obj)
                    prompt_count += 1

            if prompt_count > 0:
                print(
                    f"[MCP] Registered {prompt_count} prompts from {module_info.name}"
                )

        except Exception as e:
            print(f"[MCP] Warning: Failed to load prompts from {module_info.name}: {e}")
            import traceback

            traceback.print_exc()
            # Continue with other modules even if one fails


__all__ = ["register_prompts"]
