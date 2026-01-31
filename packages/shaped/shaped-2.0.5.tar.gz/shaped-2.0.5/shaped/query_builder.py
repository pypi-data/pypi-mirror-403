"""
Fluent query builder for constructing Shaped V2 declarative queries.
This module provides a fluent API for building RankQueryConfig objects
that leverage the declarative nature of Shaped's query language.
"""

from typing import Any, Dict, List, Optional, TypedDict, Union

from shaped.autogen.models.boosted_reorder_step import BoostedReorderStep
from shaped.autogen.models.candidate_attributes_retrieve_step import (
    CandidateAttributesRetrieveStep,
)
from shaped.autogen.models.candidate_ids_retrieve_step import CandidateIdsRetrieveStep
from shaped.autogen.models.column_order_retrieve_step import ColumnOrderRetrieveStep
from shaped.autogen.models.diversity_reorder_step import DiversityReorderStep
from shaped.autogen.models.exploration_reorder_step import ExplorationReorderStep
from shaped.autogen.models.expression_filter_step import ExpressionFilterStep
from shaped.autogen.models.filter_retrieve_step import FilterRetrieveStep
from shaped.autogen.models.passthrough_score import PassthroughScore
from shaped.autogen.models.prebuilt_filter_step import PrebuiltFilterStep

# Import all model classes
from shaped.autogen.models.rank_query_config import RankQueryConfig
from shaped.autogen.models.score_ensemble import ScoreEnsemble
from shaped.autogen.models.similarity_retrieve_step import SimilarityRetrieveStep
from shaped.autogen.models.text_search_retrieve_step import TextSearchRetrieveStep
from shaped.autogen.models.truncate_filter_step import TruncateFilterStep


# Type definition for column ordering
class ColumnOrdering(TypedDict, total=False):
    """Type definition for column ordering in retrieve steps."""

    name: str
    ascending: Optional[bool]
    nulls_first: Optional[bool]


# Factory functions for creating step objects (no "Step" suffix for cleaner names)


def Passthrough(
    name: Optional[str] = None,
) -> PassthroughScore:
    """
    Create a passthrough score.

    Args:
        name: Optional name for this score.

    Returns:
        PassthroughScore instance
    """
    return PassthroughScore(
        name=name,
    )


def ColumnOrder(
    columns: List[Union[Dict[str, Any], ColumnOrdering]],
    limit: int = 100,
    where: Optional[str] = None,
    name: Optional[str] = None,
) -> ColumnOrderRetrieveStep:
    """
    Create a column order retrieve step.

    Args:
        columns: List of column orderings (dicts with 'name' and optionally
            'ascending', 'nulls_first').
        limit: Maximum number of candidates to retrieve.
        where: Optional DuckDB filter expression.
        name: Optional name for this retrieve step.

    Returns:
        ColumnOrderRetrieveStep instance
    """
    return ColumnOrderRetrieveStep(
        columns=columns,
        limit=limit,
        where=where,
        name=name,
    )


def TextSearch(
    input_text_query: str,
    mode: Dict[str, Any],
    limit: int = 100,
    where: Optional[str] = None,
    name: Optional[str] = None,
) -> TextSearchRetrieveStep:
    """
    Create a text search retrieve step.

    Args:
        input_text_query: Text query parameter or value.
        mode: Search mode dict with 'type' ('lexical' or 'vector') and
            mode-specific fields.
        limit: Maximum number of candidates to retrieve.
        where: Optional DuckDB filter expression.
        name: Optional name for this retrieve step.

    Returns:
        TextSearchRetrieveStep instance
    """
    return TextSearchRetrieveStep(
        input_text_query=input_text_query,
        mode=mode,
        limit=limit,
        where=where,
        name=name,
    )


def Similarity(
    embedding_ref: str,
    query_encoder: Dict[str, Any],
    limit: int = 100,
    where: Optional[str] = None,
    name: Optional[str] = None,
) -> SimilarityRetrieveStep:
    """
    Create a similarity retrieve step.

    Args:
        embedding_ref: Name of the embedding to use.
        query_encoder: Encoder configuration dict.
        limit: Maximum number of candidates to retrieve.
        where: Optional DuckDB filter expression.
        name: Optional name for this retrieve step.

    Returns:
        SimilarityRetrieveStep instance
    """
    return SimilarityRetrieveStep(
        embedding_ref=embedding_ref,
        query_encoder=query_encoder,
        limit=limit,
        where=where,
        name=name,
    )


