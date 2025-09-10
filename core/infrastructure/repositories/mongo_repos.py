"""
MongoDB repository implementations for the REBORN API.

These repositories implement the repository interfaces using MongoDB.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pymongo import MongoClient
from bson import ObjectId, json_util, Regex
from django.conf import settings
import json
import hashlib
from datetime import datetime

from core.application.interfaces.repositories.author import AuthorRepository
from core.application.interfaces.repositories.concept import ConceptRepository
from core.application.interfaces.repositories.journal import JournalRepository
from core.application.interfaces.repositories.paper import PaperRepository
from core.application.interfaces.repositories.research_field import (
    ResearchFieldRepository,
)
from core.application.interfaces.repositories.statement import StatementRepository
from core.application.mappers.entity_mappers import (
    PaperMapper,
    StatementMapper,
    AuthorMapper,
    ConceptMapper,
    ResearchFieldMapper,
)
from core.domain.entities import (
    Article,
    Statement,
    Author,
    Concept,
    ResearchField,
)
from core.domain.exceptions import DatabaseError
from core.infrastructure.scrapers.node_extractor import NodeExtractor

logger = logging.getLogger(__name__)


def generate_static_id(input_string: str) -> str:
    """Generate a static ID from a string."""
    hash_object = hashlib.sha256(input_string.encode("utf-8"))
    return hash_object.hexdigest()[:32]


def fetch_reborn_doi(doi: str) -> str:
    """Fetch the reborn DOI from a regular DOI."""
    import requests

    url = "https://api.datacite.org/dois"
    query = f'relatedIdentifiers.relatedIdentifier:"{doi.replace("https://doi.org/", "")}" AND relatedIdentifiers.relationType:IsVariantFormOf'
    params = {"query": query}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        result = response.json()

        if not result.get("data"):
            return ""

        return f"https://doi.org/{result['data'][0]['id']}"

    except Exception as e:
        logger.error(f"Error fetching reborn DOI: {str(e)}")
        return ""


class MongoDBPaperRepository(PaperRepository):
    """MongoDB implementation of the Paper repository."""

    def __init__(self):
        """Initialize the repository."""
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB]
        self.scraper = NodeExtractor()

    def find_all(self, page: int = 1, page_size: int = 10) -> Tuple[List[Article], int]:
        """Find all papers with pagination."""
        try:
            collection = self.db["articles"]
            skip = (page - 1) * page_size
            total = collection.count_documents({})

            cursor = collection.find().skip(skip).limit(page_size)
            papers = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                paper = PaperMapper.from_dict(document_json)
                papers.append(paper)

            return papers, total

        except Exception as e:
            logger.error(f"Error in find_all: {str(e)}")
            raise DatabaseError(f"Failed to retrieve papers: {str(e)}")

    def find_by_id(self, paper_id: str) -> Optional[Article]:
        """Find a paper by its ID."""
        try:
            collection = self.db["articles"]
            document = collection.find_one({"article_id": paper_id})

            if document:
                document_json = json.loads(json_util.dumps(document))
                return PaperMapper.from_dict(document_json)

            return None

        except Exception as e:
            logger.error(f"Error in find_by_id: {str(e)}")
            raise DatabaseError(f"Failed to retrieve paper: {str(e)}")

    def search_by_title(self, title: str) -> List[Article]:
        """Search papers by title."""
        try:
            collection = self.db["articles"]
            regex = Regex(title, "i")
            query = {"name": regex}

            cursor = collection.find(query)
            papers = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                paper = PaperMapper.from_dict(document_json)
                papers.append(paper)

            return papers

        except Exception as e:
            logger.error(f"Error in search_by_title: {str(e)}")
            raise DatabaseError(f"Failed to search papers: {str(e)}")

    def query_papers(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        author_ids: Optional[List[str]] = None,
        journal_names: Optional[List[str]] = None,
        concept_ids: Optional[List[str]] = None,
        conference_names: Optional[List[str]] = None,
        title: Optional[str] = None,
        research_fields: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Article], int]:
        """Query papers with filters."""
        try:
            collection = self.db["statements"]
            match = {}

            if title:
                match["$or"] = [
                    {"article.name": {"$regex": title, "$options": "i"}},
                    {"supports.notation.label": {"$regex": title, "$options": "i"}},
                    {"article.identifier": {"$regex": title, "$options": "i"}},
                ]

            if author_ids and len(author_ids) > 0:
                match["authors_id"] = {"$in": author_ids}

            if journal_names and len(journal_names) > 0:
                journals = []
                for journal_name in journal_names:
                    journals.append(ObjectId(journal_name))
                match["journals_conferences_id"] = {"$in": journals}

            if concept_ids and len(concept_ids) > 0:
                concepts = []
                for concept_id in concept_ids:
                    concepts.append(ObjectId(concept_id))
                match["supports.notation.concept._id"] = {"$in": concepts}

            if start_year and end_year:
                match["datePublished"] = {
                    "$gte": datetime(int(start_year), 1, 1),
                    "$lte": datetime(int(end_year), 12, 31),
                }

            if research_fields and len(research_fields) > 0:
                match["research_fields_id"] = {"$in": research_fields}

            pipeline = [
                {
                    "$lookup": {
                        "from": "concepts",
                        "localField": "concept_ids",
                        "foreignField": "@id",
                        "as": "concepts",
                    }
                },
                {
                    "$lookup": {
                        "from": "authors",
                        "localField": "author_ids",
                        "foreignField": "id",
                        "as": "authors",
                    }
                },
                {
                    "$lookup": {
                        "from": "articles",
                        "localField": "article_id",
                        "foreignField": "_id",
                        "as": "article",
                    }
                },
                {"$unwind": {"path": "$article", "preserveNullAndEmptyArrays": True}},
                {
                    "$lookup": {
                        "from": "authors",
                        "localField": "article.author_ids",
                        "foreignField": "_id",
                        "as": "article_authors",
                    }
                },
                {"$match": match},
                {
                    "$project": {
                        "_id": "$statement_id",
                        "name": 1,
                        "author": 1,
                        "components": 1,
                        "supports": 1,
                        "content": 1,
                        "label": "$content.doi:a72ca256dc49e55a1a57#has_notation.doi:44164d31a37c28d8efbf#label",
                        "article": {
                            "doi": "$article.@id",
                            "type": "$article.@type",
                            "articleDatePublished": "$article.datePublished",
                            "hasPart": "$article.Dataset.hasPart",
                            "rebornDatePublished": {
                                "$dateToString": {
                                    "format": "%B %d, %Y",
                                    "date": {
                                        "$toDate": "$article.Dataset.datePublished"
                                    },
                                }
                            },
                            "identifier": "$article.identifier",
                            "journal": "$article.journal",
                            "abstract": "$article.abstract",
                            "conference": "$article.conference",
                            "researchField": "$article.researchField",
                            "rebornDOI": "$article.rebornDOI",
                            "research_field": "$article.research_field",
                            "name": "$article.name",
                            "publisher": "$article.publisher",
                            "paper_type": "$article.paper_type",
                            "authors": "$article.author",
                            "id": "$article.article_id",
                        },
                    }
                },
                {"$sort": {"_id": 1}},
                {"$skip": (page - 1) * page_size},
                {"$limit": page_size},
            ]

            docs = list(collection.aggregate(pipeline))
            total = collection.count_documents(match)

            papers = []
            for doc in docs:
                doc_json = json.loads(json_util.dumps(doc))
                paper = PaperMapper.from_dict(doc_json["article"])
                papers.append(paper)

            return papers, total

        except Exception as e:
            logger.error(f"Error in query_papers: {str(e)}")
            raise DatabaseError(f"Failed to query papers: {str(e)}")

    def save(self, paper: Article) -> Article:
        """Save a paper."""
        try:
            collection = self.db["articles"]

            if not paper.id:
                paper.id = generate_static_id(paper.title)

            # Convert to dictionary
            paper_dict = {}
            for key, value in paper.__dict__.items():
                if key == "author":
                    paper_dict["author"] = [author.__dict__ for author in paper.author]
                elif key == "research_fields":
                    paper_dict["research_field"] = [
                        rf.__dict__ for rf in paper.research_fields
                    ]
                    paper_dict["research_fields_id"] = paper.research_fields_id
                else:
                    paper_dict[key] = value

            # Add timestamps
            if not paper_dict.get("created_at"):
                paper_dict["created_at"] = datetime.utcnow()
            paper_dict["updated_at"] = datetime.utcnow()

            # Upsert
            result = collection.update_one(
                {"_id": paper_dict["id"]}, {"$set": paper_dict}, upsert=True
            )

            return paper

        except Exception as e:
            logger.error(f"Error in save: {str(e)}")
            raise DatabaseError(f"Failed to save paper: {str(e)}")

    def get_latest_articles(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Article], int]:
        """Get latest articles with filters."""
        try:
            collection = self.db["articles"]
            query = {}

            if search_query:
                query["$or"] = [{"name": {"$regex": search_query, "$options": "i"}}]

            if research_fields and len(research_fields) > 0:
                query["research_fields_id"] = {"$in": research_fields}

            if sort_order == "a-z":
                sort_config = [("name", 1)]
            elif sort_order == "z-a":
                sort_config = [("name", -1)]
            elif sort_order == "newest":
                sort_config = [("created_at", -1)]
            else:
                sort_config = [("name", 1)]

            skip = (page - 1) * page_size
            total = collection.count_documents(query)

            cursor = (
                collection.find(query).sort(sort_config).skip(skip).limit(page_size)
            )
            papers = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                paper = PaperMapper.from_dict(document_json)
                papers.append(paper)

            return papers, total

        except Exception as e:
            logger.error(f"Error in get_latest_articles: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest articles: {str(e)}")

    def get_semantics_articles(
        self,
        ids: List[str],
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Article], int]:
        """Get articles by IDs from semantic search."""
        try:
            collection = self.db["articles"]
            query = {}

            if ids and len(ids) > 0:
                article_ids = [ObjectId(article_id) for article_id in ids]
                query["_id"] = {"$in": article_ids}

            if sort_order == "a-z":
                sort_config = [("name", 1)]
            elif sort_order == "z-a":
                sort_config = [("name", -1)]
            elif sort_order == "newest":
                sort_config = [("created_at", -1)]
            else:
                sort_config = [("name", 1)]

            skip = (page - 1) * page_size
            total = min(collection.count_documents(query), 10)

            cursor = (
                collection.find(query).sort(sort_config).skip(skip).limit(page_size)
            )
            papers = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                paper = PaperMapper.from_dict(document_json)
                papers.append(paper)

            return papers, total

        except Exception as e:
            logger.error(f"Error in get_semantics_articles: {str(e)}")
            raise DatabaseError(f"Failed to retrieve articles by IDs: {str(e)}")

    def delete_database(self) -> bool:
        """Delete the database."""
        try:
            self.client.drop_database(settings.MONGODB_DB)
            return True

        except Exception as e:
            logger.error(f"Error in delete_database: {str(e)}")
            return False

    def add_article(
        self, paper_data: Dict[str, Any], json_files: Dict[str, str]
    ) -> bool:
        # """Add an article from scraped data."""
        # try:
        scraper = NodeExtractor()
        graph_data = paper_data.get("@graph", [])
        data = {}

        data["Dataset"] = [
            item for item in graph_data if "Dataset" in item.get("@type", [])
        ]

        data["researchField"] = [
            item for item in graph_data if "ResearchField" in item.get("@type", [])
        ]
        research_fields = []
        research_field_ids = []

        for research_field in data["researchField"]:
            research_field_id = generate_static_id(research_field["label"])
            item_check = self.db.research_fields.find_one({"@id": research_field_id})

            if item_check is None:
                research_field["@id"] = research_field_id
                self.db.research_fields.insert_one(research_field)
                item_check = self.db.research_fields.find_one(
                    {"@id": research_field_id}
                )

            research_fields.append(item_check)
            research_field_ids.append(research_field_id)
        print("research_fields:")
        print(research_fields)
        data["author"] = [item for item in graph_data if item.get("@type") == "Person"]
        authors = []

        for author in data["author"]:
            temp = author.copy()
            temp["research_fields_id"] = research_fields
            temp["label"] = (
                f"{author.get('givenName', '')} {author.get('familyName', '')}"
            )
            author_id = generate_static_id(author["@id"])
            temp["id"] = author_id

            item_check = self.db.authors.find_one({"id": author_id})
            if item_check is None:
                self.db.authors.insert_one(temp)

            authors.append(author_id)
        print("authors:")
        print(authors)
        data["publisher"] = [
            item for item in graph_data if "Publisher" in item.get("@type", [])
        ]

        data["journal"] = [
            item for item in graph_data if "Journal" in item.get("@type", [])
        ]
        journals_conferences = []

        for journal in data["journal"]:
            journal["research_fields_id"] = research_field_ids
            journal["publisher"] = data["publisher"]
            result = self.db.journals_conferences.insert_one(journal)
            journals_conferences.append(result.inserted_id)

        print("journals_conferences:")
        print(journals_conferences)

        data["conference"] = [
            item for item in graph_data if "Conference" in item.get("@type", [])
        ]

        for conference in data["conference"]:
            conference["research_fields_id"] = research_field_ids
            conference["publisher"] = data["publisher"]
            result = self.db.journals_conferences.insert_one(conference)
            journals_conferences.append(result.inserted_id)

        print("journals_conferences:")
        print(journals_conferences)

        data["concept"] = [
            item for item in graph_data if "Concept" in item.get("@type", [])
        ]
        data["concept"] = [
            item for item in graph_data if "Concept" in item.get("@type", [])
        ]
        concepts = []
        print('data["concept"]:')
        print(data["concept"])
        for concept in data["concept"]:
            concept_id = generate_static_id(concept["label"])
            item_check = self.db.concepts.find_one({"id": concept_id})

            if item_check is None:
                concept["id"] = concept_id
                concept["research_fields_id"] = research_field_ids
                result = self.db.concepts.insert_one(concept)
                concept_id = result.inserted_id
            else:
                concept_id = item_check["_id"]

            concepts.append(concept_id)

        # Process other entity types
        for entity_type in [
            "ObjectOfInterest",
            "matrix",
            "property",
            "constraint",
            "operation",
            "unit",
        ]:
            data[entity_type] = [
                item
                for item in graph_data
                if entity_type.title() in item.get("@type", [])
            ]
            print(f"entity_type:${entity_type}")
            print(data[entity_type])
            print(entity_type.lower() + "s")
            if data[entity_type]:
                self.db[entity_type.lower() + "s"].insert_many(data[entity_type])

        # Process component, variable, measure, identifier, notation, supports, file
        for entity_type in [
            "component",
            "variable",
            "measure",
            "identifier",
            "notation",
            "supports",
            "file",
        ]:
            data[entity_type] = [
                self._replace_with_full_data(item, data)
                for item in graph_data
                if entity_type.title() in item.get("@type", [])
            ]
            if data[entity_type]:
                self.db[entity_type + "s"].insert_many(data[entity_type])

        ScholarlyArticle = [
            self._replace_with_full_data(item, data)
            for item in graph_data
            if "ScholarlyArticle" in item.get("@type", [])
        ]

        ScholarlyArticle[0]["article_id"] = generate_static_id(
            ScholarlyArticle[0]["name"]
        )
        ScholarlyArticle[0]["research_fields_id"] = research_field_ids
        ScholarlyArticle[0]["researchField"] = research_fields
        ScholarlyArticle[0]["research_field"] = research_fields
        ScholarlyArticle[0]["Dataset"] = data["Dataset"][0]
        ScholarlyArticle[0]["rebornDOI"] = fetch_reborn_doi(ScholarlyArticle[0]["@id"])

        article = self.db.articles.insert_one(ScholarlyArticle[0])
        inserted_id = article.inserted_id

        data["statements"] = [
            self._replace_with_full_data(item, data)
            for item in graph_data
            if item.get("encodingFormat", "") == "application/ld+json"
            and "File" in item.get("@type", [])
        ]

        # Add to search index
        # article_data = [
        #     {
        #         "title": ScholarlyArticle[0]["name"],
        #         "abstract": ScholarlyArticle[0]["abstract"],
        #         "article_id": str(article.inserted_id),
        #     }
        # ]

        # Import here to avoid circular import
        # from core.infrastructure.search.hybrid_engine import HybridSearchEngine
        # from core.infrastructure.search.semantic_engine import SemanticSearchEngine
        # from core.infrastructure.search.keyword_engine import KeywordSearchEngine

        # semantic_engine = SemanticSearchEngine()
        # keyword_engine = KeywordSearchEngine()
        # hybrid_engine = HybridSearchEngine(semantic_engine, keyword_engine)

        # hybrid_engine.semantic_engine.add_articles(article_data)
        # hybrid_engine.keyword_engine.add_articles(article_data)

        for statement in data["statements"]:
            temp = statement.copy()
            temp["content"] = scraper.load_json_from_url(
                json_files[statement.get("name", "")]
            )
            temp["article_id"] = inserted_id
            temp["concepts_id"] = concepts
            temp["research_fields_id"] = research_field_ids
            temp["journals_conferences_id"] = journals_conferences
            temp["authors_id"] = authors
            temp["datePublished"] = datetime(
                int(ScholarlyArticle[0]["datePublished"]), 6, 6
            )
            print(temp["supports"])
            temp["statement_id"] = generate_static_id(
                temp["supports"][0]["notation"]["label"]
            )

            # statement_result = self.db.statements.insert_one(temp)

            # Add to search index
            # statement_data = [
            #     {
            #         "text": temp["supports"][0]["notation"]["label"],
            #         "abstract": ScholarlyArticle[0]["abstract"],
            #         "statement_id": str(statement_result.inserted_id),
            #     }
            # ]

            # hybrid_engine.semantic_engine.add_statements(statement_data)
            # hybrid_engine.keyword_engine.add_statements(statement_data)

        return True

    # except Exception as e:
    #     logger.error(f"Error in add_article: {str(e)}")
    #     raise DatabaseError(f"Failed to add article isssssssss: {str(e)}")

    def _replace_with_full_data(
        self, item: Dict[str, Any], data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Replace references with full data."""
        field_mapping = {
            "author": "author",
            "journal": "journal",
            "publisher": "publisher",
            "researchField": "researchField",
            "concept": "concept",
            "objectOfInterest": "objectOfInterest",
            "matrix": "matrix",
            "property": "property",
            "constraint": "constraint",
            "operation": "operation",
            "unit": "unit",
            "components": "component",
            "variable": "variable",
            "measure": "measure",
            "identifier": "identifier",
            "notation": "notation",
            "supports": "supports",
            "file": "file",
            "conference": "conference",
        }

        def find_by_id(id_value, type_list):
            return next(
                (item for item in type_list if item.get("@id") == id_value), None
            )

        def process_field(field_value, dict_key):
            if isinstance(field_value, list):
                return [
                    find_by_id(f.get("@id"), data[dict_key]) or f
                    for f in field_value
                    if isinstance(f, dict) and "@id" in f
                ]
            elif isinstance(field_value, dict) and "@id" in field_value:
                return find_by_id(field_value["@id"], data[dict_key]) or field_value
            return field_value

        result = item.copy()

        for field_name, dict_key in field_mapping.items():
            if field_name in result:
                result[field_name] = process_field(result[field_name], dict_key)

        return result


