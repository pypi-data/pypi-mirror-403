"""Tool execution helpers for ReactAgent."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from ..core.logging import react_logger as logger
from ..core.event_bus import Events
from ..core.types.block import BlockEvent, BlockKind, BlockOp
from ..core.types import (
    ToolContext,
    ToolResult,
    ToolInvocation,
)
from ..core.signals import SuspendSignal
from ..llm import LLMMessage
from ..middleware import HookAction

if TYPE_CHECKING:
    from .agent import ReactAgent
    from ..core.types.tool import BaseTool


def get_tool(agent: "ReactAgent", tool_name: str) -> "BaseTool | None":
    """Get tool by name from agent context.
    
    Args:
        agent: ReactAgent instance
        tool_name: Name of the tool to find
        
    Returns:
        Tool instance or None if not found
    """
    if agent._agent_context:
        for tool in agent._agent_context.tools:
            if tool.name == tool_name:
                return tool
    return None


async def execute_tool(agent: "ReactAgent", invocation: ToolInvocation) -> ToolResult:
    """Execute a single tool call.
    
    Args:
        agent: ReactAgent instance
        invocation: Tool invocation to execute
        
    Returns:
        ToolResult from tool execution
    """
    # Check abort before execution
    if await agent._check_abort():
        error_msg = f"Tool {invocation.tool_name} aborted before execution"
        invocation.mark_result(error_msg, is_error=True)
        logger.info(
            f"Tool aborted before execution: {invocation.tool_name}",
            extra={
                "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
                "call_id": invocation.tool_call_id,
            },
        )
        return ToolResult.error(error_msg)
    
    invocation.mark_call_complete()

    logger.info(
        f"Executing tool: {invocation.tool_name}",
        extra={
            "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
            "call_id": invocation.tool_call_id,
            "arguments": invocation.args,
        },
    )

    try:
        # Get tool from agent context
        tool = get_tool(agent, invocation.tool_name)
        if tool is None:
            error_msg = f"Unknown tool: {invocation.tool_name}"
            invocation.mark_result(error_msg, is_error=True)
            logger.warning(
                f"Tool not found: {invocation.tool_name}",
                extra={"invocation_id": agent._current_invocation.id if agent._current_invocation else ""},
            )
            return ToolResult.error(error_msg)

        # === Middleware: on_tool_call ===
        if agent.middleware:
            logger.debug(
                f"Calling middleware: on_tool_call ({invocation.tool_name})",
                extra={"invocation_id": agent._current_invocation.id, "call_id": invocation.tool_call_id},
            )
            hook_result = await agent.middleware.process_tool_call(
                tool, invocation.args
            )
            if hook_result.action == HookAction.SKIP:
                logger.warning(
                    f"Tool {invocation.tool_name} skipped by middleware",
                    extra={"invocation_id": agent._current_invocation.id},
                )
                return ToolResult(
                    output=hook_result.message or "Skipped by middleware",
                    is_error=False,
                )
            elif hook_result.action == HookAction.RETRY and hook_result.modified_data:
                logger.debug(
                    f"Tool args modified by middleware",
                    extra={"invocation_id": agent._current_invocation.id},
                )
                invocation.args = hook_result.modified_data

        # Create ToolContext
        # Get block_id for this tool call
        tool_block_id = agent._tool_call_blocks.get(invocation.tool_call_id, "")
        tool_ctx = ToolContext(
            session_id=agent.session.id,
            invocation_id=agent._current_invocation.id if agent._current_invocation else "",
            block_id=tool_block_id,
            call_id=invocation.tool_call_id,
            agent=agent.config.name,
            abort_signal=agent._abort,
            update_metadata=agent._noop_update_metadata,
            middleware=agent.middleware,
        )

        # Execute tool (with optional timeout from tool.config)
        timeout = tool.config.timeout
        if timeout is not None:
            result = await asyncio.wait_for(
                tool.execute(invocation.args, tool_ctx),
                timeout=timeout,
            )
        else:
            # No timeout - tool runs until completion
            result = await tool.execute(invocation.args, tool_ctx)

        # === Middleware: on_tool_end ===
        if agent.middleware:
            logger.debug(
                f"Calling middleware: on_tool_end ({invocation.tool_name})",
                extra={"invocation_id": agent._current_invocation.id},
            )
            hook_result = await agent.middleware.process_tool_end(tool, result)
            if hook_result.action == HookAction.RETRY:
                logger.info(
                    f"Tool {invocation.tool_name} retry requested by middleware",
                    extra={"invocation_id": agent._current_invocation.id},
                )

        invocation.mark_result(result.output, is_error=result.is_error)
        logger.info(
            f"Tool executed: {invocation.tool_name}",
            extra={
                "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
                "call_id": invocation.tool_call_id,
                "is_error": result.is_error,
                "output_length": len(result.output) if result.output else 0,
            },
        )
        return result

    except asyncio.TimeoutError:
        timeout = tool.config.timeout if tool else None
        error_msg = f"Tool {invocation.tool_name} timed out after {timeout}s"
        invocation.mark_result(error_msg, is_error=True)
        logger.error(
            f"Tool timeout: {invocation.tool_name}",
            extra={
                "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
                "timeout": timeout,
            },
        )
        return ToolResult.error(error_msg)

    except SuspendSignal:
        # HITL/Suspend signal must propagate up
        raise
    
    except Exception as e:
        import traceback
        error_type = type(e).__name__
        error_msg = f"Tool execution error ({error_type}): {e}"
        stack_trace = traceback.format_exc()
        invocation.mark_result(error_msg, is_error=True)
        logger.error(
            f"Tool execution failed: {invocation.tool_name} - {error_type}: {e}\n{stack_trace}",
            extra={
                "invocation_id": agent._current_invocation.id if agent._current_invocation else "",
                "error_type": error_type,
                "error": str(e),
            },
        )
        return ToolResult.error(error_msg)


async def process_tool_results(agent: "ReactAgent") -> None:
    """Execute tool calls and add results to history.

    Executes tools in parallel or sequentially based on config.
    
    This function directly modifies agent's internal state:
    - agent._message_history
    
    Args:
        agent: ReactAgent instance
    """
    if not agent._tool_invocations:
        return

    logger.info(
        f"Executing {len(agent._tool_invocations)} tools",
        extra={
            "invocation_id": agent._current_invocation.id,
            "mode": "parallel" if agent.config.parallel_tool_execution else "sequential",
            "tools": [inv.tool_name for inv in agent._tool_invocations],
        },
    )

    # Check abort before starting tool execution
    if await agent._check_abort():
        logger.info(
            "Tool execution aborted before starting",
            extra={"invocation_id": agent._current_invocation.id},
        )
        # Return empty results - agent loop will handle abort
        return
    
    # Execute tools based on configuration
    if agent.config.parallel_tool_execution:
        # Parallel execution using asyncio.gather with create_task
        # create_task ensures each task gets its own ContextVar copy
        tasks = [asyncio.create_task(execute_tool(agent, inv)) for inv in agent._tool_invocations]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check abort after parallel execution - cancel remaining if aborted
        if await agent._check_abort():
            logger.info(
                "Tool execution aborted after parallel execution",
                extra={"invocation_id": agent._current_invocation.id},
            )
    else:
        # Sequential execution with abort check between tools
        results = []
        for inv in agent._tool_invocations:
            # Check abort before each tool
            if await agent._check_abort():
                logger.info(
                    f"Tool execution aborted before {inv.tool_name}",
                    extra={"invocation_id": agent._current_invocation.id},
                )
                # Mark remaining as aborted
                error_result = ToolResult.error(f"Aborted before execution")
                results.append(error_result)
                inv.mark_result(error_result.output, is_error=True)
                continue
                
            try:
                result = await execute_tool(agent, inv)
                results.append(result)
            except Exception as e:
                results.append(e)

    # Check for SuspendSignal - record tool_results first, then propagate
    suspend_signal = None
    for result in results:
        if isinstance(result, SuspendSignal):
            suspend_signal = result
            break
    
    if suspend_signal:
        # Must record tool_results to history BEFORE suspending
        # Otherwise Claude API will reject next request (tool_use without tool_result)
        for invocation, result in zip(agent._tool_invocations, results):
            if isinstance(result, SuspendSignal):
                # HITL tool - record placeholder result
                invocation.mark_result(f"[等待用户输入: {suspend_signal.request_type}]", is_error=False)
            else:
                # Normal tool result - pass truncated_output
                output = result.output if hasattr(result, 'output') else str(result)
                truncated = getattr(result, 'truncated_output', None)
                invocation.mark_result(
                    output,
                    is_error=getattr(result, 'is_error', False),
                    truncated_result=truncated,
                )
            
            # Add to in-memory history (use truncated for context window)
            agent._message_history.append(
                LLMMessage(
                    role="tool",
                    content=invocation.result,
                    tool_call_id=invocation.tool_call_id,
                    name=invocation.tool_name,  # Required for Gemini
                    truncated_content=invocation.truncated_result,
                )
            )
        
        # Persist via _save_tool_messages
        await agent._save_tool_messages()
        
        logger.info(
            "Tool execution suspended (HITL), tool_results recorded",
            extra={"invocation_id": agent._current_invocation.id},
        )
        raise suspend_signal
    
    # Process results
    tool_results = []

    for invocation, result in zip(agent._tool_invocations, results):
        # Handle exceptions from gather
        if isinstance(result, Exception):
            error_msg = f"Tool execution error: {str(result)}"
            invocation.mark_result(error_msg, is_error=True)
            result = ToolResult.error(error_msg)
        else:
            # Mark result with truncated_output
            invocation.mark_result(
                result.output,
                is_error=result.is_error,
                truncated_result=result.truncated_output,
            )

        # Get parent block_id from tool_call mapping
        parent_block_id = agent._tool_call_blocks.get(invocation.tool_call_id)
        
        await agent.ctx.emit(BlockEvent(
            kind=BlockKind.TOOL_RESULT,
            op=BlockOp.APPLY,
            parent_id=parent_block_id,
            data={
                "call_id": invocation.tool_call_id,
                "content": result.output,
                "is_error": invocation.is_error,
            },
        ))

        await agent.bus.publish(
            Events.TOOL_END,
            {
                "call_id": invocation.tool_call_id,
                "tool": invocation.tool_name,
                "result": result.output[:500],  # Truncate for event
                "is_error": invocation.is_error,
                "duration_ms": invocation.duration_ms,
            },
        )

        tool_results.append(
            {
                "type": "tool_result",
                "tool_use_id": invocation.tool_call_id,
                "tool_name": invocation.tool_name,
                "content": result.output,
                "truncated_content": result.truncated_output,
                "is_error": invocation.is_error,
            }
        )

    # Add tool results as tool messages (OpenAI format)
    for tr in tool_results:
        print(f"[DEBUG _process_tool_results] Adding tool_result to history: {tr}")
        agent._message_history.append(
            LLMMessage(
                role="tool",
                content=tr["content"],
                tool_call_id=tr["tool_use_id"],
                name=tr["tool_name"],  # Required for Gemini
                truncated_content=tr.get("truncated_content"),
            )
        )
