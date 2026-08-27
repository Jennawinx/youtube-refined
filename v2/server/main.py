from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, Path, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db import get_db
from models import FeedChannel

app = FastAPI()


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


@app.get("/youtube/channels")
def get_channels(
    db: Session = Depends(get_db),
    page_size: Optional[int] = 30,
    page: Optional[int] = 0,
):
    return {"channels": db.query(FeedChannel).limit(page_size).offset(page * page_size).all()}