class MongoDBStatementRepository(StatementRepository):
    """MongoDB implementation of the Statement repository."""

    def __init__(self):
        """Initialize the repository."""
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB]

    def find_all(
        self, page: int = 1, page_size: int = 10
    ) -> Tuple[List[Statement], int]:
        """Find all statements with pagination."""
        try:
            collection = self.db["statements"]
            skip = (page - 1) * page_size
            total = collection.count_documents({})

            cursor = collection.find().skip(skip).limit(page_size)
            statements = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                statement = StatementMapper.from_dict(document_json)
                statements.append(statement)

            return statements, total

        except Exception as e:
            logger.error(f"Error in find_all: {str(e)}")
            raise DatabaseError(f"Failed to retrieve statements: {str(e)}")

    def find_by_id(self, statement_id: str) -> Optional[Statement]:
        """Find a statement by its ID."""
        try:
            collection = self.db["statements"]
            document = collection.find_one({"statement_id": statement_id})

            if document:
                document_json = json.loads(json_util.dumps(document))
                return StatementMapper.from_dict(document_json)

            return None

        except Exception as e:
            logger.error(f"Error in find_by_id: {str(e)}")
            raise DatabaseError(f"Failed to retrieve statement: {str(e)}")

    def find_by_paper_id(self, paper_id: str) -> List[Statement]:
        """Find statements by paper ID."""
        try:
            collection = self.db["statements"]

            # First get the article ObjectId
            article_collection = self.db["articles"]
            article = article_collection.find_one({"article_id": paper_id})

            if not article:
                return []

            article_id = article["_id"]

            # Now find statements with this article_id
            cursor = collection.find({"article_id": article_id})
            statements = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                statement = StatementMapper.from_dict(document_json)
                statements.append(statement)

            return statements

        except Exception as e:
            logger.error(f"Error in find_by_paper_id: {str(e)}")
            raise DatabaseError(f"Failed to retrieve statements by paper ID: {str(e)}")

    def save(self, statement: Statement) -> Statement:
        """Save a statement."""
        try:
            collection = self.db["statements"]

            if not statement.id:
                statement.id = generate_static_id(
                    statement.article_id + str(datetime.utcnow())
                )

            # Convert to dictionary
            statement_dict = {}
            for key, value in statement.__dict__.items():
                if key == "author":
                    statement_dict["author"] = [
                        author.__dict__ for author in statement.author
                    ]
                else:
                    statement_dict[key] = value

            # Add timestamps
            if not statement_dict.get("created_at"):
                statement_dict["created_at"] = datetime.utcnow()
            statement_dict["updated_at"] = datetime.utcnow()

            # Upsert
            result = collection.update_one(
                {"_id": statement_dict["id"]}, {"$set": statement_dict}, upsert=True
            )

            return statement

        except Exception as e:
            logger.error(f"Error in save: {str(e)}")
            raise DatabaseError(f"Failed to save statement: {str(e)}")

    def get_latest_statements(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Statement], int]:
        """Get latest statements with filters."""
        try:
            collection = self.db["statements"]
            match_stage = {}

            if search_query:
                match_stage["$or"] = [
                    {
                        "supports.0.notation.label": {
                            "$regex": search_query,
                            "$options": "i",
                        }
                    }
                ]

            if research_fields and len(research_fields) > 0:
                research_field_ids = [field_id for field_id in research_fields]
                match_stage["research_fields_id"] = {"$in": research_field_ids}

            if sort_order == "a-z":
                sort_config = {"article.name": 1}
            elif sort_order == "z-a":
                sort_config = {"article.name": -1}
            elif sort_order == "newest":
                sort_config = {"created_at": -1}
            else:
                sort_config = {"article.name": 1}

            pipeline = [
                {"$match": match_stage},
                {
                    "$lookup": {
                        "from": "articles",
                        "localField": "article_id",
                        "foreignField": "_id",
                        "as": "article",
                    }
                },
                {"$unwind": {"path": "$article", "preserveNullAndEmptyArrays": True}},
                {"$sort": sort_config},
                {"$skip": (page - 1) * page_size},
                {"$limit": page_size},
            ]

            cursor = collection.aggregate(pipeline)
            statements = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                statement = StatementMapper.from_dict(document_json)
                statements.append(statement)

            total = collection.count_documents(match_stage)

            return statements, total

        except Exception as e:
            logger.error(f"Error in get_latest_statements: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest statements: {str(e)}")

    def get_semantics_statements(
        self,
        ids: List[str],
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Statement], int]:
        """Get statements by IDs from semantic search."""
        try:
            collection = self.db["statements"]
            match_stage = {}

            if ids and len(ids) > 0:
                statement_ids = [ObjectId(statement_id) for statement_id in ids]
                match_stage["_id"] = {"$in": statement_ids}

            if sort_order == "a-z":
                sort_config = {"article.name": 1}
            elif sort_order == "z-a":
                sort_config = {"article.name": -1}
            elif sort_order == "newest":
                sort_config = {"created_at": -1}
            else:
                sort_config = {"article.name": 1}

            pipeline = [
                {"$match": match_stage},
                {
                    "$lookup": {
                        "from": "articles",
                        "localField": "article_id",
                        "foreignField": "_id",
                        "as": "article",
                    }
                },
                {"$unwind": {"path": "$article", "preserveNullAndEmptyArrays": True}},
                {"$sort": sort_config},
                {"$skip": (page - 1) * page_size},
                {"$limit": page_size},
            ]

            cursor = collection.aggregate(pipeline)
            statements = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                statement = StatementMapper.from_dict(document_json)
                statements.append(statement)

            total_count = collection.count_documents(match_stage)
            total = min(
                total_count, 10
            )  # Limit total to 10 as in original implementation

            return statements, total

        except Exception as e:
            logger.error(f"Error in get_semantics_statements: {str(e)}")
            raise DatabaseError(f"Failed to retrieve statements by IDs: {str(e)}")


