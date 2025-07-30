from collections import defaultdict

import logging
import re

from core.application.interfaces.repositories.author import AuthorRepository
from core.application.interfaces.repositories.concept import ConceptRepository
from core.application.interfaces.repositories.journal import JournalRepository
from core.application.interfaces.repositories.paper import PaperRepository
from core.application.interfaces.repositories.research_field import (
    ResearchFieldRepository,
)
from core.application.interfaces.repositories.statement import StatementRepository
from core.application.interfaces.services.insight import (
    InsightService as InsightServiceInterface,
)

from core.domain.exceptions import SearchEngineError

from django.db.models import Count, Q
from django.db.models.functions import TruncMonth

from core.infrastructure.models.sql_models import (
    Software as SoftwareModel,
    SoftwareLibrary as SoftwareLibraryModel,
    DataPreprocessing as DataPreprocessingModel,
    DescriptiveStatistics as DescriptiveStatisticsModel,
    AlgorithmEvaluation as AlgorithmEvaluationModel,
    MultilevelAnalysis as MultilevelAnalysisModel,
    CorrelationAnalysis as CorrelationAnalysisModel,
    GroupComparison as GroupComparisonModel,
    RegressionAnalysis as RegressionAnalysisModel,
    ClassPrediction as ClassPredictionModel,
    ClassDiscovery as ClassDiscoveryModel,
    FactorAnalysis as FactorAnalysisModel,
    Concept as ConceptModel,
    Component as ComponentModel,
    Article as ArticleModel,
    Statement as StatementModel,
)

logger = logging.getLogger(__name__)


