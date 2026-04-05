from fastapi import FastAPI

app = FastAPI(title="Defense Budget Decision Tool")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)