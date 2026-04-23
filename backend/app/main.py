from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import user, points, task, shop, admin
import app.models

app = FastAPI(title="水印去除工具 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()

app.include_router(user.router, prefix="/api/v1")
app.include_router(points.router, prefix="/api/v1")
app.include_router(task.router, prefix="/api/v1")
app.include_router(shop.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "水印去除工具 API v1.0", "docs": "/docs"}