class MongoDBAuthorRepository(AuthorRepository):
    """MongoDB implementation of the Author repository."""

    def __init__(self):
        """Initialize the repository."""
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB]

    def get_authors_by_name(self, name: str) -> List[Author]:
        """Find authors by name."""
        pass

    def get_academic_publishers_by_name(self, name: str) -> List[Author]:
        """Find academic publishers by name."""
        pass

    def save(self, author: Author) -> Author:
        """Save an author."""
        try:
            collection = self.db["authors"]

            if not author.id:
                author.id = generate_static_id(author.given_name + author.family_name)

            # Convert to dictionary
            author_dict = {}
            for key, value in author.__dict__.items():
                author_dict[key] = value

            # Upsert
            result = collection.update_one(
                {"_id": author_dict["id"]}, {"$set": author_dict}, upsert=True
            )

            return author

        except Exception as e:
            logger.error(f"Error in save: {str(e)}")
            raise DatabaseError(f"Failed to save author: {str(e)}")

    def get_latest_authors(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Author], int]:
        """Get latest authors with filters."""
        try:
            collection = self.db["authors"]
            query = {}

            if search_query:
                query["$or"] = [{"label": {"$regex": search_query, "$options": "i"}}]

            if research_fields and len(research_fields) > 0:
                query["research_fields_id"] = {"$in": research_fields}

            if sort_order == "a-z":
                sort_config = [("label", 1)]
            elif sort_order == "z-a":
                sort_config = [("label", -1)]
            elif sort_order == "newest":
                sort_config = [("created_at", -1)]
            else:
                sort_config = [("label", 1)]

            skip = (page - 1) * page_size
            total = collection.count_documents(query)

            cursor = (
                collection.find(query).sort(sort_config).skip(skip).limit(page_size)
            )
            authors = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                author = AuthorMapper.from_dict(document_json)
                authors.append(author)

            return authors, total

        except Exception as e:
            logger.error(f"Error in get_latest_authors: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest authors: {str(e)}")


