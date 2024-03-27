r"""Functions for interacting with the database.

We have the following tables in the database which we want to interact with:

repco=# \d "Transcript"
               Table "public.Transcript"
    Column     | Type | Collation | Nullable | Default 
---------------+------+-----------+----------+---------
 uid           | text |           | not null | 
 language      | text |           | not null | 
 text          | text |           | not null | 
 engine        | text |           | not null | 
 mediaAssetUid | text |           | not null | 
 author        | text |           | not null | 
 license       | text |           | not null | 
 revisionId    | text |           | not null | 
 subtitleUrl   | text |           | not null | 

 repco=# \d "ContentItem"
                                 Table "public.ContentItem"
        Column         |              Type              | Collation | Nullable |   Default   
-----------------------+--------------------------------+-----------+----------+-------------
 uid                   | text                           |           | not null | <-- 
 revisionId            | text                           |           | not null | 
 subtitle              | text                           |           |          | <-- 
 pubDate               | timestamp(3) without time zone |           |          | <-- 
 contentFormat         | text                           |           | not null | 
 primaryGroupingUid    | text                           |           |          | 
 licenseUid            | text                           |           |          | 
 publicationServiceUid | text                           |           |          | 
 title                 | jsonb                          |           | not null | '{}'::jsonb <--
 summary               | jsonb                          |           |          | 
 content               | jsonb                          |           | not null | '{}'::jsonb <--
 contentUrl            | text                           |           | not null |  <--
 originalLanguages     | jsonb                          |           |          | 

 
 repco=# \d "ContentGrouping" 
                             Table "public.ContentGrouping"
      Column       |              Type              | Collation | Nullable |   Default   
-------------------+--------------------------------+-----------+----------+-------------
 uid               | text                           |           | not null | 
 revisionId        | text                           |           | not null | 
 broadcastSchedule | text                           |           |          | 
 groupingType      | text                           |           | not null | 
 startingDate      | timestamp(3) without time zone |           |          | 
 subtitle          | text                           |           |          | 
 terminationDate   | timestamp(3) without time zone |           |          | 
 licenseUid        | text                           |           |          | 
 variant           | "ContentGroupingVariant"       |           | not null | 
 description       | jsonb                          |           |          | 
 summary           | jsonb                          |           |          | 
 title             | jsonb                          |           | not null | '{}'::jsonb
Indexes:

repco=# \d "Concept" 
                         Table "public.Concept"
       Column       |     Type      | Collation | Nullable |   Default   
--------------------+---------------+-----------+----------+-------------
 uid                | text          |           | not null | 
 revisionId         | text          |           | not null | 
 originNamespace    | text          |           |          | 
 wikidataIdentifier | text          |           |          | 
 sameAsUid          | text          |           |          | 
 parentUid          | text          |           |          | 
 kind               | "ConceptKind" |           | not null | 
 name               | jsonb         |           | not null | '{}'::jsonb
 summary            | jsonb         |           |          | 
 description        | jsonb         |           |          | 

 
We will create the following pydantic models to interact with the database:
ContentItem
Transcript
ContentGrouping 
Concept 

"""

import sys
from typing import List
from pprint import pprint

import pandas as pd
import psycopg

from pydantic import BaseModel
from tqdm import tqdm

from app.misc import  convert_html_to_text, contains_html
from app.translation import translate

__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chromadb

class Concept(BaseModel):
    """Pydantic model for the Concept table."""
    uid: str
    revisionId: str
    originNamespace: str
    wikidataIdentifier: str
    sameAsUid: str
    parentUid: str
    kind: str
    name: dict
    summary: dict
    description: dict

class ContentGrouping(BaseModel):
    """Pydantic model for the ContentGrouping table."""
    uid: str
    revisionId: str
    broadcastSchedule: str
    groupingType: str
    startingDate: str
    subtitle: str
    terminationDate: str
    licenseUid: str
    variant: str
    description: dict
    summary: dict
    title: dict

class Transcript(BaseModel):
    """Pydantic model for the Transcript table."""
    uid: str
    language: str
    text: str
    engine: str
    mediaAssetUid: str


CONTENTITEM_FIELDS = 'uid, "revisionId", subtitle, "pubDate", "contentFormat", "primaryGroupingUid", "licenseUid", "publicationServiceUid", title, summary, content, "contentUrl", "originalLanguages"'
#                     0     1            2          3          4                5                     6             7                       8      9        10        11            12
class ContentItem(BaseModel):
    """Pydantic model for the ContentItem table."""
    uid: str
    revisionId: str
    subtitle: str
    pubDate: str
    contentFormat: str
    primaryGroupingUid: str
    licenseUid: str
    publicationServiceUid: str
    title: dict
    summary: dict
    content: dict
    contentUrl: str
    originalLanguages: dict


