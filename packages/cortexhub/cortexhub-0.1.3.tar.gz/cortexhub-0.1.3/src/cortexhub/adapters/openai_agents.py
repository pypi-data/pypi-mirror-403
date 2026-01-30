"""OpenAI Agents SDK adapter for tool interception.

Intercepts tool execution by wrapping the function_tool decorator.

Architectural rules:
- Adapter is DUMB plumbing
- Adapter calls ONE SDK entrypoint: govern_execution()
- SDK orchestrates everything
- No governance logic in adapter
"""

import json
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable

import structlog

from cortexhub.adapters.base import ToolAdapter
from cortexhub.pipeline import govern_execution

if TYPE_CHECKING:
    from cortexhub.client import CortexHub

logger = structlog.get_logger(__name__)

# Attribute names for storing originals
_ORIGINAL_FUNCTION_TOOL_ATTR = "__cortexhub_original_function_tool__"
_PATCHED_ATTR = "__cortexhub_patched__"


class OpenAIAgentsAdapter(ToolAdapter):
    """Adapter for OpenAI Agents SDK.
    
    Wraps the function_tool decorator to intercept tool creation
    and wrap the on_invoke_tool method for governance.
    
    Key properties:
    - Adapter is dumb plumbing
    - Calls SDK entrypoint, doesn't implement governance
    - Wraps decorator to intercept all tools
    - Async-safe via SDK
    """
    
    @property
    def framework_name(self) -> str:
        return "openai_agents"
    
    def _get_framework_modules(self) -> list[str]:
        return ["agents", "openai_agents"]
    
    def patch(self) -> None:
        """Patch OpenAI Agents by wrapping the function_tool decorator."""
        try:
            import agents
            import agents.tool as tool_module
            
            # Check if already patched
            if getattr(tool_module, _PATCHED_ATTR, False):
                logger.info("OpenAI Agents already patched")
                return

            cortex_hub = self.cortex_hub
            tools = self._discover_tools()
            if tools:
                cortex_hub.backend.register_tool_inventory(
                    agent_id=cortex_hub.agent_id,
                    framework=self.framework_name,
                    tools=tools,
                )
            
            # Store original function_tool decorator
            if not hasattr(tool_module, _ORIGINAL_FUNCTION_TOOL_ATTR):
                setattr(tool_module, _ORIGINAL_FUNCTION_TOOL_ATTR, tool_module.function_tool)
            
            original_function_tool = getattr(tool_module, _ORIGINAL_FUNCTION_TOOL_ATTR)

            def patched_function_tool(
                func: Callable | None = None,
                *,
                name_override: str | None = None,
                description_override: str | None = None,
                use_docstring_info: bool = True,
                failure_error_function: Callable | None = None,
                strict_mode: bool = True,
                is_enabled: bool | Callable = True,
            ):
                """Wrapped function_tool that adds CortexHub governance."""
                
                def decorator(fn: Callable) -> Any:
                    # Create the original FunctionTool
                    tool = original_function_tool(
                        fn,
                        name_override=name_override,
                        description_override=description_override,
                        use_docstring_info=use_docstring_info,
                        failure_error_function=failure_error_function,
                        strict_mode=strict_mode,
                        is_enabled=is_enabled,
                    )
                    
                    # Wrap on_invoke_tool with governance
                    original_invoke = tool.on_invoke_tool
                    tool_name = tool.name
                    tool_description = tool.description
                    
                    async def governed_invoke(ctx, input_json: str) -> Any:
                        """Governed tool invocation."""
                        try:
                            args = json.loads(input_json) if input_json else {}
                        except json.JSONDecodeError:
                            args = {"_raw": input_json}
                        
                        tool_metadata = {
                            "name": tool_name,
                            "description": tool_description,
                            "framework": "openai_agents",
                        }
                        
                        # Create governed function
                        governed_fn = govern_execution(
                            tool_fn=lambda **kw: original_invoke(ctx, input_json),
                            tool_metadata=tool_metadata,
                            cortex_hub=cortex_hub,
                        )
                        
                        # Execute with governance
                        result = governed_fn(**args)
                        # Handle async
                        if hasattr(result, '__await__'):
                            result = await result
                        return result
                    
                    # Replace on_invoke_tool with governed version
                    # FunctionTool is a dataclass, so we need to create a new instance
                    from agents.tool import FunctionTool
                    
                    governed_tool = FunctionTool(
                        name=tool.name,
                        description=tool.description,
                        params_json_schema=tool.params_json_schema,
                        on_invoke_tool=governed_invoke,
                        strict_json_schema=tool.strict_json_schema,
                        is_enabled=tool.is_enabled,
                        tool_input_guardrails=tool.tool_input_guardrails,
                        tool_output_guardrails=tool.tool_output_guardrails,
                    )
                    
                    return governed_tool
                
                # Handle @function_tool vs @function_tool()
                if func is not None:
                    return decorator(func)
                return decorator

            # Apply patch
            tool_module.function_tool = patched_function_tool
            agents.function_tool = patched_function_tool
            setattr(tool_module, _PATCHED_ATTR, True)

            logger.info("OpenAI Agents adapter patched successfully")
            
        except ImportError:
            logger.debug("OpenAI Agents SDK not installed, skipping")
        except Exception as e:
            logger.error("Failed to patch OpenAI Agents", error=str(e))
    
    def unpatch(self) -> None:
        """Restore original function_tool decorator."""
        try:
            import agents
            import agents.tool as tool_module
            
            if not hasattr(tool_module, _ORIGINAL_FUNCTION_TOOL_ATTR):
                logger.debug("OpenAI Agents not patched, nothing to restore")
                return
            
            original = getattr(tool_module, _ORIGINAL_FUNCTION_TOOL_ATTR)
            tool_module.function_tool = original
            agents.function_tool = original
            setattr(tool_module, _PATCHED_ATTR, False)
            
            logger.info("OpenAI Agents adapter unpatched")
        except ImportError:
            pass
    
    def intercept(self, tool_fn, tool_name, args, **kwargs):
        """Not used - governance happens via wrapped decorator."""
        raise NotImplementedError("Use govern_execution via wrapped decorator")

    def _discover_tools(self) -> list[dict[str, Any]]:
        """Discover tools from OpenAI Agents SDK (best-effort)."""
        return []
