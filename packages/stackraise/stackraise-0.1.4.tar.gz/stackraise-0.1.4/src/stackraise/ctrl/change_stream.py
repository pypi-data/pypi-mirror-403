from fastapi import APIRouter, WebSocket, WebSocketDisconnect

import stackraise.db as db
import json

class ChangeStream:

    websockets: set[WebSocket]

    def __init__(self):
        self.websockets = set()
        #print("Initializing ChangeStream...")
        self.api_router = APIRouter(
            prefix=f"", 
            tags=['websockets'],
        )

        @self.api_router.websocket("/change-stream")
        async def endpoint(ws: WebSocket):
            await ws.accept()
            try:
                self.websockets.add(ws)
                while True:
                    await ws.receive_json()
                    # TODO: handle subscription events ... etc
            except WebSocketDisconnect:
                self.websockets.remove(ws)

        db.change_event_emitter.subscribe(self.broadcast)
        

    async def broadcast(self, change_event: db.ChangeEvent):
        payload = json.dumps(change_event)
        print(f"Broadcasting change event: {payload}")
        for ws in tuple(self.websockets):
            try: 
                await ws.send_text(payload)
            except Exception as e: 
                print(e)
                pass
