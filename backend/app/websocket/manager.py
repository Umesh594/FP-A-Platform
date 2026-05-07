from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List

router = APIRouter()

connections: List[WebSocket] = []


@router.websocket("/ws/agents")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()
    await websocket.send_json({"type": "connected", "agent": "Agent WebSocket", "explanation": "Realtime agent channel connected"})

    connections.append(websocket)

    try:

        while True:
            message = await websocket.receive_text()
            if message:
                await websocket.send_json({"type": "heartbeat", "status": "ok"})

    except WebSocketDisconnect:

        if websocket in connections:
            connections.remove(websocket)

    except Exception:

        if websocket in connections:
            connections.remove(websocket)


async def broadcast(message: dict):

    disconnected = []

    for connection in connections:

        try:

            await connection.send_json(message)

        except Exception as e:

            disconnected.append(connection)

    for conn in disconnected:

        if conn in connections:
            connections.remove(conn)
