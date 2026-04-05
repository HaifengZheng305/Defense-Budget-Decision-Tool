from fastapi import FastAPI

app = FastAPI(title="Defense Budget Decision Tool")

@app.get("/health")
def health():
    return {"status": "ok"}
