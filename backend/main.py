from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.db import Base, engine
from backend.routes.bom import router as bom_router
from backend.routes.components import router as components_router
from backend.routes.dashboard import router as dashboard_router
from backend.routes.projects import router as projects_router
from backend.routes.inventory import router as inventory_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Inventory Management API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5500", "http://127.0.0.1:5500"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(components_router)
app.include_router(projects_router)
app.include_router(bom_router)
app.include_router(dashboard_router)
app.include_router(inventory_router)


@app.exception_handler(FileNotFoundError)
async def database_not_found(_: Request, error: FileNotFoundError):
    return JSONResponse(status_code=503, content={"detail": str(error)})


@app.get("/")
def root():
    return {"message": "Inventory Management API is running", "docs": "/docs"}


@app.get("/healthz")
def healthz():
    return {"status": "ok", "database_url": str(engine.url)}