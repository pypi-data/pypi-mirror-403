"""
Tests for RankQueryBuilder - the fluent query builder for V2 queries.
"""

import pytest

try:
    from shaped import (
        CandidateAttributes,
        CandidateIds,
        ColumnOrder,
        Diversity,
        Ensemble,
        Expression,
        Filter,
        Passthrough,
        Prebuilt,
        RankQueryBuilder,
        Similarity,
        TextSearch,
        Truncate,
    )
    from shaped.autogen.models.rank_query_config import RankQueryConfig

    HAS_V2 = True
except ImportError:
    HAS_V2 = False
    pytestmark = pytest.mark.skip("V2 SDK not available")


class TestRankQueryBuilder:
    """Test the RankQueryBuilder fluent API."""

    def test_basic_similarity_retrieve(self):
        """Test building a basic similarity retrieve query."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_embedding",
                    query_encoder={"user_id": "user123"},
                )
            )
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "retrieve" in query
            assert len(query["retrieve"]) == 1
            assert query["retrieve"][0]["type"] == "similarity"
            assert query["retrieve"][0]["embedding_ref"] == "item_embedding"

    def test_text_search_retrieve(self):
        """Test building a text search retrieve query."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                TextSearch(
                    input_text_query="laptop",
                    mode={"type": "vector", "text_embedding_ref": "text_emb"},
                )
            )
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "retrieve" in query
            assert len(query["retrieve"]) == 1
            assert query["retrieve"][0]["type"] == "text_search"
            assert query["retrieve"][0]["input_text_query"] == "laptop"

    def test_candidate_ids_retrieve(self):
        """Test building a candidate IDs retrieve query."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(CandidateIds(item_ids=["1", "2", "3"]))
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "retrieve" in query
            assert len(query["retrieve"]) == 1
            assert query["retrieve"][0]["type"] == "candidate_ids"
            assert query["retrieve"][0]["item_ids"] == ["1", "2", "3"]

    def test_column_order_retrieve(self):
        """Test building a column order retrieve query."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                ColumnOrder(
                    columns=[{"name": "popularity", "ascending": False}], limit=1000
                )
            )
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "retrieve" in query
            assert len(query["retrieve"]) == 1
            assert query["retrieve"][0]["type"] == "column_order"
            assert query["retrieve"][0]["limit"] == 1000

    def test_filter_prebuilt(self):
        """Test adding a prebuilt filter step."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_embedding",
                    query_encoder={"user_id": "user123"},
                )
            )
            .filter(
                Prebuilt(
                    "ref:data.filters:my_filter", input_user_id="$parameters.userId"
                )
            )
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "filter" in query
            assert len(query["filter"]) == 1
            assert query["filter"][0]["type"] == "prebuilt"
            assert query["filter"][0]["filter_ref"] == "ref:data.filters:my_filter"

    def test_filter_expression_step(self):
        """Test adding a filter step using Expression step object."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_embedding",
                    query_encoder={"user_id": "user123"},
                )
            )
            .filter(Expression("price > 100"))
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "filter" in query
            assert len(query["filter"]) == 1
            assert query["filter"][0]["type"] == "expression"
            assert query["filter"][0]["expression"] == "price > 100"

    def test_filter_truncate(self):
        """Test adding a truncate filter step."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_embedding",
                    query_encoder={"user_id": "user123"},
                )
            )
            .filter(Truncate(max_length=500))
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "filter" in query
            assert len(query["filter"]) == 1
            assert query["filter"][0]["type"] == "truncate"
            assert query["filter"][0]["max_length"] == 500

    def test_score_ensemble(self):
        """Test adding a score ensemble step."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_embedding",
                    query_encoder={"user_id": "user123"},
                )
            )
            .score(Ensemble("lightgbm", input_user_id="$parameters.userId"))
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "score" in query
            assert query["score"]["type"] == "score_ensemble"
            assert query["score"]["value_model"] == "lightgbm"

    def test_score_passthrough(self):
        """Test adding a passthrough score step."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_embedding",
                    query_encoder={"user_id": "user123"},
                )
            )
            .score(Passthrough())
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "score" in query
            assert query["score"]["type"] == "passthrough"

    def test_reorder_diversity(self):
        """Test adding a diversity reorder step."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_embedding",
                    query_encoder={"user_id": "user123"},
                )
            )
            .reorder(Diversity(diversity_attributes=["category"]))
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "reorder" in query
            assert len(query["reorder"]) == 1
            assert query["reorder"][0]["type"] == "diversity"
            assert query["reorder"][0]["diversity_attributes"] == ["category"]

    def test_multiple_retrieve_steps(self):
        """Test adding multiple retrieve steps."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                ColumnOrder(
                    columns=[{"name": "popularity", "ascending": False}], limit=1000
                ),
                TextSearch(
                    input_text_query="laptop",
                    mode={"type": "vector", "text_embedding_ref": "text_emb"},
                ),
            )
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "retrieve" in query
            assert len(query["retrieve"]) == 2
            assert query["retrieve"][0]["type"] == "column_order"
            assert query["retrieve"][1]["type"] == "text_search"

    def test_multiple_filter_steps(self):
        """Test adding multiple filter steps."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_embedding",
                    query_encoder={"user_id": "user123"},
                )
            )
            .filter(Expression("price > 100"), Truncate(max_length=500))
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "filter" in query
            assert len(query["filter"]) == 2
            assert query["filter"][0]["type"] == "expression"
            assert query["filter"][1]["type"] == "truncate"

    def test_complex_query(self):
        """Test building a complex multi-step query."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                ColumnOrder(
                    columns=[{"name": "popularity", "ascending": False}], limit=1000
                ),
                TextSearch(
                    input_text_query="laptop",
                    mode={"type": "vector", "text_embedding_ref": "text_emb"},
                ),
            )
            .filter(Expression("price < 1000"))
            .score(Ensemble("lightgbm", input_user_id="$parameters.userId"))
            .reorder(Diversity(diversity_attributes=["category"]))
            .limit(50)
            .columns(["item_id", "title", "price"])
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "retrieve" in query
            assert "filter" in query
            assert "score" in query
            assert "reorder" in query
            assert query["limit"] == 50
            assert query["columns"] == ["item_id", "title", "price"]

    def test_query_builder_chainability(self):
        """Test that query builder methods are chainable."""
        builder = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                Similarity(
                    embedding_ref="item_embedding",
                    query_encoder={"user_id": "user123"},
                )
            )
            .filter(Expression("price > 100"))
            .limit(10)
        )

        query = builder.build()
        assert isinstance(query, (RankQueryConfig, dict))

    def test_filter_retrieve_step(self):
        """Test building a filter retrieve step (filtering without ordering)."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Filter(where="category == 'electronics'", limit=500))
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "retrieve" in query
            assert len(query["retrieve"]) == 1
            assert query["retrieve"][0]["type"] == "filter"
            assert query["retrieve"][0]["where"] == "category == 'electronics'"
            assert query["retrieve"][0]["limit"] == 500

    def test_candidate_attributes_retrieve(self):
        """Test building a candidate attributes retrieve query."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                CandidateAttributes(
                    item_attributes=[
                        {"title": "Item 1", "category": "electronics"},
                        {"title": "Item 2", "category": "books"},
                    ]
                )
            )
            .build()
        )

        assert isinstance(query, (RankQueryConfig, dict))
        if isinstance(query, dict):
            assert "retrieve" in query
            assert len(query["retrieve"]) == 1
            assert query["retrieve"][0]["type"] == "candidate_attributes"
            assert len(query["retrieve"][0]["item_attributes"]) == 2
