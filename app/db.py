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

import logging
import sys
import os

from pprint import pprint
from typing import List

from tqdm import tqdm
import pandas as pd
import psycopg
from pydantic import BaseModel

from app.misc import cleanup_text, convert_html_to_text
from app.translation import translate

# this is an ugly hack to make chromaDB work with the sqlite3 module
# see also https://stackoverflow.com/questions/77004853/chromadb-langchain-with-sentencetransformerembeddingfunction-throwing-sqlite3
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import chromadb     # noqa:

# Postgresql stuff for the repco database
DEFAULT_DSN = "dbname=repco user=repco password=repco host=localhost"
DSN = os.getenv("DSN", DEFAULT_DSN)


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
        try:
            conn = psycopg.connect(conninfo=DSN)
        except psycopg.Error as e:
            logging.error(f"Error connecting to the database: {e}")
            sys.exit(1)
        return conn

    def fetch_content_item_by_uid(self, uid) -> ContentItem:
        """Fetch a content item by its uid."""
        sql = f'SELECT {CONTENTITEM_FIELDS} FROM "ContentItem" WHERE uid = %s'
        return self.query(sql, uid)

    def fetch_content_item_content_by_uid(self, uid: str) -> str:
        """Fetch the content of a content item by its uid."""
        sql = 'SELECT content FROM "ContentItem" WHERE uid = %s'
        result = self.query(sql, (uid,))
        if not result:
            logging.warning(f"Content item with uid {uid} not found.")
            return ""
        return result[0][0]

    def fetch_all_content_items(self, limit: int = 0) -> List[ContentItem]:
        """Fetch all content items."""
        if limit > 0:
            sql = f'SELECT {CONTENTITEM_FIELDS} FROM "ContentItem" ORDER BY "pubDate" DESC LIMIT %s'
            return self.query(sql, (limit,))
        sql = 'SELECT * FROM "ContentItem" ORDER BY pubDate DESC'
        return self.query(sql, {})

    def fetch_random_content_items(self, limit: int = 0, seed: float = None) -> List[ContentItem]:
        """Fetch random content items."""
        if seed:
            sql = f'SELECT setseed({seed});'
            _result = self.query(sql, seed)
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
    for key in [8, 9, 10]:        # pretty unelegant, but it works
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
    logging.info(f"{collection.count()=}")

    # make a pandas df for collecting all the data which gets stored into the vector database
    df_content_items = pd.DataFrame(columns=["id", "url", "pubDate", "title", "text", "dst_text"])

    db = DB()   # the postgresql DB
    df = db.stats_content_items()
    print(df.head())
    row = db.fetch_content_item_by_uid(('eaykah2ikjffarfaszdfxedk5fq',))
    row2 = db.fetch_content_item_by_uid(('eayj634lmufeqr65fkcgymtcsgs',))
    rows = [row[0], row2[0]]

    rows = db.fetch_random_content_items(4500)
    # pprint(rows)
    # XXX NOTE: this is a list of https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes .
    # But it would be better to get them from the official source
    LANGUAGES = ['de', 'en', 'pl', 'sl', 'fa', 'hu', 'es', 'ar', 'fr', 'ru', 'it', 'sv', 'sq', 'lt', 'bs', 'zh', 'tr', 'bg', 'ku', 'cs', 'hr', 'pt', 'az', 'no', 'da', 'et',
                 'el', 'so', 'sk', 'sr', 'nl', 'uk', 'ro', 'ca', 'lv', 'an', 'be', 'mk', 'fi', 'th', 'ce', 'am', 'is', 'cy', 'mC', 'rm', 'ur', 'si', 'he', 'ko', 'yi', 'tu', 'ja']

    logging.info("Starting to translate the content items")
    for row in tqdm(rows):
        for language in LANGUAGES:
            if language in row[9]:      # example: row[9] is {'de': {'value': 'text in German'}}
                text = combine_content_item_colums(row)
                text = cleanup_text(text)
                src_language = language
                dst_language = 'en'
                id = row[0]             # pylint: disable=redifined-builtin
                url = row[11]
                pubDate = str(row[3].date())
                title = row[8]
                parsed_title = ''       # pylint: disable=invalid-name
                for _language in LANGUAGES:     # FIXME: this should be more elegant
                    if _language in title and 'value' in title[_language]:
                        parsed_title = cleanup_text(title[_language]['value'])
                        break   # we found it
                pprint(f"{text=}, {src_language=}, {dst_language=}, {id=}, {url=}, {pubDate=}, {parsed_title=}", indent=2)
                if src_language != dst_language:
                    try:
                        dst_text = translate(src_text=text, dst_language=dst_language, _src_language=src_language)
                    except Exception as e:
                        logging.error(f"Translation failed for {id}: {e}")
                        logging.debug(f"Dump of the row: {row}")
                        dst_text = None
                        continue
                    if not dst_text:
                        logging.warning("Translation failed for ID %s" % id)
                else:
                    dst_text = text
                    # now add the document to the vector database

                # now we split the text into sentences and add them to the vector database
                # split by \n
                sentences = dst_text.split("\n")    # might want to explore other chunking methods here
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                    print(f"Adding sentence: {sentence}")
                    collection.add(documents=[sentence],
                                   metadatas=[{"title": parsed_title, "date": pubDate, "language": src_language, "url": url}],
                                   ids=[row[0]])
                # append the whole row (translated & original) to the pandas df_content_items
                df2 = pd.DataFrame({"id": id, "url": url,
                                    "pubDate": pubDate, "title": parsed_title, "text": text,
                                    "dst_text": dst_text}, index=[0])
                df_content_items = pd.concat([df_content_items, df2], ignore_index=True)
                break
    db.close()

    # finally write the df_content_items to an XLSX file via pandas:
    df_content_items.to_excel("content_items.xlsx", index=False)
    print("Data written to content_items.xksx")
    print(df_content_items.head())
