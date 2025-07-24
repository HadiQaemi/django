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
from django.db.models import Count
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

    def get_research_insights(self) -> any:
        """Perform search on authors by name."""
        # cache_key = f"get_research_insights"
        # cached_result = cache.get(cache_key)

        # if cached_result:
        #     return cached_result

        try:
            print("-------get_research_insights-------", __file__)
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
                    if len(words) > 1:
                        acronym = "".join(
                            word[0].upper() for word in words if word[0].isalpha()
                        )
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
                .values("label", "string_match", "usage_count")
            )
            components_results = []
            for component in components_with_usage:
                string_match = component["string_match"]
                components_results.append(
                    {
                        "text": string_match[0],
                        "definition": component["label"],
                        "value": component["usage_count"],
                    }
                )
            return {
                "statistics": {
                    "Articles": self.paper_repository.get_count_all(),
                    "Statements": self.statement_repository.get_count_all(),
                    "Journals": self.journal_repository.get_count_all(),
                    "Authors": self.author_repository.get_count_all(),
                    # "Research_fields": self.research_field_repository.get_count_all(),
                    # "num_concepts": self.concept_repository.get_count_all(),
                },
                "num_programming_languages": models_by_label,
                "num_packages": grouped_data,
                "data_types": data_types,
                "concepts": concepts_results,
                "components": components_results,
            }

        except Exception as e:
            logger.error(f"Error in search authers by name {str(e)}")
            raise SearchEngineError(
                f"Failed to perform search authers by name: {str(e)}"
            )