class MongoDBConceptRepository(ConceptRepository):
    """MongoDB implementation of the Concept repository."""

    def __init__(self):
        """Initialize the repository."""
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB]

    def find_by_label(self, label: str) -> List[Concept]:
        """Find concepts by label."""
        try:
            collection = self.db["concepts"]
            regex = Regex(label, "i")
            query = {"label": regex}

            cursor = collection.find(query).limit(10)
            concepts = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                concept = ConceptMapper.from_dict(document_json)
                concepts.append(concept)

            return concepts

        except Exception as e:
            logger.error(f"Error in find_by_label: {str(e)}")
            raise DatabaseError(f"Failed to find concepts: {str(e)}")

    def save(self, concept: Concept) -> Concept:
        """Save a concept."""
        try:
            collection = self.db["concepts"]

            if not concept.id:
                concept.id = generate_static_id(concept.label)

            # Convert to dictionary
            concept_dict = {}
            for key, value in concept.__dict__.items():
                concept_dict[key] = value

            # Upsert
            result = collection.update_one(
                {"_id": concept_dict["id"]}, {"$set": concept_dict}, upsert=True
            )

            return concept

        except Exception as e:
            logger.error(f"Error in save: {str(e)}")
            raise DatabaseError(f"Failed to save concept: {str(e)}")

    def get_latest_concepts(self, limit: int = 8) -> List[Concept]:
        """Get latest concepts."""
        try:
            collection = self.db["concepts"]
            cursor = collection.find().limit(limit)
            concepts = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                concept = ConceptMapper.from_dict(document_json)
                concepts.append(concept)

            return concepts

        except Exception as e:
            logger.error(f"Error in get_latest_concepts: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest concepts: {str(e)}")

    def get_latest_keywords(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Concept], int]:
        """Get latest keywords with filters."""
        try:
            collection = self.db["concepts"]
            query = {}

            if search_query:
                query["$or"] = [{"label": {"$regex": search_query, "$options": "i"}}]

            if research_fields and len(research_fields) > 0:
                query["research_fields_id"] = {"$in": research_fields}

            if sort_order == "a-z":
                sort_config = [("label", 1)]
            elif sort_order == "z-a":
                sort_config = [("label", -1)]
            elif sort_order == "newest":
                sort_config = [("created_at", -1)]
            else:
                sort_config = [("label", 1)]

            skip = (page - 1) * page_size
            total = collection.count_documents(query)

            cursor = (
                collection.find(query).sort(sort_config).skip(skip).limit(page_size)
            )
            concepts = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                concept = ConceptMapper.from_dict(document_json)
                concepts.append(concept)

            return concepts, total

        except Exception as e:
            logger.error(f"Error in get_latest_keywords: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest keywords: {str(e)}")


