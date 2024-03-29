"""Main fastapi application."""


from datetime import datetime

from fastapi import FastAPI
from fastapi import Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from langdetect import detect   # https://www.geeksforgeeks.org/detect-an-unknown-language-using-python/

from app.translation import translate


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class SearchResponse(BaseModel):
    """Search response model."""
    date: str
    url: str
    title: str
    original_text: str
    dst_text: str


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """Display the index.html page"""
    return templates.TemplateResponse("index.html", {"request": request})


def search_in_vectorsearchDB(text: str, count_answers: int = -1) -> list[SearchResponse]:
    """Search in the vector search database using langchain and chromaDB.
    
    Arguments:
    text -- the text to search for
    count_answers -- the number of answers to return. -1 means all

    Returns:
    list[SearchResponse] -- the search results
    """

    # Simulate some search results , in reality this will go to a RAG system
    results = [
        {
            "url": "https://example.com/article1",
            "date": "2023/4/1",
            "title": "Article 1",
            "original_text": "This is the original text of article 1. Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.",
            "dst_text": "Esto es el texto original del artículo 1."
        },
        {
            "url": "https://example.com/article2",
            "date": "2023/3/15",
            "title": "Article 2",
            "original_text": "This is the original text of article 2.",
            "dst_text": "Esto es el texto original del artículo 2."
        }
    ]

    return results


@app.get("/search", response_model=list[SearchResponse])
def search(query: str = Query(..., min_length=1)) -> list[SearchResponse]:
    # first detect the input language
    lang = detect(query)
    print(f"Detected language: {lang}")
    if lang != "en":
        query = translate(query, dst_language="english")
    print(f"(Translated) query: {query}")

    # Simulate some search results , in reality this will go to a RAG system
    results = search_in_vectorsearchDB(query)

    # Translate the results using the Google Translate API
    # translator = Translator()
    # for result in results:
    #     print(result["original_text"])
    #     result["dst_text"] = translator.translate(result["original_text"], dest="es").text

    return results