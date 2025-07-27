from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict,Any
from datetime import datetime,timezone
import json

from app.database import get_db
from app.models import User, Message, Friendship
from app.utils.auth import Token as token_manager



router = APIRouter(prefix="/chat", tags=["Chat"])

# Store connected clients: user_id -> websocket
active_connections: Dict[int, WebSocket] = {}

# Helper to get current user from JWT token
async def get_current_user_from_token(token: str, db: AsyncSession) -> User:
    try:
        payload = token_manager.decode_token(token)
        user_id = int(payload.get("sub"))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


# Helper to check if two users are friends (accepted)
async def are_friends(user1_id: int, user2_id: int, db: AsyncSession) -> bool:
    stmt = select(Friendship).where(
        ((Friendship.sender_id == user1_id) & (Friendship.receiver_id == user2_id)) |
        ((Friendship.sender_id == user2_id) & (Friendship.receiver_id == user1_id)),
        Friendship.status == "accepted"
    )
    result = await db.execute(stmt)
    friendship = result.scalar_one_or_none()
    return friendship is not None



@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...), db: AsyncSession = Depends(get_db)):
    """
    WebSocket connection endpoint for chat.
    Client must send JWT token as query param ?token=...
    """
    await websocket.accept()
    try:
        current_user = await get_current_user_from_token(token, db)
    except HTTPException as e:
        await websocket.close(code=1008)  # Policy Violation
        return

    user_id = current_user.id
    active_connections[user_id] = websocket

    try:
        while True:
            data_str = await websocket.receive_text()
            data: dict [str, Any]= json.loads(data_str)

            msg_type = data.get("type")

            if msg_type == "message":
                # New chat message
                to_user_id = data.get("to")
                content = data.get("content")
                if not to_user_id or not content:
                    await websocket.send_text(json.dumps({"error": "Missing 'to' or 'content'"}))
                    continue

                # Validate friendship
                if not await are_friends(user_id, to_user_id, db):
                    await websocket.send_text(json.dumps({"error": "You are not friends with this user"}))
                    continue

                # Save message in DB
                message = Message(
                    sender_id=user_id,
                    receiver_id=to_user_id,
                    content=content,
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(message)
                await db.commit()
                await db.refresh(message)

                # Send message back to sender as confirmation
                await websocket.send_text(json.dumps({
                    "type": "message",
                    "from": user_id,
                    "to": to_user_id,
                    "content": content,
                    "timestamp": message.timestamp.isoformat()
                }))

                # Forward message to recipient if connected
                recipient_ws = active_connections.get(to_user_id)
                if recipient_ws:
                    await recipient_ws.send_text(json.dumps({
                        "type": "message",
                        "from": user_id,
                        "content": content,
                        "timestamp": message.timestamp.isoformat()
                    }))

            elif msg_type == "history":
                # Load recent messages between current user and specified friend
                friend_id = data.get("friend_id")
                if not friend_id:
                    await websocket.send_text(json.dumps({"error": "Missing 'friend_id' for history"}))
                    continue

                if not await are_friends(user_id, friend_id, db):
                    await websocket.send_text(json.dumps({"error": "You are not friends with this user"}))
                    continue

                # Query last 50 messages between user and friend ordered by timestamp asc
                stmt = select(Message).where(
                    ((Message.sender_id == user_id) & (Message.receiver_id == friend_id)) |
                    ((Message.sender_id == friend_id) & (Message.receiver_id == user_id))
                ).order_by(Message.timestamp.asc()).limit(50)

                result = await db.execute(stmt)
                messages = result.scalars().all()

                # Send history message to client
                history = [
                    {
                        "from": m.sender_id,
                        "to": m.receiver_id,
                        "content": m.content,
                        "timestamp": m.timestamp.isoformat() if m.timestamp else None
                    }
                    for m in messages
                ]
                await websocket.send_text(json.dumps({"type": "history", "messages": history}))

            else:
                await websocket.send_text(json.dumps({"error": f"Unknown message type '{msg_type}'"}))

    except WebSocketDisconnect:
        del active_connections[user_id]
    except Exception as e:
        # Log if you want, here just close connection
        del active_connections[user_id]
        await websocket.close(code=1011)
