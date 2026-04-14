from fastapi import FastAPI
from app.controller.agent_controller import router


app = FastAPI(title="Report Genius", version="0.1.0")
app.include_router(router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
