from fastapi import FastAPI

from papyrus_agent.routers.workflows import router as workflows_router
from papyrus_agent.routers.health import router as health_router
from papyrus_agent.routers.llm import router as llm_router

app = FastAPI(
    title="Papyrus Agent API",
    description="Agentic document processing runtime",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(llm_router)
app.include_router(workflows_router)