def CandidateIds(
    item_ids: List[str],
    limit: Optional[int] = None,
    name: Optional[str] = None,
) -> CandidateIdsRetrieveStep:
    """
    Create a candidate IDs retrieve step.

    Args:
        item_ids: List of entity IDs to retrieve.
        limit: Maximum number of IDs to retrieve (defaults to length of item_ids).
        name: Optional name for this retrieve step.

    Returns:
        CandidateIdsRetrieveStep instance
    """
    return CandidateIdsRetrieveStep(
        item_ids=item_ids,
        limit=limit,
        name=name,
    )


def CandidateAttributes(
    item_attributes: List[Dict[str, Any]],
    limit: Optional[int] = None,
    name: Optional[str] = None,
) -> CandidateAttributesRetrieveStep:
    """
    Create a candidate attributes retrieve step.

    Args:
        item_attributes: List of item attribute dictionaries.
        limit: Maximum number of items to retrieve.
        name: Optional name for this retrieve step.

    Returns:
        CandidateAttributesRetrieveStep instance
    """
    return CandidateAttributesRetrieveStep(
        item_attributes=item_attributes,
        limit=limit,
        name=name,
    )


def Filter(
    where: Optional[str] = None,
    limit: int = 100,
    name: Optional[str] = None,
) -> FilterRetrieveStep:
    """
    Create a filter retrieve step (filtering without ordering).

    Args:
        where: Optional DuckDB filter expression.
        limit: Maximum number of candidates to retrieve.
        name: Optional name for this retrieve step.

    Returns:
        FilterRetrieveStep instance
    """
    return FilterRetrieveStep(
        where=where,
        limit=limit,
        name=name,
    )


def Expression(
    expression: str,
    name: Optional[str] = None,
) -> ExpressionFilterStep:
    """
    Create an expression filter step.

    Args:
        expression: DuckDB filter expression.
        name: Optional name for this filter step.

    Returns:
        ExpressionFilterStep instance
    """
    return ExpressionFilterStep(
        expression=expression,
        name=name,
    )


def Truncate(
    max_length: int = 500,
    name: Optional[str] = None,
) -> TruncateFilterStep:
    """
    Create a truncate filter step.

    Args:
        max_length: Maximum number of items to keep after truncation.
        name: Optional name for this filter step.

    Returns:
        TruncateFilterStep instance
    """
    return TruncateFilterStep(
        max_length=max_length,
        name=name,
    )


def Prebuilt(
    filter_ref: str,
    input_user_id: Optional[str] = None,
    name: Optional[str] = None,
) -> PrebuiltFilterStep:
    """
    Create a prebuilt filter step.

    Args:
        filter_ref: Reference to a prebuilt filter (e.g., ref:data.filters:name).
        input_user_id: User ID for personal filters. Required for personal,
            omitted for global filters.
        name: Optional name for this filter step.

    Returns:
        PrebuiltFilterStep instance
    """
    return PrebuiltFilterStep(
        filter_ref=filter_ref,
        input_user_id=input_user_id,
        name=name,
    )


def ensemble(
    value_model: str,
    input_user_id: Optional[str] = None,
    input_user_features: Optional[Dict[str, Any]] = None,
    input_interactions_item_ids: Optional[List[str]] = None,
    name: Optional[str] = None,
    **kwargs: Any,
) -> ScoreEnsemble:
    """
    Create a score ensemble step.

    Args:
        value_model: Name of the value model to use for scoring.
        input_user_id: Optional user ID for personalization.
        input_user_features: Optional dictionary of user features.
        input_interactions_item_ids: Optional list of item IDs from user interactions.
        name: Optional name for this score step.
        **kwargs: Additional keyword arguments for backward compatibility.

    Returns:
        ScoreEnsemble instance

    Example:
        >>> ensemble("lightgbm", input_user_id="user123")
        >>> ensemble("xgboost", name="xgboost_scorer")
    """
    # Handle the case where parameters are passed in the options dictionary
    if not input_user_id and "input_user_id" in kwargs:
        input_user_id = kwargs.pop("input_user_id")
    if not input_user_features and "input_user_features" in kwargs:
        input_user_features = kwargs.pop("input_user_features")
    if not input_interactions_item_ids and "input_interactions_item_ids" in kwargs:
        input_interactions_item_ids = kwargs.pop("input_interactions_item_ids")
    if not name and "name" in kwargs:
        name = kwargs.pop("name")

    # Create the config dictionary
    config: Dict[str, Any] = {
        "value_model": value_model,
    }

    # Add optional parameters if provided
    if input_user_id is not None:
        config["input_user_id"] = input_user_id
    if input_user_features is not None:
        config["input_user_features"] = input_user_features
    if input_interactions_item_ids is not None:
        config["input_interactions_item_ids"] = input_interactions_item_ids
    if name is not None:
        config["name"] = name

    # Add any additional parameters from kwargs (for backward compatibility)
    config.update(kwargs)

    return ScoreEnsemble(**config)


