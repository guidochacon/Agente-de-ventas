"""
AgentCore: orchestrates the conversation loop with Claude API.
Handles tool use, streaming, and conversation history.
"""
import anthropic
import httpx
from typing import AsyncIterator
from config import settings
from agent.prompts import build_system_prompt, build_coach_prompt
from agent.tools import TOOLS, execute_tool
from rag.retriever import retrieve

_client = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        import certifi
        http_client = httpx.AsyncClient(
            trust_env=False,
            verify=certifi.where(),
            timeout=httpx.Timeout(60.0, connect=15.0),
        )
        _client = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key,
            http_client=http_client,
        )
    return _client


async def stream_response(
    user_message: str,
    history: list[dict],
    session_id: str,
    db=None,
    mode: str | None = None,
) -> AsyncIterator[str]:
    """
    Process a user message and stream the agent's response.
    Yields text tokens as they arrive, or event markers for tool calls.

    Special yielded values:
    - Regular strings: text tokens
    - "__TOOL_CALL__:{name}": tool execution start marker
    - "__TOOL_RESULT__:{result}": tool result marker
    """
    client = get_client()

    # Retrieve relevant context from knowledge base
    kb_context = retrieve(user_message, n_results=5)

    if mode:
        system_prompt = build_coach_prompt(mode=mode, knowledge_context=kb_context)
    else:
        system_prompt = build_system_prompt(
            agent_name=settings.agent_name,
            business_name=settings.agent_business_name,
            collect_lead_after_messages=settings.collect_lead_after_messages,
            knowledge_context=kb_context,
        )

    # Build messages list (history + new user message)
    messages = list(history) + [{"role": "user", "content": user_message}]

    # Agentic loop — handles multi-step tool use
    while True:
        full_response_text = ""
        tool_uses = []
        stop_reason = None

        async with client.messages.stream(
            model=settings.claude_model,
            max_tokens=2048,
            system=system_prompt,
            tools=TOOLS,
            messages=messages,
        ) as stream:
            async for event in stream:
                if hasattr(event, "type"):
                    if event.type == "content_block_delta":
                        delta = event.delta
                        if hasattr(delta, "type"):
                            if delta.type == "text_delta":
                                full_response_text += delta.text
                                yield delta.text
                            elif delta.type == "input_json_delta":
                                # Accumulate tool input — handled at block_stop
                                pass

            # Get the final message to inspect tool use
            final_message = await stream.get_final_message()
            stop_reason = final_message.stop_reason

            # Collect tool use blocks
            for block in final_message.content:
                if block.type == "tool_use":
                    tool_uses.append(block)

        if stop_reason == "tool_use" and tool_uses:
            # Add assistant turn with all content blocks
            messages.append({"role": "assistant", "content": final_message.content})

            # Execute each tool and build tool_result blocks
            tool_results = []
            for tool_block in tool_uses:
                yield f"\n__TOOL_CALL__:{tool_block.name}\n"
                result = await execute_tool(
                    tool_name=tool_block.name,
                    tool_input=tool_block.input,
                    session_id=session_id,
                    db=db,
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": str(result),
                    }
                )

            # Add tool results as user turn
            messages.append({"role": "user", "content": tool_results})
            # Continue the loop — Claude will now process tool results

        else:
            # end_turn or no more tool calls
            break


async def get_response(
    user_message: str,
    history: list[dict],
    session_id: str,
    db=None,
) -> str:
    """Non-streaming version — returns complete response text."""
    parts = []
    async for token in stream_response(user_message, history, session_id, db):
        if not token.startswith("__"):
            parts.append(token)
    return "".join(parts)
