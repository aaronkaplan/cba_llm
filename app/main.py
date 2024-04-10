"""Main fastapi application."""


import sys
import logging

from pprint import pprint
from typing import List
import pandas as pd

from fastapi import FastAPI, Query, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from langdetect import \
    detect  # https://www.geeksforgeeks.org/detect-an-unknown-language-using-python/
from pydantic import BaseModel

from app.translation import translate, translate_via_deepl
from app.db import DB


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# a handle for the postgresql repco DB
db = DB()

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


def search_in_vectorsearch_db(text: str, count_answers: int = 10) -> List[SearchResponse]:
    """Search in the vector search database using langchain and chromaDB.

    Arguments:
    text -- the text to search for
    count_answers -- the number of answers to return. -1 means all

    Returns:
    list[SearchResponse] -- the search results
    """

    print(f"{text=}")
    # first detect the input language
    query_lang = detect(text)
    logging.info(f"Detected language: {query_lang}")
    if query_lang != "en":
        query = translate(text, dst_language="EN-US")
        logging.info(f"(Translated) query: {query}")
    else:
        query = text

    # Simulate some search results , in reality this will go to a RAG system
    # search in the vector search database
    results = []
    try:
        vs_results = collection.query(query_texts=[query], n_results=count_answers)
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
            search_dict = {}
            id = d[0]
            distance = d[1]
            metadata = d[2]
            search_dict['id'] = id
            search_dict['distance'] = distance
            search_dict['date'] = metadata['date']
            search_dict['url'] = metadata['url']
            search_dict['title'] = metadata['title']
            search_dict['language'] = metadata['language']
            search_dict['dst_text'] = "".join(d[3:])
            row = db.fetch_content_item_content_by_uid(id)
            # next, find out the language in the row dict (['de'], 'en', etc.), so that we can access ['value']
            lang = search_dict['language']
            if lang in row:
                val = row[lang]['value']
            else:
                _l = list(row.keys())
                if len(_l) > 0:
                    lang = _l[0]
                    val = row[lang]['value']
            print(120 * "=")
            print(f"{val=}")
            print(120 * "=")
            search_dict['original_text'] = val
            if val:
                translated_to_query_lang = translate_via_deepl(val, dst_language=query_lang.upper())
                search_dict['dst_text'] = translated_to_query_lang
                pprint(search_dict)
            # convert to pandas dataframe
            sd_df = pd.DataFrame(search_dict, index=[0])
            pd.concat([sd_df, pd.DataFrame([search_dict])], ignore_index=True)
            sr = SearchResponse(**search_dict)
            results.append(sr)

        """
        # now after we collected all search_dicts in a pandas dataframe, we will group by id and select the best match according to the minimum distance
        results = []
        for id in sd_df['id'].unique():
            search_dict = sd_df[sd_df['id'] == id].sort_values(by='distance').iloc[0].to_dict()
        """

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

    results = search_in_vectorsearch_db(query)
    results = sorted(results, key=lambda x: x.distance, reverse=False)

    return results
