"""CrewAI adapter for tool and LLM interception.

Patches CrewAI at multiple levels:
- CrewStructuredTool.invoke for all LLM-driven tool calls
- BaseTool._run for direct tool usage
- LiteLLM completion for LLM call governance (guardrails, PII detection)

IMPORTANT: CrewAI has its own OpenTelemetry setup that may conflict with
CortexHub's telemetry. To ensure proper telemetry capture, either:
1. Call cortexhub.init() BEFORE importing crewai
2. Set environment variable: CREWAI_TRACING_ENABLED=false

Architectural rules:
- Adapter is DUMB plumbing
- SDK orchestrates everything via govern_execution()
- Store original on class, not global
"""

from typing import Any

import structlog

from cortexhub.adapters.base import ToolAdapter
from cortexhub.pipeline import govern_execution

logger = structlog.get_logger(__name__)

# Attribute names for storing originals on class
_ORIGINAL_INVOKE_ATTR = "__cortexhub_original_invoke__"
_ORIGINAL_RUN_ATTR = "__cortexhub_original_run__"
_PATCHED_ATTR = "__cortexhub_patched__"
_PATCHED_TOOL_ATTR = "__cortexhub_tool_patched__"
_PATCHED_LLM_ATTR = "__cortexhub_llm_patched__"
_ORIGINAL_COMPLETION_ATTR = "__cortexhub_original_completion__"
_ORIGINAL_ACOMPLETION_ATTR = "__cortexhub_original_acompletion__"


