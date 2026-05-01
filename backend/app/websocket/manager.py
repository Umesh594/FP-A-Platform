from fastapi import APIRouter, WebSocket
from typing import List

router = APIRouter()

connections: List[WebSocket] = []


@router.websocket("/ws/agents")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()

    connections.append(websocket)

    try:

        while True:
            await websocket.receive_text()

    except Exception as e:

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