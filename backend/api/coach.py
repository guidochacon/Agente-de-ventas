"""
WebSocket endpoint for coaching modes: analyze, practice, consult.
Usage: ws://host/api/coach/{session_id}?mode=analyze|practice|consult
"""
import json
import traceback
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from agent.core import stream_response

logger = logging.getLogger(__name__)
router = APIRouter()

_sessions: dict[str, list[dict]] = {}

VALID_MODES = {"analyze", "practice", "consult"}


@router.websocket("/api/coach/{session_id}")
async def websocket_coach(
    websocket: WebSocket,
    session_id: str,
    mode: str = Query(default="consult"),
):
    if mode not in VALID_MODES:
        mode = "consult"

    await websocket.accept()
    logger.info(f"Coach WS connected: session={session_id} mode={mode}")

    session_key = f"{session_id}:{mode}"
    if session_key not in _sessions:
        _sessions[session_key] = []

    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                user_message = payload.get("message", "").strip()
            except Exception:
                user_message = data.strip()

            if not user_message:
                continue

            logger.info(f"Message received [{mode}]: {user_message[:80]}")
            history = _sessions[session_key]
            assistant_parts = []

            await websocket.send_text(json.dumps({"type": "start"}))

            try:
                async for token in stream_response(
                    user_message=user_message,
                    history=history,
                    session_id=session_key,
                    mode=mode,
                ):
                    if token.startswith("__TOOL_CALL__:"):
                        tool_name = token.replace("__TOOL_CALL__:", "").strip()
                        await websocket.send_text(json.dumps({"type": "tool_call", "tool": tool_name}))
                    elif token.startswith("__TOOL_RESULT__:"):
                        pass
                    else:
                        assistant_parts.append(token)
                        await websocket.send_text(json.dumps({"type": "token", "text": token}))
            except Exception as e:
                logger.error(f"stream_response error: {e}\n{traceback.format_exc()}")
                await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
                await websocket.send_text(json.dumps({"type": "end"}))
                continue

            full_response = "".join(assistant_parts)
            logger.info(f"Response complete: {len(full_response)} chars")

            _sessions[session_key].append({"role": "user", "content": user_message})
            _sessions[session_key].append({"role": "assistant", "content": full_response})

            if len(_sessions[session_key]) > 40:
                _sessions[session_key] = _sessions[session_key][-40:]

            await websocket.send_text(json.dumps({"type": "end"}))

    except WebSocketDisconnect:
        logger.info(f"Coach WS disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Coach WS fatal error: {e}\n{traceback.format_exc()}")
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
