"""Main fastapi application."""


import sys
import logging

from pprint import pprint

from typing import List

from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langdetect import \
    detect  # https://www.geeksforgeeks.org/detect-an-unknown-language-using-python/
from pydantic import BaseModel

from app.translation import translate

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# this is an ugly hack to make chromaDB work with the sqlite3 module
# see also https://stackoverflow.com/questions/77004853/chromadb-langchain-with-sentencetransformerembeddingfunction-throwing-sqlite3
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chromadb     # noqa:


# try to load the chromaDB
try:
    chroma_client = chromadb.PersistentClient(path="./chroma.db")
    collection = chroma_client.get_or_create_collection(name="ContentItems")
    logging.info("ChromaDB loaded")
    logging.info(f"{collection.count()=}")
except Exception as e:
    logging.error(f"Failed to load ChromaDB: {e}")
    raise e


class SearchResponse(BaseModel):
    """Search response model."""
    id: str
    distance: float     # the distance of the search result
    date: str
    url: str
    title: str
    language: str
    original_text: str
    dst_text: str


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    """Display the index.html page"""
    return templates.TemplateResponse("index.html", {"request": request})


def search_in_vectorsearch_db(text: str, count_answers: int = 3) -> List[SearchResponse]:
    """Search in the vector search database using langchain and chromaDB.

    Arguments:
    text -- the text to search for
    count_answers -- the number of answers to return. -1 means all

    Returns:
    list[SearchResponse] -- the search results
    """

    # first translate the text to english
    # try:
    #     text = translate(text, dst_language="english")
    # except Exception as e:
    #     logging.error(f"Translation failed: {e}")
    #     raise HTTPException(status_code=500, detail="Translation failed")

    # now search in the vector search database
    results = []
    try:
        vs_results = collection.query(query_texts=[text], n_results=count_answers)
        # pprint(vs_results)
        print(f"{type(vs_results)=}")
        print(f"{vs_results.keys()=}")
        # vs_results.keys()=dict_keys(['ids', 'distances', 'metadatas', 'embeddings', 'documents', 'uris', 'data'])
        ids = vs_results['ids'][0]
        distances = vs_results['distances'][0]
        metadatas = vs_results['metadatas'][0]
        documents = vs_results['documents'][0]
        data = zip(ids, distances, metadatas, documents)
        # pprint(list(data))
        # convert the vs_restults to the SearchResponse model
        for d in data:
            print(f"{type(d)=}")
            pprint(d)
            print(80 * "-")
            sd = {}
            id = d[0]
            distance = d[1]
            metadata = d[2]
            sd['id'] = id
            sd['distance'] = distance
            sd['date'] = metadata['date']
            sd['url'] = metadata['url']
            sd['title'] = metadata['title']
            sd['language'] = metadata['language']
            sd['original_text'] = "".join(d[3:])
            sd['dst_text'] = sd['original_text']      # XXX FIXME: this is a placeholder
            pprint(sd)
            sr = SearchResponse(**sd)
            results.append(sr)

        return results
    except Exception as e:
        logging.error(f"Search failed: {e}")
        raise e
        raise HTTPException(status_code=500, detail="Search failed")

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

    """
    return results


@app.get("/search", response_model=List[SearchResponse])
def search(query: str = Query(..., min_length=1)) -> List[SearchResponse]:
    # first detect the input language
    lang = detect(query)
    logging.info(f"Detected language: {lang}")
    # if lang != "en":
    #    query = translate(query, dst_language="english")
    # logging.info(f"(Translated) query: {query}")

    # Simulate some search results , in reality this will go to a RAG system
    results = search_in_vectorsearch_db(query)
    results = sorted(results, key=lambda x: x.distance, reverse=False)

    return results
