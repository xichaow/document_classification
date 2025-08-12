"""
Main FastAPI application entry point.

This module serves as the entry point for the document classification system,
initializing the FastAPI application and routing.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from src.api.routes import router as api_router
from src.utils.config import settings
from src.utils.logging_config import setup_logging

# Initialize logging
setup_logging()

app = FastAPI(
    title="Document Classification System",
    description="Automatically classify home loan application documents using AWS Textract and Bedrock",
    version="1.0.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

# Templates
templates = Jinja2Templates(directory="src/web/templates")

# Include API routes
app.include_router(api_router, prefix="/api")

@app.get("/", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Upload page - main interface."""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/status", response_class=HTMLResponse)
async def status_page(request: Request):
    """Task status page."""
    return templates.TemplateResponse("status.html", {"request": request})

@app.get("/evaluation", response_class=HTMLResponse)
async def evaluation_page(request: Request):
    """Evaluation page for batch testing and metrics."""
    return templates.TemplateResponse("evaluation.html", {"request": request})

@app.get("/evaluation-standalone", response_class=HTMLResponse)
async def evaluation_standalone():
    """Standalone evaluation page - completely independent."""
    with open("evaluation_standalone.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/evaluation-debug", response_class=HTMLResponse)
async def evaluation_debug():
    """Debug evaluation page for testing."""
    with open("evaluation_debug.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "document-classification"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)