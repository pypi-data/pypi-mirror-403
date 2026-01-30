"""Claude Agent SDK adapter for tool interception.

The Claude Agent SDK provides agentic capabilities including:
- Computer use (bash, files, code)
- Custom MCP tools via @tool decorator
- Subagents for parallelization
- Hooks for pre/post tool execution

We integrate by:
1. Wrapping the @tool decorator to govern custom tools
2. Using hooks (PreToolUse, PostToolUse) to govern built-in tools

Reference: https://docs.anthropic.com/en/docs/agent-sdk/python

Architectural rules:
- Adapter is DUMB plumbing
- Adapter calls ONE SDK entrypoint: govern_execution()
- SDK orchestrates everything
- No governance logic in adapter
"""

import os
from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Awaitable

import structlog

from cortexhub.adapters.base import ToolAdapter
from cortexhub.pipeline import govern_execution

if TYPE_CHECKING:
    from cortexhub.client import CortexHub

logger = structlog.get_logger(__name__)

# Attribute names for storing originals
_ORIGINAL_TOOL_ATTR = "__cortexhub_original_tool__"
_PATCHED_ATTR = "__cortexhub_patched__"


class ClaudeAgentsAdapter(ToolAdapter):
    """Adapter for Claude Agent SDK.

    Integrates CortexHub governance via two mechanisms:
    
    1. @tool decorator wrapping:
       Custom MCP tools created with @tool are wrapped to run
       governance pipeline before/after execution.
    
    2. Hooks integration:
       PreToolUse and PostToolUse hooks intercept built-in tools
       like Bash, Read, Write, Edit, etc.
    
    For approval workflows:
    - PreToolUse hook can block tool execution
    - Custom tools can raise ApprovalRequiredError
    
    Key properties:
    - Adapter is dumb plumbing
    - Calls SDK entrypoint, doesn't implement governance
    """

    @property
    def framework_name(self) -> str:
        return "claude_agents"

    def _get_framework_modules(self) -> list[str]:
        return ["claude_agent_sdk"]

    def patch(self) -> None:
        """Patch Claude Agent SDK tool creation.
        
        Wraps the @tool decorator to intercept custom tool creation
        and add CortexHub governance.
        """
        try:
            import claude_agent_sdk
            from claude_agent_sdk import tool as original_tool_decorator
            
            # Check if already patched
            if getattr(claude_agent_sdk, _PATCHED_ATTR, False):
                logger.info("Claude Agent SDK already patched")
                return
            
            cortex_hub = self.cortex_hub
            tools = self._discover_tools()
            if tools:
                cortex_hub.backend.register_tool_inventory(
                    agent_id=cortex_hub.agent_id,
                    framework=self.framework_name,
                    tools=tools,
                )
            
            # Store original decorator
            if not hasattr(claude_agent_sdk, _ORIGINAL_TOOL_ATTR):
                setattr(claude_agent_sdk, _ORIGINAL_TOOL_ATTR, original_tool_decorator)
            
            original_tool = getattr(claude_agent_sdk, _ORIGINAL_TOOL_ATTR)
            
            def patched_tool(
                name: str,
                description: str,
                input_schema: type | dict[str, Any],
            ) -> Callable[[Callable[[Any], Awaitable[dict[str, Any]]]], Any]:
                """Wrapped @tool decorator that adds CortexHub governance."""
                
                def decorator(handler: Callable[[Any], Awaitable[dict[str, Any]]]) -> Any:
                    # Create the original tool
                    original_decorated = original_tool(name, description, input_schema)(handler)
                    
                    # Wrap the handler with governance
                    original_handler = original_decorated.handler
                    tool_name = original_decorated.name
                    tool_description = original_decorated.description
                    
                    @wraps(original_handler)
                    async def governed_handler(args: dict[str, Any]) -> dict[str, Any]:
                        """Governed tool execution."""
                        tool_metadata = {
                            "name": tool_name,
                            "description": tool_description,
                            "framework": "claude_agents",
                        }
                        
                        governed_fn = govern_execution(
                            tool_fn=lambda **kw: original_handler(args),
                            tool_metadata=tool_metadata,
                            cortex_hub=cortex_hub,
                        )
                        
                        # Execute with governance (async)
                        result = governed_fn(**args)
                        if hasattr(result, '__await__'):
                            result = await result
                        return result
                    
                    # Replace the handler
                    original_decorated.handler = governed_handler
                    return original_decorated
                
                return decorator
            
            # Apply patch
            claude_agent_sdk.tool = patched_tool
            setattr(claude_agent_sdk, _PATCHED_ATTR, True)
            
            logger.info("Claude Agent SDK @tool decorator patched successfully")
            
        except ImportError:
            logger.debug("Claude Agent SDK not installed, skipping adapter")
        except Exception as e:
            logger.error("Failed to patch Claude Agent SDK", error=str(e))

    def unpatch(self) -> None:
        """Restore original @tool decorator."""
        try:
            import claude_agent_sdk
            
            if hasattr(claude_agent_sdk, _ORIGINAL_TOOL_ATTR):
                original = getattr(claude_agent_sdk, _ORIGINAL_TOOL_ATTR)
                claude_agent_sdk.tool = original
                setattr(claude_agent_sdk, _PATCHED_ATTR, False)
                logger.info("Claude Agent SDK adapter unpatched")
        except ImportError:
            pass

    def intercept(self, tool_fn, tool_name, args, **kwargs):
        """Not used - governance happens via wrapped decorator."""
        raise NotImplementedError("Use govern_execution via wrapped decorator")

    def _discover_tools(self) -> list[dict[str, Any]]:
        """Discover tools from Claude Agent SDK (best-effort)."""
        return []
    
    def create_governance_hooks(self) -> dict[str, list]:
        """Create CortexHub governance hooks for Claude Agent SDK.
        
        These hooks can be passed to ClaudeAgentOptions to govern
        built-in tools like Bash, Read, Write, Edit, etc.
        
        Returns:
            Dict of hook configurations for PreToolUse and PostToolUse
        
        Example:
            adapter = ClaudeAgentsAdapter(cortex_hub)
            hooks = adapter.create_governance_hooks()
            
            options = ClaudeAgentOptions(
                hooks=hooks,
                allowed_tools=["Bash", "Read", "Write"],
            )
        """
        cortex_hub = self.cortex_hub
        
        async def pre_tool_governance(
            input_data: dict[str, Any],
            tool_use_id: str | None,
            context: Any,
        ) -> dict[str, Any]:
            """Pre-tool governance hook.
            
            Evaluates policy BEFORE tool execution.
            Can block the tool by returning decision="block".
            """
            tool_name = input_data.get("tool_name", "unknown")
            tool_input = input_data.get("tool_input", {})
            
            tool_metadata = {
                "name": tool_name,
                "description": f"Claude Agent SDK built-in tool: {tool_name}",
                "framework": "claude_agents",
            }
            
            # Build authorization request and evaluate
            from cortexhub.policy.models import (
                Action,
                Principal,
                Resource as PolicyResource,
            )
            
            request = cortex_hub.build_request(
                principal=Principal(type="Agent", id=cortex_hub.agent_id),
                action=Action(type="tool.invoke", name=tool_name),
                resource=PolicyResource(type="Tool", id=tool_name),
                args=tool_input,
                framework="claude_agents",
            )
            
            # Evaluate policy if in enforcement mode
            if cortex_hub.enforce and cortex_hub.evaluator:
                from cortexhub.policy.effects import Effect
                decision = cortex_hub.evaluator.evaluate(request)
                
                if decision.effect == Effect.DENY:
                    return {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "deny",
                            "permissionDecisionReason": decision.reasoning,
                        }
                    }
                
                if decision.effect == Effect.ESCALATE:
                    try:
                        context_hash = cortex_hub._compute_context_hash(tool_name, tool_input)
                        approval_response = cortex_hub.backend.create_approval(
                            run_id=cortex_hub.session_id,
                            trace_id=cortex_hub._get_current_trace_id(),
                            tool_name=tool_name,
                            tool_args_values=tool_input if not cortex_hub.privacy else None,
                            context_hash=context_hash,
                            policy_id=decision.policy_id or "",
                            policy_name=decision.policy_name or "Unknown Policy",
                            policy_explanation=decision.reasoning,
                            risk_category=None,
                            agent_id=cortex_hub.agent_id,
                            framework="claude_agents",
                            environment=os.getenv("CORTEXHUB_ENVIRONMENT"),
                        )
                        approval_id = approval_response.get("approval_id", "unknown")
                    except Exception as e:
                        logger.error("Failed to create approval", error=str(e))
                        return {
                            "hookSpecificOutput": {
                                "hookEventName": "PreToolUse",
                                "permissionDecision": "deny",
                                "permissionDecisionReason": (
                                    f"Tool '{tool_name}' requires approval but failed to create approval record: {e}"
                                ),
                            }
                        }

                    return {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "ask",
                            "permissionDecisionReason": (
                                f"Approval required: {decision.reasoning}\n\nApproval ID: {approval_id}"
                            ),
                        }
                    }
            
            # Allow execution
            return {}
        
        async def post_tool_governance(
            input_data: dict[str, Any],
            tool_use_id: str | None,
            context: Any,
        ) -> dict[str, Any]:
            """Post-tool governance hook.
            
            Logs tool execution results for audit.
            """
            tool_name = input_data.get("tool_name", "unknown")
            tool_response = input_data.get("tool_response", {})
            
            # Log the tool execution
            logger.debug(
                "Tool executed",
                tool=tool_name,
                framework="claude_agents",
            )
            
            return {}
        
        # Return hook configuration
        # Note: HookMatcher is from claude_agent_sdk
        try:
            from claude_agent_sdk import HookMatcher
            
            return {
                "PreToolUse": [
                    HookMatcher(hooks=[pre_tool_governance])
                ],
                "PostToolUse": [
                    HookMatcher(hooks=[post_tool_governance])
                ],
            }
        except ImportError:
            logger.warning("Could not create hooks - claude_agent_sdk not installed")
            return {}