class CrewAIAdapter(ToolAdapter):
    """Adapter for CrewAI framework.

    Patches CrewStructuredTool.invoke - the method called by CrewAI's
    agent executor when tools are invoked by the LLM.
    
    Key properties:
    - Adapter is dumb plumbing
    - Patches at class level so all tools are governed
    - Works regardless of when tools are created
    """

    @property
    def framework_name(self) -> str:
        return "crewai"

    def _get_framework_modules(self) -> list[str]:
        return ["crewai", "crewai.tools"]

    def patch(self) -> None:
        """Patch CrewAI tool execution methods."""
        try:
            from crewai.tools.structured_tool import CrewStructuredTool
            
            cortex_hub = self.cortex_hub
            tools = self._discover_tools()
            if tools:
                cortex_hub.backend.register_tool_inventory(
                    agent_id=cortex_hub.agent_id,
                    framework=self.framework_name,
                    tools=tools,
                )

            # Patch CrewStructuredTool.invoke (primary execution path)
            if not getattr(CrewStructuredTool, _PATCHED_ATTR, False):
                if not hasattr(CrewStructuredTool, _ORIGINAL_INVOKE_ATTR):
                    setattr(CrewStructuredTool, _ORIGINAL_INVOKE_ATTR, CrewStructuredTool.invoke)
                
                original_invoke = getattr(CrewStructuredTool, _ORIGINAL_INVOKE_ATTR)

                def patched_invoke(self, input, config=None, **kwargs):
                    """Governed CrewStructuredTool execution."""
                    tool_name = getattr(self, 'name', 'unknown_tool')
                    tool_description = getattr(self, 'description', None)
                    
                    tool_metadata = {
                        "name": tool_name,
                        "description": tool_description,
                        "framework": "crewai",
                    }

                    governed_fn = govern_execution(
                        tool_fn=lambda **_kw: original_invoke(self, input, config, **kwargs),
                        tool_metadata=tool_metadata,
                        cortex_hub=cortex_hub,
                    )

                    # Extract args from input
                    if isinstance(input, dict):
                        return governed_fn(**input)
                    elif isinstance(input, str):
                        return governed_fn(_raw=input)
                    return governed_fn()

                CrewStructuredTool.invoke = patched_invoke
                setattr(CrewStructuredTool, _PATCHED_ATTR, True)
                logger.info("CrewAI CrewStructuredTool.invoke patched")

            # Also patch BaseTool._run for direct tool.run() calls
            try:
                from crewai.tools.base_tool import BaseTool
                
                if not getattr(BaseTool, _PATCHED_TOOL_ATTR, False):
                    if not hasattr(BaseTool, _ORIGINAL_RUN_ATTR):
                        setattr(BaseTool, _ORIGINAL_RUN_ATTR, BaseTool._run)
                    
                    original_run = getattr(BaseTool, _ORIGINAL_RUN_ATTR)

                    def patched_run(self, *args, **kwargs):
                        """Governed BaseTool execution."""
                        tool_name = getattr(self, 'name', 'unknown_tool')
                        tool_description = getattr(self, 'description', None)
                        
                        tool_metadata = {
                            "name": tool_name,
                            "description": tool_description,
                            "framework": "crewai",
                        }

                        governed_fn = govern_execution(
                            tool_fn=lambda **_kw: original_run(self, *args, **kwargs),
                            tool_metadata=tool_metadata,
                            cortex_hub=cortex_hub,
                        )

                        # Extract args
                        if kwargs:
                            return governed_fn(**kwargs)
                        if len(args) == 1 and isinstance(args[0], dict):
                            return governed_fn(**args[0])
                        if args:
                            return governed_fn(_raw=args[0])
                        return governed_fn()

                    BaseTool._run = patched_run
                    setattr(BaseTool, _PATCHED_TOOL_ATTR, True)
                    logger.info("CrewAI BaseTool._run patched")
                    
            except ImportError:
                logger.debug("CrewAI BaseTool not available")

            logger.info("CrewAI adapter patched successfully")
            
            # Patch LiteLLM for LLM call governance (guardrails, PII)
            self._patch_litellm(cortex_hub)

        except ImportError:
            logger.debug("CrewAI not available, skipping adapter")
            raise
        except Exception as e:
            logger.error("Failed to patch CrewAI", error=str(e))
            raise

    def _patch_litellm(self, cortex_hub) -> None:
        """Patch LiteLLM completion for LLM call governance.
        
        CrewAI uses LiteLLM internally for all LLM calls.
        We patch litellm.completion to intercept and run guardrails.
        """
        try:
            import litellm
            
            if getattr(litellm, _PATCHED_LLM_ATTR, False):
                logger.debug("LiteLLM already patched for CrewAI")
                return
            
            # Store originals
            if not hasattr(litellm, _ORIGINAL_COMPLETION_ATTR):
                setattr(litellm, _ORIGINAL_COMPLETION_ATTR, litellm.completion)
            original_completion = getattr(litellm, _ORIGINAL_COMPLETION_ATTR)
            
            def patched_completion(*args, **kwargs):
                """Governed LiteLLM completion."""
                model = kwargs.get("model") or (args[0] if args else "unknown")
                messages = kwargs.get("messages") or (args[1] if len(args) > 1 else [])
                
                # Extract prompt from messages
                prompt = messages
                
                def call_original(prompt_override):
                    # Replace messages if overridden (for redaction)
                    call_kwargs = kwargs.copy()
                    if prompt_override is not None:
                        call_kwargs["messages"] = prompt_override
                    return original_completion(*args[:1] if args else [], **call_kwargs)
                
                llm_metadata = {
                    "kind": "llm",
                    "framework": "crewai",
                    "model": model,
                    "prompt": prompt,
                    "call_original": call_original,
                }
                
                governed = govern_execution(
                    tool_fn=lambda *a, **kw: original_completion(*args, **kwargs),
                    tool_metadata=llm_metadata,
                    cortex_hub=cortex_hub,
                )
                return governed()
            
            litellm.completion = patched_completion
            
            # Patch async version too
            if hasattr(litellm, "acompletion"):
                if not hasattr(litellm, _ORIGINAL_ACOMPLETION_ATTR):
                    setattr(litellm, _ORIGINAL_ACOMPLETION_ATTR, litellm.acompletion)
                original_acompletion = getattr(litellm, _ORIGINAL_ACOMPLETION_ATTR)
                
                async def patched_acompletion(*args, **kwargs):
                    """Governed async LiteLLM completion."""
                    model = kwargs.get("model") or (args[0] if args else "unknown")
                    messages = kwargs.get("messages") or (args[1] if len(args) > 1 else [])
                    prompt = messages
                    
                    async def call_original(prompt_override):
                        call_kwargs = kwargs.copy()
                        if prompt_override is not None:
                            call_kwargs["messages"] = prompt_override
                        return await original_acompletion(*args[:1] if args else [], **call_kwargs)
                    
                    llm_metadata = {
                        "kind": "llm",
                        "framework": "crewai",
                        "model": model,
                        "prompt": prompt,
                        "call_original": call_original,
                    }
                    
                    governed = govern_execution(
                        tool_fn=lambda *a, **kw: original_acompletion(*args, **kwargs),
                        tool_metadata=llm_metadata,
                        cortex_hub=cortex_hub,
                    )
                    return await governed()
                
                litellm.acompletion = patched_acompletion
            
            setattr(litellm, _PATCHED_LLM_ATTR, True)
            logger.info("CrewAI LiteLLM interception patched successfully")
            
        except ImportError:
            logger.debug("LiteLLM not available, skipping LLM interception for CrewAI")
        except Exception as e:
            logger.debug("CrewAI LiteLLM interception skipped", reason=str(e))

    def unpatch(self) -> None:
        """Restore original CrewAI methods."""
        try:
            from crewai.tools.structured_tool import CrewStructuredTool
            
            if hasattr(CrewStructuredTool, _ORIGINAL_INVOKE_ATTR):
                original = getattr(CrewStructuredTool, _ORIGINAL_INVOKE_ATTR)
                CrewStructuredTool.invoke = original
                setattr(CrewStructuredTool, _PATCHED_ATTR, False)
            
            logger.info("CrewAI CrewStructuredTool unpatched")
            
            try:
                from crewai.tools.base_tool import BaseTool
                if hasattr(BaseTool, _ORIGINAL_RUN_ATTR):
                    original = getattr(BaseTool, _ORIGINAL_RUN_ATTR)
                    BaseTool._run = original
                    setattr(BaseTool, _PATCHED_TOOL_ATTR, False)
                logger.info("CrewAI BaseTool unpatched")
            except ImportError:
                pass
            
            # Restore LiteLLM
            try:
                import litellm
                if hasattr(litellm, _ORIGINAL_COMPLETION_ATTR):
                    litellm.completion = getattr(litellm, _ORIGINAL_COMPLETION_ATTR)
                if hasattr(litellm, _ORIGINAL_ACOMPLETION_ATTR):
                    litellm.acompletion = getattr(litellm, _ORIGINAL_ACOMPLETION_ATTR)
                setattr(litellm, _PATCHED_LLM_ATTR, False)
                logger.info("CrewAI LiteLLM unpatched")
            except ImportError:
                pass
                
        except ImportError:
            pass

    def intercept(self, tool_fn, tool_name, args, **kwargs):
        """Not used - governance happens via SDK entrypoint."""
        raise NotImplementedError("Use govern_execution via pipeline")

    def _discover_tools(self) -> list[dict[str, Any]]:
        """Discover tools from CrewAI (best-effort)."""
        return []
