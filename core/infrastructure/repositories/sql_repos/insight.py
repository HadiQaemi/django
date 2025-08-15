from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.db.models import Count, Q
from core.application.interfaces.repositories.insight import InsightRepository
from core.domain.exceptions import DatabaseError
from core.infrastructure.models.sql_models import (
    Software as SoftwareModel,
    SoftwareLibrary as SoftwareLibraryModel,
    Article as ArticleModel,
    Statement as StatementModel,
    Concept as ConceptModel,
    Component as ComponentModel,
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
)
from collections import defaultdict
import logging
import re

logger = logging.getLogger(__name__)


class SQLInsightRepository(InsightRepository):
    def get_per_month_articles_statements(self, research_fields=None) -> any:
        qs = ArticleModel.objects.filter(reborn_date_published__isnull=False)
        if research_fields:
            qs = qs.filter(research_fields__research_field_id__in=research_fields)
        articles_per_month = (
            qs.annotate(month=TruncMonth("reborn_date_published"))
            .values("month")
            .annotate(article_count=Count("id"))
            .order_by("month")
            .distinct()
        )
        qs = StatementModel.objects.filter(article__reborn_date_published__isnull=False)
        if research_fields:
            qs = qs.filter(
                article__research_fields__research_field_id__in=research_fields
            )
        statements_per_month = (
            qs.annotate(month=TruncMonth("article__reborn_date_published"))
            .values("month")
            .annotate(statement_count=Count("id"))
            .order_by("month")
            .distinct()
        )

        result = defaultdict(lambda: {"article_count": 0, "statement_count": 0})

        for entry in articles_per_month:
            result[entry["month"]]["article_count"] = entry["article_count"]

        for entry in statements_per_month:
            result[entry["month"]]["statement_count"] = entry["statement_count"]

        articles_statements_per_month = [
            {
                "month": month.strftime("%Y - %m"),
                "article_count": counts["article_count"],
                "statement_count": counts["statement_count"],
            }
            for month, counts in sorted(result.items())
        ]
        return articles_statements_per_month

    def get_software_library_with_usage(self, research_fields=None) -> any:
        qs = SoftwareLibraryModel.objects.exclude(label__isnull=True).exclude(
            label__exact=""
        )

        if research_fields:
            qs = qs.filter(
                software_methods__software_method__statement__article__research_fields__research_field_id__in=research_fields
            )

        qs = (
            qs.values("part_of__label", "label")
            .annotate(count=Count("id"))
            .order_by("-count")
            .distinct()
        )

        packages = defaultdict(list)

        for item in qs:
            label = item["part_of__label"]
            packages[label].append({"label": item["label"], "count": item["count"]})

        return packages

    def get_concepts_with_usage(self, research_fields=None):
        concepts_qs = ConceptModel.objects.annotate(
            usage_count=Count(
                "statements",
                filter=Q(
                    statements__article__research_fields__research_field_id__in=research_fields
                )
                if research_fields
                else Q(),
                distinct=True,
            )
        ).filter(usage_count__gt=0)

        concepts_qs = concepts_qs.values("label", "definition", "usage_count")

        concepts_results = []
        for concept in concepts_qs:
            label = concept["label"]
            acronym = None

            match = re.search(r"\(([^)]+)\)", label)
            if match:
                acronym = match.group(1).strip()
            else:
                words = label.split()
                if len(words) > 3:
                    acronym = " ".join(words[:3]) + "..."
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

        return concepts_results

    def get_components_with_usage(self, research_fields=None):
        usage_filter = (
            Q(
                statements__article__research_fields__research_field_id__in=research_fields
            )
            if research_fields
            else Q()
        )

        components_with_usage = (
            ComponentModel.objects.annotate(
                usage_count=Count(
                    "statements",
                    filter=usage_filter,
                    distinct=True,
                )
            )
            .filter(usage_count__gt=0)
            .prefetch_related("matrices", "object_of_interests", "properties", "units")
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
        return components_results

    def get_data_type_with_usage(self, research_fields=None):
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

        data_types = []

        for name, model in models:
            qs = model.objects.all()

            if research_fields:
                qs = qs.filter(
                    statement__article__research_fields__research_field_id__in=research_fields
                )

            count = qs.distinct().count()

            if count > 0:
                data_types.append({"label": name, "count": count})

        return sorted(data_types, key=lambda x: x["count"], reverse=True)

    def get_programming_language_with_usage(self, research_fields=None):
        qs = SoftwareModel.objects.all()

        if research_fields:
            qs = qs.filter(
                part_of_software__software_methods__software_method__statement__article__research_fields__research_field_id__in=research_fields
            )

        programming_languages = (
            qs.distinct().values("label").annotate(count=Count("id"))
        )

        total_count = sum(item["count"] for item in programming_languages) or 1
        for item in programming_languages:
            item["count"] = round((item["count"] / total_count) * 100)
        return programming_languages

    def get_research_insights(self) -> any:
        try:
            models_by_label = SoftwareModel.objects.values("label").annotate(
                model_count=Count("id")
            )
            libraries_by_label = SoftwareLibraryModel.objects.values(
                "part_of__label"
            ).annotate(library_count=Count("id"))
            return [
                {
                    "models_by_label": models_by_label,
                    "libraries_by_label": libraries_by_label,
                }
            ]

        except Exception as e:
            logger.error(f"Error in get_research_insights: {str(e)}")
            raise DatabaseError(f"Failed to find research insights: {str(e)}")