class MongoDBResearchFieldRepository(ResearchFieldRepository):
    """MongoDB implementation of the ResearchField repository."""

    def __init__(self):
        """Initialize the repository."""
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB]

    def find_by_label(self, label: str) -> List[ResearchField]:
        """Find research fields by label."""
        try:
            collection = self.db["research_fields"]
            regex = Regex(label, "i")
            query = {"label": regex}

            cursor = collection.find(query).limit(10)
            research_fields = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                research_field = ResearchFieldMapper.from_dict(document_json)
                research_fields.append(research_field)

            return research_fields

        except Exception as e:
            logger.error(f"Error in find_by_label: {str(e)}")
            raise DatabaseError(f"Failed to find research fields: {str(e)}")

    def save(self, research_field: ResearchField) -> ResearchField:
        """Save a research field."""
        try:
            collection = self.db["research_fields"]

            if not research_field.id:
                research_field.id = generate_static_id(research_field.label)

            # Convert to dictionary
            rf_dict = {}
            for key, value in research_field.__dict__.items():
                rf_dict[key] = value

            # Upsert
            result = collection.update_one(
                {"_id": rf_dict["id"]}, {"$set": rf_dict}, upsert=True
            )

            return research_field

        except Exception as e:
            logger.error(f"Error in save: {str(e)}")
            raise DatabaseError(f"Failed to save research field: {str(e)}")