def passthrough(name: Optional[str] = None) -> PassthroughScore:
    """
    Create a passthrough score step that doesn't modify the scores.

    Args:
        name: Optional name for this score step.

    Returns:
        PassthroughScore instance

    Example:
        >>> passthrough()
        >>> passthrough(name="noop_scorer")
    """
    config: Dict[str, Any] = {
        "type": "passthrough",
    }
    if name is not None:
        config["name"] = name
    return PassthroughScore(**config)


def Boosted(
    retriever: Dict[str, Any],
    strength: float = 0.5,
    name: Optional[str] = None,
) -> BoostedReorderStep:
    """
    Create a boosted reorder step.

    Args:
        retriever: Retrieve step to use as source for boosting.
        strength: Boost strength (0.0-1.0).
        name: Optional name for this reorder step.

    Returns:
        BoostedReorderStep instance
    """
    return BoostedReorderStep(
        retriever=retriever,
        strength=strength,
        name=name,
    )


def Exploration(
    retriever: Dict[str, Any],
    strength: float = 0.5,
    name: Optional[str] = None,
) -> ExplorationReorderStep:
    """
    Create an exploration reorder step.

    Args:
        retriever: Retrieve step to use as source for exploration.
        strength: Exploration strength (0.0-1.0).
        name: Optional name for this reorder step.

    Returns:
        ExplorationReorderStep instance
    """
    return ExplorationReorderStep(
        retriever=retriever,
        strength=strength,
        name=name,
    )


def Diversity(
    diversity_attributes: Optional[Union[List[str], str]] = None,
    limit: int = 100,
    name: Optional[str] = None,
    strength: float = 0.5,
    diversity_lookback_window: int = 30,
    diversity_lookforward_window: int = 30,
    text_encoding_embedding_ref: Optional[str] = None,
    **kwargs,
) -> DiversityReorderStep:
    """
    Create a diversity reorder step.

    Args:
        diversity_attributes: List of attribute names to use for diversification.
        limit: Maximum number of items to return after diversification.
        name: Optional name for this reorder step.
        strength: Strength of the diversity effect (0.0 to 1.0).
        diversity_lookback_window: Number of previous items to consider for diversity.
        diversity_lookforward_window: Number of next items to consider for diversity.
        text_encoding_embedding_ref: Reference to text encoding embedding.
        **kwargs: Additional keyword arguments for backward compatibility.

    Returns:
        DiversityReorderStep instance
    """
    # Handle the case where diversity_attributes is passed as a single string
    if isinstance(diversity_attributes, str):
        diversity_attributes = [diversity_attributes]

    # Handle the case where diversity_attributes is not provided but is in kwargs
    if diversity_attributes is None:
        if "diversity_attribute" in kwargs:
            diversity_attributes = [kwargs.pop("diversity_attribute")]
        elif "diversityAttributes" in kwargs:
            diversity_attributes = kwargs.pop("diversityAttributes")
            if isinstance(diversity_attributes, str):
                diversity_attributes = [diversity_attributes]

    # Create the config dictionary
    config: Dict[str, Any] = {
        "diversity_attributes": diversity_attributes or [],
        "limit": limit,
        "strength": strength,
        "diversity_lookback_window": diversity_lookback_window,
        "diversity_lookforward_window": diversity_lookforward_window,
    }

    # Add text_encoding_embedding_ref if provided
    if text_encoding_embedding_ref is not None:
        config["text_encoding_embedding_ref"] = text_encoding_embedding_ref

    # Add name if provided
    if name is not None:
        config["name"] = name

    # Add any additional parameters from kwargs (for backward compatibility)
    config.update(kwargs)

    return DiversityReorderStep(**config)


def _get_step_type(step: Any) -> Optional[str]:
    """Extract step type from step object or dict."""
    if isinstance(step, dict):
        return step.get("type")
    if hasattr(step, "type"):
        return getattr(step, "type")
    return None


