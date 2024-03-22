"""Classes to interface the postgresql DB via pydantic models

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
 uid                   | text                           |           | not null | 
 revisionId            | text                           |           | not null | 
 subtitle              | text                           |           |          | 
 pubDate               | timestamp(3) without time zone |           |          | 
 contentFormat         | text                           |           | not null | 
 primaryGroupingUid    | text                           |           |          | 
 licenseUid            | text                           |           |          | 
 publicationServiceUid | text                           |           |          | 
 title                 | jsonb                          |           | not null | '{}'::jsonb
 summary               | jsonb                          |           |          | 
 content               | jsonb                          |           | not null | '{}'::jsonb
 contentUrl            | text                           |           | not null | 

 
We will create the following pydantic models to interact with the database:
ContentItem
Transcript

"""

from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ContentItem(Base):
    __tablename__ = 'ContentItem'
    
    uid = Column(String, primary_key=True)
    subtitle = Column(String) 
    pubDate = Column(String)
    contentFormat = Column(String)
    title = Column(JSON)
    summary = dict
    content = dict
    contentUrl = str

    def __init__(self, uid: str, subtitle: str, pubDate: str, contentFormat: str, title: dict, summary: dict, content: dict, contentUrl: str):
        self.uid = uid
        self.subtitle = subtitle
        self.pubDate = pubDate
        self.contentFormat = contentFormat
        self.title = title
        self.summary = summary
        self.content = content
        self.contentUrl = contentUrl

    def __repr__(self):
        return f"<ContentItem(uid={self.uid}, title={self.title})>"
    
    def fetch_content_item_by_uid(self, uid: str):
        return self.query.filter_by(uid=uid).first()

    def fetch_content_item_by_title(self, title: str):
        return self.query.filter_by(title=title).first()
