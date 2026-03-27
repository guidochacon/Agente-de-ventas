"""
WebSocket chat endpoint.
Each session maintains its own conversation history in memory.
"""
import json
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_db
from models.conversation import Conversation, Message
from sqlalchemy import select
from agent.core import stream_response

router = APIRouter()

# In-memory session store: session_id -> list of messages
_sessions: dict[str, list[dict]] = {}


async def get_or_create_conversation(session_id: str, db: AsyncSession) -> Conversation:
    result = await db.execute(select(Conversation).where(Conversation.session_id == session_id))
    conv = result.scalar_one_or_none()
    if not conv:
        conv = Conversation(session_id=session_id)
        db.add(conv)
        await db.commit()
        await db.refresh(conv)
    return conv


@router.websocket("/api/chat/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    await websocket.accept()

    if session_id not in _sessions:
        _sessions[session_id] = []

    conv = await get_or_create_conversation(session_id, db)

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

            # Save user message to DB
            user_msg = Message(
                conversation_id=conv.id,
                role="user",
                content=user_message,
            )
            db.add(user_msg)
            await db.commit()

            history = _sessions[session_id]
            assistant_text_parts = []

            # Signal start of response
            await websocket.send_text(json.dumps({"type": "start"}))

            async for token in stream_response(user_message, history, session_id, db):
                if token.startswith("__TOOL_CALL__:"):
                    tool_name = token.replace("__TOOL_CALL__:", "").strip()
                    await websocket.send_text(json.dumps({"type": "tool_call", "tool": tool_name}))
                elif token.startswith("__TOOL_RESULT__:"):
                    pass  # Internal — not sent to client
                else:
                    assistant_text_parts.append(token)
                    await websocket.send_text(json.dumps({"type": "token", "text": token}))

            full_response = "".join(assistant_text_parts)

            # Update history
            _sessions[session_id].append({"role": "user", "content": user_message})
            _sessions[session_id].append({"role": "assistant", "content": full_response})

            # Keep history bounded (last 20 turns = 40 messages)
            if len(_sessions[session_id]) > 40:
                _sessions[session_id] = _sessions[session_id][-40:]

            # Save assistant message to DB
            asst_msg = Message(
                conversation_id=conv.id,
                role="assistant",
                content=full_response,
            )
            db.add(asst_msg)
            conv.message_count = (conv.message_count or 0) + 1
            await db.commit()

            # Signal end of response
            await websocket.send_text(json.dumps({"type": "end"}))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_text(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass
