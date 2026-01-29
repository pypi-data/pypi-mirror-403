import os
import uuid

from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pypdf import PdfReader

from . import database
from .models import MemoryCreate, SearchResult  # noqa: F401

app = FastAPI(title="Eternity MCP")

# Mount static files
app.mount(
    "/static",
    StaticFiles(
        directory=os.path.join(os.path.dirname(__file__), "static")
    ),
    name="static",
)

# Templates
templates = Jinja2Templates(
    directory=os.path.join(os.path.dirname(__file__), "templates")
)


# Initialize DB on startup
@app.on_event("startup")
def startup():
    database.init_db()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the home page with a list of recent memories."""
    memories = database.get_all_memories()
    return templates.TemplateResponse(
        "index.html", {"request": request, "memories": memories}
    )


@app.post("/add")
async def add_memory(
    request: Request,
    content: str = Form(""),
    tags: str = Form(""),
    file: UploadFile = File(None),  # noqa: B008
):
    """Add a new memory via form submission (text or file)."""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    file_path = None
    file_type = None
    extracted_text = ""

    if file:
        file_type = file.content_type
        # Create uploads directory if not exists
        os.makedirs("uploads", exist_ok=True)
        file_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join("uploads", file_name)

        with open(file_path, "wb") as f:
            content_bytes = await file.read()
            f.write(content_bytes)

        if "pdf" in file_type:
            try:
                reader = PdfReader(file_path)
                for page in reader.pages:
                    extracted_text += page.extract_text() + "\n"
            except Exception as e:
                print("Error reading PDF: {}".format(e))  # noqa: UP032
        elif "text" in file_type:
            with open(file_path, "r", errors="ignore") as f:  # noqa: UP015
                extracted_text = f.read()

        if not content and extracted_text:
            # content = extracted_text[:1000] # tetse previews

            content = extracted_text  # full text in content.

    if not content and not file:
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "memories": database.get_all_memories(),
                "error": "Please provide text or a file.",
            },
        )

    database.add_memory(content, tag_list, file_path, file_type)

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "memories": database.get_all_memories()},
    )


@app.get("/search", response_model=list[SearchResult])
async def search_memory(q: str):
    """Search memories API endpoint."""
    results = database.search_memories(q)
    return results


# HTML Search page (optional, or integrated into home)
@app.get("/search_ui", response_class=HTMLResponse)
async def search_ui(request: Request, q: str = ""):
    results = []
    if q:
        results = database.search_memories(q)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "memories": [],
            "search_results": results,
            "query": q,
        },
    )


def start():
    """Entry point for the application script"""
    import uvicorn

    uvicorn.run("eternity.main:app", host="0.0.0.0", port=8000, reload=True)  # noqa: S104