class RankQueryBuilder:
    """
    Fluent builder for constructing RankQueryConfig queries.

    Example:
        from shaped import RankQueryBuilder, ColumnOrder, TextSearch, Filter, Expression, Ensemble, Diversity

        query = (RankQueryBuilder()
            .from_entity('item')
            .retrieve(
                ColumnOrder([{'name': 'popularity', 'ascending': False}], limit=1000),
                TextSearch('laptop', mode={'type': 'vector', 'text_embedding_ref': 'text_emb'}),
                Filter(where='category == "electronics"', limit=500)
            )
            .filter(Expression('price < 1000'))
            .score(Ensemble('lightgbm', input_user_id='$parameters.userId'))
            .reorder(Diversity(diversity_attributes=['category']))
            .limit(50)
            .columns(['item_id', 'title', 'price'])
            .build())
    """

    def __init__(self):
        self._retrieve_steps: List[Union[Dict[str, Any], Any]] = []
        self._filter_steps: List[Union[Dict[str, Any], Any]] = []
        self._score_config: Optional[Union[Dict[str, Any], Any]] = None
        self._reorder_steps: List[Union[Dict[str, Any], Any]] = []
        self._from_entity: Optional[str] = None
        self._limit: Optional[int] = None
        self._columns: Optional[List[str]] = None
        self._embeddings: Optional[List[str]] = None

    def from_entity(self, entity: str) -> "RankQueryBuilder":
        """
        Set the entity type to rank (item or user).

        Args:
            entity: Entity type, either 'item', 'user', or 'item_attribute'.

        Returns:
            Self for method chaining.
        """
        if entity not in ["item", "user", "item_attribute"]:
            raise ValueError(
                f"Entity must be 'item', 'user', or 'item_attribute', got '{entity}'"
            )
        self._from_entity = entity
        return self

    def retrieve(
        self,
        *steps: Union[
            ColumnOrderRetrieveStep,
            TextSearchRetrieveStep,
            SimilarityRetrieveStep,
            FilterRetrieveStep,
            CandidateIdsRetrieveStep,
            CandidateAttributesRetrieveStep,
            Dict[str, Any],
        ],
    ) -> "RankQueryBuilder":
        """
        Add one or more retrieve steps.

        Args:
            *steps: Retrieve step objects (ColumnOrder, TextSearch, Similarity,
                Filter, CandidateIds, CandidateAttributes) or dicts.

        Returns:
            Self for method chaining.
        """
        valid_types = {
            "column_order",
            "text_search",
            "similarity",
            "filter",
            "candidate_ids",
            "candidate_attributes",
        }
        for step in steps:
            step_type = _get_step_type(step)
            if step_type is None:
                raise ValueError(
                    f"Invalid retrieve step: missing 'type' field. "
                    f"Expected one of: {', '.join(sorted(valid_types))}"
                )
            if step_type not in valid_types:
                raise ValueError(
                    f"Invalid retrieve step type: '{step_type}'. "
                    f"Expected one of: {', '.join(sorted(valid_types))}"
                )
            self._retrieve_steps.append(step)
        return self

    def filter(
        self,
        *steps: Union[
            ExpressionFilterStep,
            TruncateFilterStep,
            PrebuiltFilterStep,
            Dict[str, Any],
        ],
    ) -> "RankQueryBuilder":
        """
        Add one or more filter steps.

        Args:
            *steps: Filter step objects (Expression, Truncate, Prebuilt) or dicts.

        Returns:
            Self for method chaining.

        Examples:
            .filter(Expression('price < 1000'))
            .filter(Truncate(max_length=100))
            .filter(Prebuilt('ref:data.filters:my_filter', input_user_id='$parameters.userId'))
            .filter(Expression('price > 100'), Truncate(max_length=500), Prebuilt('ref:data.filters:global'))
        """
        valid_types = {"expression", "truncate", "prebuilt"}

        for step in steps:
            step_type = _get_step_type(step)
            if step_type is None:
                raise ValueError(
                    f"Invalid filter step: missing 'type' field. "
                    f"Expected one of: {', '.join(sorted(valid_types))}"
                )
            if step_type not in valid_types:
                raise ValueError(
                    f"Invalid filter step type: '{step_type}'. "
                    f"Expected one of: {', '.join(sorted(valid_types))}"
                )
            self._filter_steps.append(step)
        return self

    def score(
        self,
        config: Union[ScoreEnsemble, PassthroughScore, Dict[str, Any]],
    ) -> "RankQueryBuilder":
        """
        Set the score configuration.

        Args:
            config: Score configuration (Ensemble, Passthrough) or dict.

        Returns:
            Self for method chaining.
        """
        valid_types = {"score_ensemble", "passthrough"}
        step_type = _get_step_type(config)
        if step_type is None:
            raise ValueError(
                f"Invalid score config: missing 'type' field. "
                f"Expected one of: {', '.join(sorted(valid_types))}"
            )
        if step_type not in valid_types:
            raise ValueError(
                f"Invalid score config type: '{step_type}'. "
                f"Expected one of: {', '.join(sorted(valid_types))}"
            )
        self._score_config = config
        return self

    def reorder(
        self,
        *steps: Union[
            DiversityReorderStep,
            BoostedReorderStep,
            ExplorationReorderStep,
            Dict[str, Any],
        ],
    ) -> "RankQueryBuilder":
        """
        Add one or more reorder steps.

        Args:
            *steps: Reorder step objects (Diversity, Boosted, Exploration) or dicts.

        Returns:
            Self for method chaining.
        """
        valid_types = {"diversity", "boosted", "exploration"}
        for step in steps:
            step_type = _get_step_type(step)
            if step_type is None:
                raise ValueError(
                    f"Invalid reorder step: missing 'type' field. "
                    f"Expected one of: {', '.join(sorted(valid_types))}"
                )
            if step_type not in valid_types:
                raise ValueError(
                    f"Invalid reorder step type: '{step_type}'. "
                    f"Expected one of: {', '.join(sorted(valid_types))}"
                )
            self._reorder_steps.append(step)
        return self

    def limit(self, limit: int) -> "RankQueryBuilder":
        """
        Set the maximum number of entities to return.

        Args:
            limit: Maximum number of entities.

        Returns:
            Self for method chaining.
        """
        self._limit = limit
        return self

    def columns(self, columns: List[str]) -> "RankQueryBuilder":
        """
        Set the list of column names to include in results.

        Args:
            columns: List of column names.

        Returns:
            Self for method chaining.
        """
        self._columns = columns
        return self

    def embeddings(self, embeddings: List[str]) -> "RankQueryBuilder":
        """
        Set the list of embedding names to include in results.

        Args:
            embeddings: List of embedding names.

        Returns:
            Self for method chaining.
        """
        self._embeddings = embeddings
        return self

    def build(self) -> Union[RankQueryConfig, Dict[str, Any]]:
        """
        Build the RankQueryConfig object.

        Returns:
            RankQueryConfig instance if models are available, otherwise a dict.
        """
        config: Dict[str, Any] = {"type": "rank"}

        if self._from_entity is not None:
            config["from"] = self._from_entity

        if self._retrieve_steps:
            # Convert steps to dicts if they're model instances
            retrieve_list = []
            for step in self._retrieve_steps:
                if isinstance(step, dict):
                    retrieve_list.append(step)
                elif hasattr(step, "model_dump"):
                    retrieve_list.append(step.model_dump(by_alias=True))
                else:
                    retrieve_list.append(step)
            config["retrieve"] = retrieve_list

        if self._filter_steps:
            filter_list = []
            for step in self._filter_steps:
                if isinstance(step, dict):
                    filter_list.append(step)
                elif hasattr(step, "model_dump"):
                    filter_list.append(step.model_dump(by_alias=True))
                else:
                    filter_list.append(step)
            config["filter"] = filter_list

        if self._score_config is not None:
            if isinstance(self._score_config, dict):
                config["score"] = self._score_config
            elif hasattr(self._score_config, "model_dump"):
                config["score"] = self._score_config.model_dump(by_alias=True)
            else:
                config["score"] = self._score_config

        if self._reorder_steps:
            reorder_list = []
            for step in self._reorder_steps:
                if isinstance(step, dict):
                    reorder_list.append(step)
                elif hasattr(step, "model_dump"):
                    reorder_list.append(step.model_dump(by_alias=True))
                else:
                    reorder_list.append(step)
            config["reorder"] = reorder_list

        if self._limit is not None:
            config["limit"] = self._limit

        if self._columns is not None:
            config["columns"] = self._columns

        if self._embeddings is not None:
            config["embeddings"] = self._embeddings

        # If models are available, convert to proper model instance.
        if RankQueryConfig is not None:
            try:
                return RankQueryConfig(**config)
            except Exception:
                # Fallback to dict if conversion fails
                return config

        return config
