import mongoengine as me
from datetime import datetime
from typing import Any, Dict, List, Optional


class Author(me.Document):
    """Author model for MongoDB."""

    id = me.StringField(primary_key=True)
    given_name = me.StringField(required=True)
    family_name = me.StringField(required=True)
    label = me.StringField()
    research_fields_id = me.ListField(me.StringField())

    meta = {"collection": "authors", "indexes": ["label", "research_fields_id"]}


class Concept(me.Document):
    """Concept model for MongoDB."""

    id = me.StringField(primary_key=True)
    label = me.StringField(required=True)
    identifier = me.StringField()
    research_fields_id = me.ListField(me.StringField())

    meta = {"collection": "concepts", "indexes": ["label", "research_fields_id"]}


class ResearchField(me.Document):
    """Research field model for MongoDB."""

    id = me.StringField(primary_key=True)
    label = me.StringField(required=True)

    meta = {"collection": "research_fields", "indexes": ["label"]}


class JournalConference(me.Document):
    """Journal or conference model for MongoDB."""

    id = me.StringField(primary_key=True)
    label = me.StringField(required=True)
    publisher = me.DictField()
    research_fields_id = me.ListField(me.StringField())

    meta = {
        "collection": "journals_conferences",
        "indexes": ["label", "research_fields_id"],
    }


class Notation(me.EmbeddedDocument):
    """Notation model for MongoDB."""

    id = me.StringField()
    label = me.StringField(required=True)
    concept = me.DictField()


class Support(me.EmbeddedDocument):
    """Support model for MongoDB."""

    id = me.StringField()
    notation = me.EmbeddedDocumentField(Notation)


class Statement(me.Document):
    """Statement model for MongoDB."""

    id = me.StringField(primary_key=True)
    statement_id = me.StringField()
    content = me.DictField()
    author = me.ListField(me.DictField())
    article_id = me.StringField(required=True)
    supports = me.ListField(me.EmbeddedDocumentField(Support))
    authors_id = me.ListField(me.StringField())
    concepts_id = me.ListField(me.StringField())
    research_fields_id = me.ListField(me.StringField())
    journals_conferences_id = me.ListField(me.StringField())
    date_published = me.DateTimeField()
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "statements",
        "indexes": [
            "statement_id",
            "article_id",
            "authors_id",
            "concepts_id",
            "research_fields_id",
            "journals_conferences_id",
            "date_published",
            "created_at",
            "updated_at",
        ],
    }


class DatasetPart(me.EmbeddedDocument):
    """Dataset part model for MongoDB."""

    id = me.StringField()
    name = me.StringField()


class Dataset(me.EmbeddedDocument):
    """Dataset model for MongoDB."""

    id = me.StringField()
    has_part = me.ListField(me.EmbeddedDocumentField(DatasetPart))
    date_published = me.DateTimeField()


class Article(me.Document):
    """Article model for MongoDB."""

    id = me.StringField(primary_key=True)
    article_id = me.StringField(unique=True)
    name = me.StringField(required=True)
    abstract = me.StringField()
    author = me.ListField(me.DictField())
    date_published = me.DateTimeField()
    publisher = me.DictField()
    journal = me.DictField()
    conference = me.DictField()
    identifier = me.StringField()
    paper_type = me.StringField()
    reborn_doi = me.StringField()
    research_field = me.ListField(me.DictField())
    dataset = me.EmbeddedDocumentField(Dataset)
    research_fields_id = me.ListField(me.StringField())
    author_ids = me.ListField(me.StringField())
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "articles",
        "indexes": [
            "article_id",
            "name",
            "author_ids",
            "research_fields_id",
            "date_published",
            "created_at",
            "updated_at",
        ],
    }


class Contribution(me.Document):
    """Contribution model for MongoDB."""

    id = me.StringField(primary_key=True)
    paper_id = me.StringField(required=True)
    json_id = me.StringField()
    json_type = me.StringField()
    json_context = me.DictField()
    label = me.StringField()
    title = me.StringField()
    author = me.ListField(me.DictField())
    info = me.DictField()
    predicates = me.DictField()
    created_at = me.DateTimeField(default=datetime.utcnow)
    updated_at = me.DateTimeField(default=datetime.utcnow)

    meta = {
        "collection": "contributions",
        "indexes": ["paper_id", "json_id", "created_at", "updated_at"],
    }
