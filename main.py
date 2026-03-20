from fastapi import FastAPI

app = FastAPI(
    title="FastAPI",
    description="FastAPI",
    version="0.0.1"
)

@app.get("/")
async def read_root():
    return {"Hello": "gais"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}