from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import create_views
from app.api.routes.countries import router as countries_router

app = FastAPI(title="Defense Budget Decision Tool")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Ensure SQL views exist
    create_views()
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(countries_router)
