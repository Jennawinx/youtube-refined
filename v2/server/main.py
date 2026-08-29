from fastapi import FastAPI, Request
from pydantic import BaseModel
from api.channels.router import router as channels_router
from api.feed.router import router as videos_router
from api.feed_schedule.router import router as schedule_router

app = FastAPI()
app.include_router(channels_router)
app.include_router(videos_router)
app.include_router(schedule_router)

class ServerInfoResponse(BaseModel):
    openapi_url: str
    server_url: str
    server_docs: str

@app.get("/", response_model=ServerInfoResponse)
def root(request: Request):
    return {
        "openapi_url": app.openapi_url,
        "server_url": request.base_url._url,
        "server_docs": f"{request.base_url._url[:-1]}{app.docs_url}",
    }
