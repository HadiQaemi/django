from django.db import models
from django.db.models import JSONField
from django.contrib.postgres.fields import ArrayField
from django.utils.translation import gettext_lazy as _
from polymorphic.models import PolymorphicModel
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.contrib.postgres.indexes import GinIndex


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Author(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, null=True)
    author_id = models.CharField(max_length=255, null=True)
    given_name = models.CharField(max_length=255)
    family_name = models.CharField(max_length=255)
    label = models.TextField(null=True, blank=True)
    orcid = models.CharField(max_length=50, null=True, blank=True)
    json = JSONField(null=True, blank=True)

    class Meta:
        db_table = "authors"
        indexes = [
            models.Index(fields=["_id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label or f"{self.given_name} {self.family_name}"


class ResearchField(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, null=True)
    related_identifier = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    research_field_id = models.CharField(max_length=255, null=True)
    label = models.CharField(max_length=255)
    json = JSONField(null=True, blank=True)

    class Meta:
        db_table = "research_fields"
        indexes = [
            models.Index(fields=["_id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class SeeAlso(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, unique=True, null=True)
    label = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "see_alsos"
        indexes = [
            models.Index(fields=["_id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class Matrix(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, unique=True, null=True)
    json = JSONField(null=True, blank=True)
    label = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    type = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    exact_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    close_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )

    class Meta:
        db_table = "matrices"
        indexes = [
            models.Index(fields=["_id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class Property(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, unique=True, null=True)
    json = JSONField(null=True, blank=True)
    label = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    exact_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    close_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )

    class Meta:
        db_table = "properties"
        indexes = [
            models.Index(fields=["_id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class Unit(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, unique=True, null=True)
    json = JSONField(null=True, blank=True)
    type = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    label = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    exact_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    close_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )

    class Meta:
        db_table = "units"
        indexes = [
            models.Index(fields=["_id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class ObjectOfInterest(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, unique=True, null=True)
    json = JSONField(null=True, blank=True)
    label = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    type = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    exact_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    close_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )

    class Meta:
        db_table = "object_of_interests"
        indexes = [
            models.Index(fields=["_id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class Constraint(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, unique=True, null=True)
    json = JSONField(null=True, blank=True)
    label = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    exact_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    close_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )

    class Meta:
        db_table = "constraints"
        indexes = [
            models.Index(fields=["_id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class Operation(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, unique=True, null=True)
    json = JSONField(null=True, blank=True)
    label = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    exact_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    close_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )

    class Meta:
        db_table = "operations"
        indexes = [
            models.Index(fields=["_id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class Component(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, unique=True, null=True)
    label = models.CharField(max_length=255, null=True)
    json = JSONField(null=True, blank=True)
    matrices = models.ManyToManyField(
        Matrix,
        related_name="components",
        blank=True,
        db_index=True,
    )
    operations = models.ManyToManyField(
        Operation,
        related_name="components",
        blank=True,
        db_index=True,
    )
    object_of_interests = models.ManyToManyField(
        ObjectOfInterest,
        related_name="components",
        blank=True,
        db_index=True,
    )
    properties = models.ManyToManyField(
        Property,
        related_name="components",
        blank=True,
        db_index=True,
    )
    units = models.ManyToManyField(
        Unit,
        related_name="components",
        blank=True,
        db_index=True,
    )

    string_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    exact_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    close_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    type = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )

    ID_TYPE = [
        ("component", "Component"),
        ("measure", "Measure"),
        ("variable", "Variable"),
    ]

    class Meta:
        db_table = "components"
        indexes = [
            models.Index(fields=["_id"]),
        ]

    def __str__(self):
        return self.id


class Concept(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, null=True)
    concept_id = models.CharField(max_length=255, null=True)
    json = JSONField(null=True, blank=True)
    label = models.CharField(max_length=255)
    definition = models.TextField(null=True, blank=True)
    string_match = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    see_also = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "concepts"
        indexes = [
            models.Index(fields=["_id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class Identifier(TimeStampedModel):
    ENTITY_CHOICES = [
        ("concept", "Concept"),
        ("research_field", "ResearchField"),
        ("author", "Author"),
        ("publisher", "Publisher"),
        ("journal_conference", "JournalConference"),
        ("article", "Article"),
    ]

    ID_TYPE_CHOICES = [
        ("uuid", "UUID"),
        ("external_id", "External ID"),
        ("doi", "DOI"),
    ]

    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, null=True)
    identifier_value = models.CharField(max_length=255)
    entity_type = models.CharField(max_length=50, choices=ENTITY_CHOICES)
    identifier_type = models.CharField(
        max_length=50, choices=ID_TYPE_CHOICES, default="doi"
    )
    entity_id = models.PositiveBigIntegerField()

    class Meta:
        db_table = "identifiers"
        verbose_name = "Identifier"
        verbose_name_plural = "Identifiers"
        unique_together = [("entity_type", "entity_id", "identifier_type")]
        indexes = [
            models.Index(fields=["_id"]),
            models.Index(fields=["identifier_value"]),
            models.Index(fields=["entity_type", "entity_id"]),
        ]

    def __str__(self):
        return f"{self.identifier_value} ({self.entity_type}:{self.entity_id})"


class Publisher(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, null=True)
    publisher_id = models.CharField(max_length=255, null=True)
    json = JSONField(null=True, blank=True)
    label = models.CharField(max_length=255)

    class Meta:
        db_table = "publishers"
        indexes = [
            models.Index(fields=["_id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class JournalConference(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, null=True)
    journal_conference_id = models.CharField(max_length=255, null=True)
    json = JSONField(null=True, blank=True)
    label = models.CharField(max_length=255)
    type = models.CharField(max_length=255, null=True)
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        related_name="journals_conferences",
        null=True,
        blank=True,
        db_index=True,
    )
    research_fields = models.ManyToManyField(
        ResearchField, related_name="journals_conferences", blank=True
    )

    class Meta:
        db_table = "journals_conferences"
        indexes = [
            models.Index(fields=["_id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class Article(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    _id = models.CharField(max_length=255, null=True)
    article_id = models.CharField(max_length=255, null=True)
    json = JSONField(null=True, blank=True)
    name = models.CharField(max_length=255)
    abstract = models.TextField(null=True, blank=True)
    date_published = models.DateTimeField(null=True, blank=True)
    identifier = models.TextField(null=True, blank=True)
    reborn_doi = models.TextField(null=True, blank=True)
    paper_type = models.TextField(null=True, blank=True)
    concepts = models.ManyToManyField(Concept, related_name="articles", blank=True)
    authors = models.ManyToManyField(
        Author, related_name="articles", blank=True, through="ArticleAuthor"
    )
    research_fields = models.ManyToManyField(
        ResearchField, related_name="articles", blank=True
    )
    journal_conference = models.ForeignKey(
        JournalConference,
        on_delete=models.CASCADE,
        related_name="articles",
        null=True,
        blank=True,
        db_index=True,
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        related_name="articles",
        null=True,
        blank=True,
        db_index=True,
    )
    search_vector = SearchVectorField(null=True)

    class Meta:
        db_table = "articles"
        indexes = [
            GinIndex(fields=["search_vector"]),
            models.Index(fields=["name"]),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Article.objects.filter(pk=self.pk).update(
            search_vector=SearchVector("name", "abstract", "json")
        )

    def __str__(self):
        return self.name


class ArticleAuthor(models.Model):
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "articles_authors"
        ordering = ["order"]

    def __str__(self):
        return f"{self.article.name} - {self.author.family_name} ({self.order})"


class SchemaType(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    type_id = models.CharField(max_length=255, unique=True)
    schema_data = JSONField()
    name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )
    description = models.TextField(null=True, blank=True)
    property = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "schemata"
        indexes = [
            models.Index(fields=["type_id"]),
            models.Index(fields=["last_updated"]),
        ]

    def __str__(self):
        return self.name


class Statement(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    order = models.PositiveIntegerField(default=0)
    _id = models.CharField(max_length=255, null=True)
    statement_id = models.CharField(max_length=255, null=True)
    json = JSONField(null=True, blank=True)
    content = JSONField(null=True, blank=True)
    version = models.CharField(max_length=255, null=True)
    encodingFormat = models.CharField(max_length=255, null=True)
    name = models.CharField(max_length=255, null=True)
    label = models.CharField(null=True, blank=True)
    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name="statements",
        null=True,
        blank=True,
        db_index=True,
    )
    authors = models.ManyToManyField(
        Author,
        related_name="statements",
        blank=True,
        db_index=True,
    )
    concepts = models.ManyToManyField(
        Concept,
        related_name="statements",
        blank=True,
        db_index=True,
    )
    components = models.ManyToManyField(
        Component,
        related_name="statements",
        blank=True,
        db_index=True,
    )
    search_vector = SearchVectorField(null=True)

    class Meta:
        db_table = "statements"
        indexes = [models.Index(fields=["_id"]), GinIndex(fields=["search_vector"])]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Statement.objects.filter(pk=self.pk).update(
            search_vector=SearchVector("label", "content", "json")
        )

    def __str__(self):
        return self.name


class Implement(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    url = models.TextField(null=True, blank=True)
    statement = models.ForeignKey(
        Statement,
        on_delete=models.CASCADE,
        related_name="implement_statements",
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        db_table = "implements"
        indexes = [
            models.Index(fields=["id"]),
            models.Index(fields=["statement_id"]),
        ]

    def __str__(self):
        return self.url


class HasPart(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    label = models.TextField(null=True, blank=True)
    type = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    statement = models.ForeignKey(
        Statement,
        on_delete=models.CASCADE,
        related_name="has_part_statements",
        null=True,
        blank=True,
        db_index=True,
    )
    schema_type = models.ForeignKey(
        SchemaType,
        on_delete=models.CASCADE,
        related_name="has_parts",
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        db_table = "has_parts"
        indexes = [
            models.Index(fields=["id"]),
            models.Index(fields=["statement_id"]),
        ]

    def __str__(self):
        return self.label


class MartixSize(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    number_rows = models.TextField(null=True, blank=True)
    number_columns = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "martix_sizes"
        indexes = [
            models.Index(fields=["id"]),
        ]

    def __str__(self):
        return f"{self.number_rows} {self.number_columns}"


class DataItemComponent(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    label = models.TextField(null=True, blank=True)
    see_also = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "data_item_components"
        indexes = [
            models.Index(fields=["id"]),
        ]

    def __str__(self):
        return self.label


class Figure(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    label = models.TextField(null=True, blank=True)
    source_url = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "figures"
        indexes = [
            models.Index(fields=["id"]),
        ]

    def __str__(self):
        return self.label


class DataItem(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    label = models.TextField(null=True, blank=True)
    source_url = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    source_table = JSONField(null=True, blank=True)
    has_characteristic = models.ForeignKey(
        MartixSize,
        on_delete=models.CASCADE,
        related_name="data_item",
        null=True,
        blank=True,
        db_index=True,
    )
    has_expression = models.ManyToManyField(
        Figure,
        related_name="data_item",
        blank=True,
        db_index=True,
    )
    has_part = models.ManyToManyField(
        DataItemComponent,
        related_name="data_item",
        blank=True,
        db_index=True,
    )

    class Meta:
        db_table = "data_items"
        indexes = [
            models.Index(fields=["id"]),
        ]

    def __str__(self):
        return self.label


class Software(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    label = models.TextField(null=True, blank=True)
    version_info = models.TextField(null=True, blank=True)
    has_support_url = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "softwares"
        indexes = [
            models.Index(fields=["id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class SoftwareLibrary(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    label = models.TextField(null=True, blank=True)
    version_info = models.TextField(null=True, blank=True)
    has_support_url = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )
    part_of = models.ForeignKey(
        Software,
        on_delete=models.CASCADE,
        related_name="part_of_software",
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        db_table = "software_libraries"
        indexes = [
            models.Index(fields=["id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class SoftwareMethod(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    label = models.TextField(null=True, blank=True)
    part_of = models.ManyToManyField(
        SoftwareLibrary,
        related_name="software_methods",
        blank=True,
        db_index=True,
    )
    is_implemented_by = ArrayField(
        models.TextField(null=True, blank=True), blank=True, null=True, default=list
    )
    has_support_url = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )

    class Meta:
        db_table = "software_methods"
        indexes = [
            models.Index(fields=["id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class DataType(TimeStampedModel, PolymorphicModel):
    id = models.AutoField(primary_key=True)
    label = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=255)
    see_also = models.CharField(max_length=255)
    statement = models.ForeignKey(
        Statement,
        on_delete=models.CASCADE,
        related_name="data_type_statement",
        null=True,
        blank=True,
        db_index=True,
    )
    executes = models.ManyToManyField(
        SoftwareMethod,
        related_name="software_method",
        blank=True,
        db_index=True,
    )
    has_inputs = models.ManyToManyField(
        DataItem,
        related_name="input_data",
        blank=True,
        db_index=True,
    )
    has_outputs = models.ManyToManyField(
        DataItem,
        related_name="output_data",
        blank=True,
        db_index=True,
    )
    schema_type = models.ForeignKey(
        SchemaType,
        on_delete=models.CASCADE,
        related_name="data_type",
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        db_table = "data_types"
        indexes = [
            models.Index(fields=["id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class DataPreprocessing(DataType):
    data_preprocessing_label = models.CharField(max_length=255)

    class Meta:
        db_table = "data_preprocessing"

    def __str__(self):
        return self.id


class DescriptiveStatistics(DataType):
    descriptive_statistics_label = models.CharField(max_length=255)

    class Meta:
        db_table = "descriptive_statistics"

    def __str__(self):
        return self.id


class SharedType(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    label = models.TextField(null=True, blank=True)
    type = models.TextField(null=True, blank=True)
    see_also = ArrayField(
        models.CharField(max_length=255), blank=True, null=True, default=list
    )

    class Meta:
        db_table = "shared_types"
        indexes = [
            models.Index(fields=["id"]),
            models.Index(fields=["label"]),
        ]

    def __str__(self):
        return self.label


class AlgorithmEvaluation(DataType):
    evaluate = models.ForeignKey(
        SharedType,
        on_delete=models.CASCADE,
        related_name="evaluate",
        null=True,
        blank=True,
        db_index=True,
    )
    evaluates_for = models.ForeignKey(
        SharedType,
        on_delete=models.CASCADE,
        related_name="evaluates_for",
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        db_table = "algorithm_evaluations"

    def __str__(self):
        return self.id


class MultilevelAnalysis(DataType):
    targets = models.ManyToManyField(
        SharedType,
        related_name="targets_multilevel_analysis",
        blank=True,
        db_index=True,
    )
    level = models.ManyToManyField(
        SharedType,
        related_name="level_multilevel_analysis",
        blank=True,
        db_index=True,
    )

    class Meta:
        db_table = "multilevel_analysis"

    def __str__(self):
        return self.id


class CorrelationAnalysis(DataType):
    correlation_analysis_label = models.CharField(max_length=255)

    class Meta:
        db_table = "correlation_analysis"

    def __str__(self):
        return self.id


class GroupComparison(DataType):
    targets = models.ManyToManyField(
        SharedType,
        related_name="group_comparisons",
        blank=True,
        db_index=True,
    )

    class Meta:
        db_table = "group_comparisons"

    def __str__(self):
        return self.id


class RegressionAnalysis(DataType):
    targets = models.ManyToManyField(
        SharedType,
        related_name="regression_analysis",
        blank=True,
        db_index=True,
    )

    class Meta:
        db_table = "regression_analysis"

    def __str__(self):
        return self.id


class ClassPrediction(DataType):
    targets = models.ManyToManyField(
        SharedType,
        related_name="class_predictions",
        blank=True,
        db_index=True,
    )

    class Meta:
        db_table = "class_predictions"

    def __str__(self):
        return self.id


class ClassDiscovery(DataType):
    class_discovery_label = models.CharField(max_length=255)

    class Meta:
        db_table = "class_discoveries"

    def __str__(self):
        return self.id


class FactorAnalysis(DataType):
    factor_analysis_label = models.CharField(max_length=255)

    class Meta:
        db_table = "factor_analysis"

    def __str__(self):
        return self.id


class Statistics(TimeStampedModel):
    mean = models.TextField(null=True, blank=True)
    standard_deviation = models.TextField(null=True, blank=True)


class Contribution(TimeStampedModel):
    id = models.CharField(max_length=255, primary_key=True)
    contribution_paper_id = models.CharField(max_length=255)
    json_id = models.TextField(null=True, blank=True)
    json_type = models.TextField(null=True, blank=True)
    json_context = JSONField(null=True, blank=True)
    label = models.TextField(null=True, blank=True)
    title = models.TextField(null=True, blank=True)
    author = JSONField(null=True, blank=True)
    info = JSONField(null=True, blank=True)
    predicates = JSONField(null=True, blank=True)

    class Meta:
        db_table = "contributions"
        indexes = [
            models.Index(fields=["contribution_paper_id"]),
            models.Index(fields=["json_id"]),
        ]

    def __str__(self):
        return self.title or self.label or self.id
