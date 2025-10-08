from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import logging

from core.infrastructure.search.semantic_engine import SemanticSearchEngine
from core.infrastructure.search.keyword_engine import KeywordSearchEngine

logger = logging.getLogger(__name__)


class HybridSearchEngine:

    def __init__(
        self,
        semantic_engine: SemanticSearchEngine,
        keyword_engine: Union[KeywordSearchEngine, bool] = False,
        weight_semantic: float = 0.7,
        weight_keyword: float = 0.3,
    ):
        self.semantic_engine = semantic_engine
        self.keyword_engine = keyword_engine
        self.weight_semantic = weight_semantic
        self.weight_keyword = weight_keyword

        # Validate weights
        if not np.isclose(self.weight_semantic + self.weight_keyword, 1.0):
            logger.warning(
                f"Weights for semantic ({weight_semantic}) and keyword ({weight_keyword}) "
                f"do not sum to 1. Normalizing weights."
            )
            total = self.weight_semantic + self.weight_keyword
            self.weight_semantic /= total
            self.weight_keyword /= total

    def _normalize_scores(self, scores: List[float]) -> List[float]:
        if not scores:
            return []

        min_score = min(scores)
        max_score = max(scores)

        if min_score == max_score:
            return [0.5] * len(scores)

        return [(score - min_score) / (max_score - min_score) for score in scores]

    def _merge_results(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        id_field: str,
        threshold: float,
        name_field: str,
        keyword_engine: bool = False,
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        results_map = {}

        for result in semantic_results:
            item_id = result.get("id") or result.get("item", {}).get(id_field)

            if item_id:
                results_map[item_id] = {
                    "item": result.get("item", {}),
                    "semantic_score": result.get("score", 0.0),
                    "keyword_score": 0.0,
                }

        if keyword_engine and keyword_results:
            for result in keyword_results:
                item_id = result.get("id") or result.get("data", {}).get(id_field)

                if item_id:
                    if item_id in results_map:
                        results_map[item_id]["keyword_score"] = result.get("score", 0.0)
                    else:
                        results_map[item_id] = {
                            "item": result.get("data", {}),
                            "semantic_score": 0.0,
                            "keyword_score": result.get("score", 0.0),
                        }

        semantic_scores = [result["semantic_score"] for result in results_map.values()]
        normalized_semantic_scores = self._normalize_scores(semantic_scores)

        if keyword_engine and keyword_results:
            keyword_scores = [
                result["keyword_score"] for result in results_map.values()
            ]
            normalized_keyword_scores = self._normalize_scores(keyword_scores)

        final_results = []
        final_ids = []

        for i, (item_id, result) in enumerate(results_map.items()):
            if keyword_engine and keyword_results:
                final_score = (
                    self.weight_semantic * normalized_semantic_scores[i]
                    + self.weight_keyword * normalized_keyword_scores[i]
                )
            else:
                final_score = self.weight_semantic * normalized_semantic_scores[i]

            if final_score > threshold:
                item = result["item"]
                if name_field in item and len(item[name_field]) > 50:
                    if keyword_engine and keyword_results:
                        final_results.append(
                            {
                                "item": item,
                                "final_score": final_score,
                                "semantic_score": result["semantic_score"],
                                "keyword_score": result["keyword_score"],
                            }
                        )
                    else:
                        final_results.append(
                            {
                                "item": item,
                                "final_score": final_score,
                                "semantic_score": result["semantic_score"],
                                "keyword_score": 0.0,
                            }
                        )

                    final_ids.append(item_id)

        final_results.sort(key=lambda x: x["final_score"], reverse=True)

        return final_results, final_ids

    def search_articles(
        self, query: str, k: int = 5
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        try:
            semantic_results = self.semantic_engine.search_articles(query, k)

            if self.keyword_engine and isinstance(
                self.keyword_engine, KeywordSearchEngine
            ):
                keyword_results = self.keyword_engine.search_articles(query, k)
                return self._merge_results(
                    semantic_results, keyword_results, "article_id", 0.6, "title", True
                )
            else:
                return self._merge_results(
                    semantic_results, [], "article_id", 0.6, "title", False
                )

        except Exception as e:
            logger.error(f"Error in search_articles: {str(e)}")
            raise

    def search_statements(
        self, query: str, k: int = 5
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        try:
            semantic_results = self.semantic_engine.search_statements(query, k)

            if self.keyword_engine and isinstance(
                self.keyword_engine, KeywordSearchEngine
            ):
                keyword_results = self.keyword_engine.search_statements(query, k)
                return self._merge_results(
                    semantic_results, keyword_results, "statement_id", 0.3, "text", True
                )
            else:
                return self._merge_results(
                    semantic_results, [], "statement_id", 0.3, "text", False
                )

        except Exception as e:
            logger.error(f"Error in search_statements: {str(e)}")
            raise