class MongoDBJournalRepository(JournalRepository):
    """MongoDB implementation of the Journal repository."""

    def __init__(self):
        """Initialize the repository."""
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client[settings.MONGODB_DB]

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find journals by name."""
        try:
            collection = self.db["journals_conferences"]
            regex = Regex(name, "i")
            query = {"label": regex}

            cursor = collection.find(query).limit(10)
            journals = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                journals.append(document_json)

            return journals

        except Exception as e:
            logger.error(f"Error in find_by_name: {str(e)}")
            raise DatabaseError(f"Failed to find journals: {str(e)}")

    def get_latest_journals(
        self,
        research_fields: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        sort_order: str = "a-z",
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get latest journals with filters."""
        try:
            collection = self.db["journals_conferences"]
            query = {}

            if search_query:
                query["$or"] = [{"label": {"$regex": search_query, "$options": "i"}}]

            if research_fields and len(research_fields) > 0:
                query["research_fields_id"] = {"$in": research_fields}

            if sort_order == "a-z":
                sort_config = [("label", 1)]
            elif sort_order == "z-a":
                sort_config = [("label", -1)]
            elif sort_order == "newest":
                sort_config = [("created_at", -1)]
            else:
                sort_config = [("label", 1)]

            skip = (page - 1) * page_size
            total = collection.count_documents(query)

            cursor = (
                collection.find(query).sort(sort_config).skip(skip).limit(page_size)
            )
            journals = []

            for document in cursor:
                document_json = json.loads(json_util.dumps(document))
                journals.append(document_json)

            return journals, total

        except Exception as e:
            logger.error(f"Error in get_latest_journals: {str(e)}")
            raise DatabaseError(f"Failed to retrieve latest journals: {str(e)}")
