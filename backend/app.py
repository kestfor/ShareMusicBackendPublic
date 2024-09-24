import uvicorn
from fastapi import FastAPI, Response, WebSocket

import backend.routers.music_endpoints.endpoints as music_endpoints
import backend.routers.login_endpoints.endpoints as login_endpoints
import backend.routers.socket_io as socket_io
import backend.routers.social_endpoints.endpoints as social_endpoints

app = FastAPI()  # docs_url=None, redoc_url=None
app.include_router(music_endpoints.router, prefix="/api/music_api")
app.include_router(social_endpoints.router, prefix='/api/social')
app.include_router(login_endpoints.router)
app.mount("/", socket_io.socket_app)  # Here we mount socket app to main fastapi app


@app.get("/")
def read_root():
    return Response(content="кто прочитал тот здохнет..", media_type='charset=utf-8')


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")

if __name__ == '__main__':
    print("http://127.0.0.1/")
    print("http://127.0.0.1/login/")
    print("http://127.0.0.1:8000/docs")
    uvicorn.run(app, host='0.0.0.0', port=8000)