class InsightServiceImpl(InsightServiceInterface):
    def __init__(
        self,
        author_repository: AuthorRepository,
        concept_repository: ConceptRepository,
        research_field_repository: ResearchFieldRepository,
        journal_repository: JournalRepository,
        paper_repository: PaperRepository,
        statement_repository: StatementRepository,
    ):
        self.author_repository = author_repository
        self.concept_repository = concept_repository
        self.research_field_repository = research_field_repository
        self.journal_repository = journal_repository
        self.paper_repository = paper_repository
        self.statement_repository = statement_repository

    def get_research_components(self, research_fields) -> any:
        print("--------get_research_components---------")
        print(research_fields, __file__)

        try:
            components_with_usage = (
                ComponentModel.objects.annotate(
                    usage_count=Count(
                        "statements",
                        filter=Q(
                            statements__article__research_fields__research_field_id__in=research_fields
                        ),
                        distinct=True,
                    )
                )
                .filter(usage_count__gt=0)
                .prefetch_related(
                    "matrices", "object_of_interests", "properties", "units"
                )
            )
            components_results = []
            for component in components_with_usage:
                label = re.sub(r"[\[\]']", "", component.label)
                if "Measure" in component.type or "Property" in component.type:
                    components_results.append(
                        {
                            "text": component.string_match[0],
                            "label": component.string_match[0],
                            "definition": label,
                            "value": component.usage_count,
                            "see_also": component.exact_match[0]
                            if len(component.exact_match) > 0
                            else component.close_match[0]
                            if len(component.close_match) > 0
                            else "",
                            "operations": [],
                            "matrices": [],
                            "object_of_interests": [],
                            "properties": [],
                            "units": [],
                        }
                    )
                else:
                    operations = []
                    for operation in component.operations.all():
                        operations.append(
                            {
                                "label": operation.label[0],
                                "see_also": operation.exact_match[0]
                                if len(operation.exact_match) > 0
                                else operation.close_match[0]
                                if len(operation.close_match) > 0
                                else "",
                            }
                        )
                    matrices = []
                    for matrix in component.matrices.all():
                        matrices.append(
                            {
                                "label": matrix.label[0],
                                "see_also": matrix.exact_match[0]
                                if len(matrix.exact_match) > 0
                                else matrix.close_match[0]
                                if len(matrix.close_match) > 0
                                else "",
                            }
                        )
                    object_of_interests = []
                    for object_of_interest in component.object_of_interests.all():
                        object_of_interests.append(
                            {
                                "label": object_of_interest.label[0],
                                "see_also": object_of_interest.exact_match[0]
                                if len(object_of_interest.exact_match) > 0
                                else object_of_interest.close_match[0]
                                if len(object_of_interest.close_match) > 0
                                else "",
                            }
                        )
                    properties = []
                    for property in component.properties.all():
                        properties.append(
                            {
                                "label": property.label[0],
                                "see_also": property.exact_match[0]
                                if len(property.exact_match) > 0
                                else property.close_match[0]
                                if len(property.close_match) > 0
                                else "",
                            }
                        )
                    units = []
                    for unit in component.units.all():
                        units.append(
                            {
                                "label": unit.label[0],
                                "see_also": unit.exact_match[0]
                                if len(unit.exact_match) > 0
                                else unit.close_match[0]
                                if len(unit.close_match) > 0
                                else "",
                            }
                        )
                    components_results.append(
                        {
                            "text": component.string_match[0],
                            "label": component.string_match[0],
                            "definition": label,
                            "value": component.usage_count,
                            "see_also": component.exact_match
                            if len(component.exact_match) > 0
                            else component.close_match,
                            "operations": operations,
                            "matrices": matrices,
                            "object_of_interests": object_of_interests,
                            "properties": properties,
                            "units": units,
                        }
                    )
            return {"items": components_results}

        except Exception as e:
            logger.error(f"Error in research components {str(e)}")
            raise SearchEngineError(f"Failed to perform research components: {str(e)}")

    def get_research_concepts(self, research_fields) -> any:
        print("--------get_research_concepts---------")
        print(research_fields, __file__)

        try:
            concepts_with_usage = (
                ConceptModel.objects.annotate(
                    usage_count=Count(
                        "statements",
                        filter=Q(
                            statements__article__research_fields__research_field_id__in=research_fields
                        ),
                        distinct=True,
                    )
                )
                .filter(usage_count__gt=0)
                .values("label", "definition", "usage_count")
            )
            concepts_results = []
            for concept in concepts_with_usage:
                label = concept["label"]
                acronym = None

                match = re.search(r"\(([^)]+)\)", label)
                if match:
                    acronym = match.group(1).strip()
                else:
                    words = label.split()
                    if len(words) > 3:
                        selected_words = words[:3]
                        acronym = " ".join(word for word in selected_words) + "..."
                    else:
                        acronym = label

                concepts_results.append(
                    {
                        "label": label,
                        "definition": concept["definition"],
                        "value": concept["usage_count"],
                        "text": acronym,
                    }
                )
            return {"items": concepts_results}

        except Exception as e:
            logger.error(f"Error in research components {str(e)}")
            raise SearchEngineError(f"Failed to perform research components: {str(e)}")

    def get_research_insights(self) -> any:
        """Perform search on authors by name."""
        # cache_key = f"get_research_insights"
        # cached_result = cache.get(cache_key)

        # if cached_result:
        #     return cached_result
        print("-------get_research_insights-------", __file__)

        try:
            models_by_label = SoftwareModel.objects.values("label").annotate(
                count=Count("id")
            )
            total_count = sum(item["count"] for item in models_by_label)

            for item in models_by_label:
                item["count"] = round((item["count"] / total_count) * 100)

            qs = (
                SoftwareLibraryModel.objects.exclude(label__isnull=True)
                .exclude(label__exact="")
                .values("part_of__label", "label")
                .annotate(count=Count("id"))
                .order_by("-count")
            )
            grouped_data = defaultdict(list)

            for item in qs:
                label = item["part_of__label"]
                grouped_data[label].append(
                    {"label": item["label"], "count": item["count"]}
                )

            models = [
                ("Data Preprocessing", DataPreprocessingModel),
                ("Descriptive Statistics", DescriptiveStatisticsModel),
                ("Algorithm Evaluation", AlgorithmEvaluationModel),
                ("Multilevel Analysis", MultilevelAnalysisModel),
                ("Correlation Analysis", CorrelationAnalysisModel),
                ("Group Comparison", GroupComparisonModel),
                ("Regression Analysis", RegressionAnalysisModel),
                ("Class Prediction", ClassPredictionModel),
                ("Class Discovery", ClassDiscoveryModel),
                ("Factor Analysis", FactorAnalysisModel),
            ]
            data_types = [
                {"label": name, "count": model.objects.count()}
                for name, model in models
            ]
            data_types = sorted(
                [
                    {"label": name, "count": model.objects.count()}
                    for name, model in models
                    if model.objects.count() > 0
                ],
                key=lambda x: x["count"],
                reverse=True,
            )

            concepts_with_usage = (
                ConceptModel.objects.annotate(usage_count=Count("statements"))
                .filter(usage_count__gt=0)
                .values("label", "definition", "usage_count")
            )
            concepts_results = []
            for concept in concepts_with_usage:
                label = concept["label"]
                acronym = None

                match = re.search(r"\(([^)]+)\)", label)
                if match:
                    acronym = match.group(1).strip()
                else:
                    words = label.split()
                    if len(words) > 3:
                        selected_words = words[:3]
                        acronym = " ".join(word for word in selected_words) + "..."
                    else:
                        acronym = label

                concepts_results.append(
                    {
                        "label": label,
                        "definition": concept["definition"],
                        "value": concept["usage_count"],
                        "text": acronym,
                    }
                )

            components_with_usage = (
                ComponentModel.objects.annotate(usage_count=Count("statements"))
                .filter(usage_count__gt=0)
                .prefetch_related(
                    "matrices", "object_of_interests", "properties", "units"
                )
            )
            components_results = []
            for component in components_with_usage:
                label = re.sub(r"[\[\]']", "", component.label)
                if "Measure" in component.type or "Property" in component.type:
                    components_results.append(
                        {
                            "text": component.string_match[0],
                            "label": component.string_match[0],
                            "definition": label,
                            "value": component.usage_count,
                            "see_also": component.exact_match[0]
                            if len(component.exact_match) > 0
                            else component.close_match[0]
                            if len(component.close_match) > 0
                            else "",
                            "operations": [],
                            "matrices": [],
                            "object_of_interests": [],
                            "properties": [],
                            "units": [],
                        }
                    )
                else:
                    operations = []
                    for operation in component.operations.all():
                        operations.append(
                            {
                                "label": operation.label[0],
                                "see_also": operation.exact_match[0]
                                if len(operation.exact_match) > 0
                                else operation.close_match[0]
                                if len(operation.close_match) > 0
                                else "",
                            }
                        )
                    matrices = []
                    for matrix in component.matrices.all():
                        matrices.append(
                            {
                                "label": matrix.label[0],
                                "see_also": matrix.exact_match[0]
                                if len(matrix.exact_match) > 0
                                else matrix.close_match[0]
                                if len(matrix.close_match) > 0
                                else "",
                            }
                        )
                    object_of_interests = []
                    for object_of_interest in component.object_of_interests.all():
                        object_of_interests.append(
                            {
                                "label": object_of_interest.label[0],
                                "see_also": object_of_interest.exact_match[0]
                                if len(object_of_interest.exact_match) > 0
                                else object_of_interest.close_match[0]
                                if len(object_of_interest.close_match) > 0
                                else "",
                            }
                        )
                    properties = []
                    for property in component.properties.all():
                        properties.append(
                            {
                                "label": property.label[0],
                                "see_also": property.exact_match[0]
                                if len(property.exact_match) > 0
                                else property.close_match[0]
                                if len(property.close_match) > 0
                                else "",
                            }
                        )
                    units = []
                    for unit in component.units.all():
                        units.append(
                            {
                                "label": unit.label[0],
                                "see_also": unit.exact_match[0]
                                if len(unit.exact_match) > 0
                                else unit.close_match[0]
                                if len(unit.close_match) > 0
                                else "",
                            }
                        )
                    components_results.append(
                        {
                            "text": component.string_match[0],
                            "label": component.string_match[0],
                            "definition": label,
                            "value": component.usage_count,
                            "see_also": component.exact_match
                            if len(component.exact_match) > 0
                            else component.close_match,
                            "operations": operations,
                            "matrices": matrices,
                            "object_of_interests": object_of_interests,
                            "properties": properties,
                            "units": units,
                        }
                    )

            articles_per_month = (
                ArticleModel.objects.filter(reborn_date_published__isnull=False)
                .annotate(month=TruncMonth("reborn_date_published"))
                .values("month")
                .annotate(article_count=Count("id"))
                .order_by("month")
            )

            statements_per_month = (
                StatementModel.objects.filter(
                    article__reborn_date_published__isnull=False
                )
                .annotate(month=TruncMonth("article__reborn_date_published"))
                .values("month")
                .annotate(statement_count=Count("id"))
                .order_by("month")
            )

            result = defaultdict(lambda: {"article_count": 0, "statement_count": 0})

            for entry in articles_per_month:
                result[entry["month"]]["article_count"] = entry["article_count"]

            for entry in statements_per_month:
                result[entry["month"]]["statement_count"] = entry["statement_count"]

            articles_statements_per_month = [
                {
                    "month": month.strftime("%Y - %B"),
                    "article_count": counts["article_count"],
                    "statement_count": counts["statement_count"],
                }
                for month, counts in sorted(result.items())
            ]

            return {
                "statistics": {
                    "Articles": self.paper_repository.get_count_all(),
                    "Scientific statements": self.statement_repository.get_count_all(),
                    "Journals": self.journal_repository.get_count_all(),
                    "Authors": self.author_repository.get_count_all(),
                },
                "articles_statements_per_month": articles_statements_per_month,
                "num_programming_languages": models_by_label,
                "num_packages": grouped_data,
                "data_types": data_types,
                "concepts": concepts_results,
                "components": components_results,
            }

        except Exception as e:
            logger.error(f"Error in get research insights {str(e)}")
            raise SearchEngineError(
                f"Failed to perform get research insights: {str(e)}"
            )
