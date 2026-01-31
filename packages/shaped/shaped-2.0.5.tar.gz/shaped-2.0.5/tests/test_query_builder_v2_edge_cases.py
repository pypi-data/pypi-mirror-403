"""
Edge case tests for RankQueryBuilder.

Tests query builder edge cases, invalid inputs, and boundary conditions.
"""

import pytest

try:
    from shaped import (
        Boosted,
        CandidateIds,
        ColumnOrder,
        Diversity,
        Ensemble,
        Expression,
        Prebuilt,
        RankQueryBuilder,
        Similarity,
        Truncate,
    )

    HAS_V2 = True
except ImportError:
    HAS_V2 = False
    pytestmark = pytest.mark.skip("V2 SDK not available")


class TestQueryBuilderEdgeCases:
    """Test query builder edge cases."""

    def test_build_empty_query(self):
        """Test building a query with no steps."""
        builder = RankQueryBuilder()
        query = builder.build()
        assert query is not None

    def test_build_with_only_from_entity(self):
        """Test building query with only entity type set."""
        query = RankQueryBuilder().from_entity("item").build()
        assert query is not None

    def test_invalid_entity_type(self):
        """Test that invalid entity types raise ValueError."""
        with pytest.raises(ValueError):
            RankQueryBuilder().from_entity("invalid_entity")

    def test_valid_entity_types(self):
        """Test that valid entity types are accepted."""
        for entity in ["item", "user", "item_attribute"]:
            query = RankQueryBuilder().from_entity(entity).build()
            assert query is not None

    def test_multiple_retrieve_steps(self):
        """Test adding multiple retrieve steps."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_emb",
                    query_encoder={"user_id": "user123"},
                ),
                ColumnOrder([{"name": "popularity", "ascending": False}]),
            )
            .build()
        )
        assert query is not None

    def test_multiple_filter_steps(self):
        """Test adding multiple filter steps."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_emb", query_encoder={"user_id": "user123"}
                )
            )
            .filter(Expression("price > 100"), Truncate(max_length=50))
            .build()
        )
        assert query is not None

    def test_multiple_reorder_steps(self):
        """Test adding multiple reorder steps."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_emb", query_encoder={"user_id": "user123"}
                )
            )
            .reorder(
                Diversity(diversity_attributes=["category"]),
                Boosted(
                    retriever={"type": "column_order", "columns": []}, strength=0.5
                ),
            )
            .build()
        )
        assert query is not None

    def test_retrieve_with_empty_item_ids(self):
        """Test CandidateIds with empty list."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(CandidateIds(item_ids=[]))
            .build()
        )
        assert query is not None

    def test_retrieve_with_single_item_id(self):
        """Test CandidateIds with single item."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(CandidateIds(item_ids=["item1"]))
            .build()
        )
        assert query is not None

    def test_filter_expression_with_empty_string(self):
        """Test filter with empty string expression."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_emb", query_encoder={"user_id": "user123"}
                )
            )
            .filter(Expression(""))
            .build()
        )
        assert query is not None

    def test_score_ensemble_with_empty_model(self):
        """Test score with empty model string."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_emb", query_encoder={"user_id": "user123"}
                )
            )
            .score(Ensemble(""))
            .build()
        )
        assert query is not None

    def test_reorder_diversity_without_attribute(self):
        """Test Diversity without attributes."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_emb", query_encoder={"user_id": "user123"}
                )
            )
            .reorder(Diversity())
            .build()
        )
        assert query is not None

    def test_query_builder_chaining(self):
        """Test that query builder methods are chainable."""
        builder = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_emb", query_encoder={"user_id": "user123"}
                )
            )
            .filter(Expression("price > 100"))
            .score(Ensemble("lightgbm"))
            .reorder(Diversity(diversity_attributes=["category"]))
        )

        query = builder.build()
        assert query is not None

    def test_query_builder_with_limit(self):
        """Test query builder with limit set."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_emb", query_encoder={"user_id": "user123"}
                )
            )
            .limit(50)
            .build()
        )
        assert query is not None

    def test_query_builder_with_columns(self):
        """Test query builder with columns set."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_emb", query_encoder={"user_id": "user123"}
                )
            )
            .columns(["item_id", "title", "price"])
            .build()
        )
        assert query is not None

    def test_query_builder_with_embeddings(self):
        """Test query builder with embeddings set."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_emb", query_encoder={"user_id": "user123"}
                )
            )
            .embeddings(["item_embedding", "text_embedding"])
            .build()
        )
        assert query is not None

    def test_complex_query_all_features(self):
        """Test building a complex query with all features."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_emb",
                    query_encoder={"user_id": "user123"},
                    limit=1000,
                ),
                ColumnOrder([{"name": "popularity", "ascending": False}], limit=500),
            )
            .filter(
                Expression("price > 100 AND price < 1000"), Truncate(max_length=200)
            )
            .score(Ensemble("lightgbm", input_user_id="$parameters.userId"))
            .reorder(Diversity(diversity_attributes=["category"], strength=0.7))
            .limit(50)
            .columns(["item_id", "title", "price", "category"])
            .embeddings(["item_embedding"])
            .build()
        )
        assert query is not None

    def test_invalid_retrieve_step_type(self):
        """Test that invalid retrieve step types raise ValueError."""
        with pytest.raises(ValueError, match="Invalid retrieve step type"):
            RankQueryBuilder().from_entity("item").retrieve({"type": "invalid_type"})

    def test_invalid_filter_step_type(self):
        """Test that invalid filter step types raise ValueError."""
        with pytest.raises(ValueError, match="Invalid filter step type"):
            RankQueryBuilder().from_entity("item").retrieve(
                Similarity(
                    embedding_ref="item_emb", query_encoder={"user_id": "user123"}
                )
            ).filter({"type": "invalid_type"})

    def test_invalid_score_config_type(self):
        """Test that invalid score config types raise ValueError."""
        with pytest.raises(ValueError, match="Invalid score config type"):
            RankQueryBuilder().from_entity("item").retrieve(
                Similarity(
                    embedding_ref="item_emb", query_encoder={"user_id": "user123"}
                )
            ).score({"type": "invalid_type"})

    def test_invalid_reorder_step_type(self):
        """Test that invalid reorder step types raise ValueError."""
        with pytest.raises(ValueError, match="Invalid reorder step type"):
            RankQueryBuilder().from_entity("item").retrieve(
                Similarity(
                    embedding_ref="item_emb", query_encoder={"user_id": "user123"}
                )
            ).reorder({"type": "invalid_type"})

    def test_filter_prebuilt(self):
        """Test prebuilt filter step."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_emb", query_encoder={"user_id": "user123"}
                )
            )
            .filter(Prebuilt("ref:data.filters:my_filter"))
            .build()
        )
        assert query is not None
        if isinstance(query, dict):
            assert "filter" in query
            assert query["filter"][0]["type"] == "prebuilt"
            assert query["filter"][0]["filter_ref"] == "ref:data.filters:my_filter"