class DB():
    """Slim wrapper around psycopg."""
    def __init__(self):
        self.conn = self.connect_to_db()
        self.cursor = self.conn.cursor()

    def query(self, sql: str, kwargs):
        """Execute a query."""
        self.cursor.execute(sql, kwargs)
        return self.cursor.fetchall()

    def close(self):
        """Close the connection."""
        self.conn.close()

    def connect_to_db(self):
        """Connect to the database."""
        conn = psycopg.connect(
            dbname='repco',
            user='repco',
            password='repco',
            host='localhost',
        )
        return conn

    def fetch_content_item_by_uid(self, uid) -> ContentItem:
        """Fetch a content item by its uid."""
        sql = f'SELECT {CONTENTITEM_FIELDS} FROM "ContentItem" WHERE uid = %s'
        return self.query(sql, uid)

    def fetch_all_content_items(self, limit: int = 0) -> List[ContentItem]:
        """Fetch all content items."""
        if limit > 0:
            sql = f'SELECT {CONTENTITEM_FIELDS} FROM "ContentItem" ORDER BY "pubDate" DESC LIMIT %s'
            return self.query(sql, (limit,))
        sql = 'SELECT * FROM "ContentItem" ORDER BY pubDate DESC'
        return self.query(sql, {})

    def fetch_random_content_items(self, limit: int = 0) -> List[ContentItem]:
        """Fetch random content items."""
        if limit > 0:
            sql = f'SELECT {CONTENTITEM_FIELDS} FROM "ContentItem" ORDER BY RANDOM() LIMIT %s'''
            return self.query(sql, (limit,))
        sql = f'SELECT {CONTENTITEM_FIELDS} FROM "ContentItem" ORDER BY RANDOM()'
        return self.query(sql, {})

    def stats_content_items(self) -> pd.DataFrame:
        """Get stats on content items."""
        sql = """
                SELECT each_entry.key, COUNT(each_entry.key) as key_count
                FROM "ContentItem",
                    jsonb_each_text(summary) as each_entry
                GROUP BY each_entry.key
                ORDER BY key_count DESC;
            """
        df = pd.DataFrame(self.query(sql, {}))
        return df



def combine_content_item_colums(content_item: ContentItem) -> str:
    """Combine the columns of a content item into a single string.
    This combines the title, subtitle, summary, and content columns into a single string and 
    cleans it up (html tags get removed).

    Example input:
      content_item = {   'uid': 'eay', "summary": {"de": {"value": "<H1>Zusammenfassung</h1>"}}, "content": {"de": {"value": "Inhalt"}}, "title": {"de": {"value": "Beispiel Titel"}}}
    Output:
      "Beispiel Titel Zusammenfassung Inhalt"

    """
    combined = ""
    # for key in ['title', 'subtitle', 'summary', 'content']:       # FIXME: subtitle needs to be cleaned up in the DB
    for key in [8,9,10]:        # pretty unelegant, but it works
        for language in content_item[key]:
            if 'value' not in content_item[key][language]:
                continue
            text = convert_html_to_text(content_item[key][language]['value'])
            # FIXME: here we might escape any existing '|' in the text
            combined += f"{text} "   # we don't need a separator here, \n is already in the text
    return combined


if __name__ == "__main__":


    chroma_client = chromadb.PersistentClient(path="./chroma.db")
    collection = chroma_client.get_or_create_collection(name="ContentItems")
    print(f"{collection.count()=}")


    db = DB()   # the postgresql DB
    df = db.stats_content_items()
    print(df.head())
    row = db.fetch_content_item_by_uid(('eaykah2ikjffarfaszdfxedk5fq',))
    row2 = db.fetch_content_item_by_uid(('eayj634lmufeqr65fkcgymtcsgs',))
    rows = [row[0], row2[0]]

    # print(combine_content_item_colums(row[0]))
    # sys.exit(0)
    rows = db.fetch_random_content_items(100)
    pprint(rows)
    # XXX FIXME: this is a list of https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes . 
    # But it would be better to get them from the official source
    LANGUAGES =  ['de', 'en', 'pl', 'sl', 'fa', 'hu', 'es', 'ar', 'fr', 'ru', 'it', 'sv', 'sq', 'lt', 'bs', 'zh', 'tr', 'bg', 'ku', 'cs', 'hr', 'pt', 'az', 'no', 'da', 'et', 'el', 'so', 'sk', 'sr', 'nl', 'uk', 'ro', 'ca', 'lv', 'an', 'be', 'mk', 'fi', 'th', 'ce', 'am', 'is', 'cy', 'mC', 'rm', 'ur', 'si', 'he', 'ko', 'yi', 'tu', 'ja']


    pprint(rows)
    for row in tqdm(rows):
        for language in LANGUAGES:
            if language in row[9]:      # example: row[9] is {'de': {'value': 'text in German'}}
                text = combine_content_item_colums(row)
                src_language = language
                dst_language = 'en'
                id = row[0]
                url = row[11]
                print(f"{src_language=}")
                print(f"{dst_language=}")
                print(f"{text=}")
                if src_language != dst_language:
                    translated_text = translate(src_text = text, dst_language=dst_language, _src_language=src_language)
                    print(80*"=")
                    print(f"ID: {id}, url: {url}")
                    print(f"{translated_text=}")
                    print(80*"/")
                # now add the document to the vector database
                collection.add(documents=[text, translated_text],
                    metadatas=[{"language": src_language, "url": url}, {"language": dst_language, "url": url}],
                    ids=[row[0], row[0]+"_en"])
                break
    db.close()
