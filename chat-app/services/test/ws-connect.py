from fastapi import WebSocket, WebSocketDisconnect, Query
from jose import jwt, JWTError, ExpiredSignatureError
import logging
import os

logger = logging.getLogger("uvicorn.error")

SECRET_KEY = os.getenv("SECRET_KEY", "NyDc4fb1c5EXYe5jY6fozs8qcnMb3R8_wK_C7DYaQvA")

async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        # Token valid, accept connection
        await websocket.accept()
        # Proceed with your WS logic here
    except ExpiredSignatureError:
        logger.warning("WebSocket connection rejected: Token expired.")
        await websocket.close(code=4401, reason="Token expired")  # 4401 custom code
    except JWTError as e:
        logger.warning(f"WebSocket connection rejected: Invalid token: {str(e)}")
        await websocket.close(code=4403, reason="Invalid token")
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket auth: {str(e)}")
        await websocket.close(code=1011, reason="Internal error")
