"""Main fastapi application."""


from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime
from googletrans import Translator

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class SearchResponse(BaseModel):
    """Search response model."""
    date: datetime
    url: str
    title: str
    original_text: str
    translated_text: str


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """Display the index.html page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/search", response_model=list[SearchResponse])
def search(query: str = Query(..., min_length=1)) -> list[SearchResponse]:
    # Simulate some search results , in reality this will go to a RAG system
    results = [
        {
            "url": "https://example.com/article1",
            "date": datetime(2023, 4, 1).isoformat(),
            "title": "Article 1",
            "original_text": "This is the original text of article 1.",
            "translated_text": "Esto es el texto original del artículo 1."
        },
        {
            "url": "https://example.com/article2",
            "date": datetime(2023, 3, 15).isoformat(),
            "title": "Article 2",
            "original_text": "This is the original text of article 2.",
            "translated_text": "Esto es el texto original del artículo 2."
        }
    ]

    # Translate the results using the Google Translate API
    # translator = Translator()
    # for result in results:
    #     print(result["original_text"])
    #     result["translated_text"] = translator.translate(result["original_text"], dest="es").text

    return results