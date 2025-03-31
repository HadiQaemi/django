"""
SQL models for the REBORN API.

These models represent the data structure in PostgreSQL.
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """Base model with created and updated timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Author(TimeStampedModel):
    """Author model for SQL."""

    id = models.CharField(max_length=255, primary_key=True)
    given_name = models.CharField(max_length=255)
    family_name = models.CharField(max_length=255)
    label = models.CharField(max_length=255, null=True, blank=True)
    research_fields_id = ArrayField(
        models.CharField(max_length=255), null=True, blank=True
    )

    class Meta:
        db_table = "authors"
        indexes = [
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label or f"{self.given_name} {self.family_name}"


class ResearchField(TimeStampedModel):
    """Research field model for SQL."""

    id = models.CharField(max_length=255, primary_key=True)
    label = models.CharField(max_length=255)

    class Meta:
        db_table = "research_fields"
        indexes = [
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class Concept(TimeStampedModel):
    """Concept model for SQL."""

    id = models.CharField(max_length=255, primary_key=True)
    label = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255, null=True, blank=True)
    research_fields_id = ArrayField(
        models.CharField(max_length=255), null=True, blank=True
    )
    research_fields = models.ManyToManyField(
        ResearchField, related_name="concepts", blank=True
    )

    class Meta:
        db_table = "concepts"
        indexes = [
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class JournalConference(TimeStampedModel):
    """Journal or conference model for SQL."""

    id = models.CharField(max_length=255, primary_key=True)
    label = models.CharField(max_length=255)
    publisher = JSONField(null=True, blank=True)
    research_fields_id = ArrayField(
        models.CharField(max_length=255), null=True, blank=True
    )
    research_fields = models.ManyToManyField(
        ResearchField, related_name="journals_conferences", blank=True
    )

    class Meta:
        db_table = "journals_conferences"
        indexes = [
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class Article(TimeStampedModel):
    """Article model for SQL."""

    id = models.CharField(max_length=255, primary_key=True)
    article_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    abstract = models.TextField(null=True, blank=True)
    date_published = models.DateTimeField(null=True, blank=True)
    publisher = JSONField(null=True, blank=True)
    journal = JSONField(null=True, blank=True)
    conference = JSONField(null=True, blank=True)
    identifier = models.CharField(max_length=255, null=True, blank=True)
    paper_type = models.CharField(max_length=255, null=True, blank=True)
    reborn_doi = models.CharField(max_length=255, null=True, blank=True)
    research_field = JSONField(null=True, blank=True)
    dataset = JSONField(null=True, blank=True)
    research_fields_id = ArrayField(
        models.CharField(max_length=255), null=True, blank=True
    )
    author_ids = ArrayField(models.CharField(max_length=255), null=True, blank=True)
    authors = models.ManyToManyField(Author, related_name="articles", blank=True)
    research_fields = models.ManyToManyField(
        ResearchField, related_name="articles", blank=True
    )
    concepts = models.ManyToManyField(Concept, related_name="articles", blank=True)

    class Meta:
        db_table = "articles"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["date_published"]),
        ]

    def __str__(self):
        return self.name


class Statement(TimeStampedModel):
    """Statement model for SQL."""

    id = models.CharField(max_length=255, primary_key=True)
    statement_id = models.CharField(max_length=255, null=True, blank=True)
    content = JSONField()
    author = JSONField()
    article_id = models.CharField(max_length=255)
    supports = JSONField(null=True, blank=True)
    authors_id = ArrayField(models.CharField(max_length=255), null=True, blank=True)
    concepts_id = ArrayField(models.CharField(max_length=255), null=True, blank=True)
    research_fields_id = ArrayField(
        models.CharField(max_length=255), null=True, blank=True
    )
    journals_conferences_id = ArrayField(
        models.CharField(max_length=255), null=True, blank=True
    )
    date_published = models.DateTimeField(null=True, blank=True)
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="statements",
        to_field="article_id",
    )
    authors = models.ManyToManyField(Author, related_name="statements", blank=True)
    concepts = models.ManyToManyField(Concept, related_name="statements", blank=True)
    research_fields = models.ManyToManyField(
        ResearchField, related_name="statements", blank=True
    )

    class Meta:
        db_table = "statements"
        indexes = [
            models.Index(fields=["statement_id"]),
            models.Index(fields=["article_id"]),
            models.Index(fields=["date_published"]),
        ]

    def __str__(self):
        return self.statement_id or self.id


class Contribution(TimeStampedModel):
    """Contribution model for SQL."""

    id = models.CharField(max_length=255, primary_key=True)
    paper_id = models.CharField(max_length=255)
    json_id = models.CharField(max_length=255, null=True, blank=True)
    json_type = models.CharField(max_length=255, null=True, blank=True)
    json_context = JSONField(null=True, blank=True)
    label = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    author = JSONField(null=True, blank=True)
    info = JSONField(null=True, blank=True)
    predicates = JSONField(null=True, blank=True)
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="contributions",
        to_field="article_id",
        db_column="paper_id",
    )

    class Meta:
        db_table = "contributions"
        indexes = [
            models.Index(fields=["paper_id"]),
            models.Index(fields=["json_id"]),
        ]

    def __str__(self):
        return self.title or self.label or self.id
