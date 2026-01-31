"""
Comprehensive tests for RankQueryBuilder covering edge cases and advanced scenarios.
"""

import pytest

try:
    from shaped import (
        Boosted,
        CandidateAttributes,
        CandidateIds,
        ColumnOrder,
        Diversity,
        Ensemble,
        Exploration,
        Expression,
        Passthrough,
        Prebuilt,
        RankQueryBuilder,
        Similarity,
        TextSearch,
        Truncate,
    )

    HAS_V2 = True
except ImportError:
    HAS_V2 = False
    pytestmark = pytest.mark.skip("V2 SDK not available")


class TestQueryBuilderComprehensive:
    """Comprehensive tests for RankQueryBuilder."""

    def test_all_retrieve_step_types(self):
        """Test all retrieve step types can be used."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                ColumnOrder([{"name": "popularity", "ascending": False}]),
                TextSearch(
                    "laptop",
                    mode={"type": "vector", "text_embedding_ref": "emb"},
                ),
                Similarity("emb_ref", {"user_id": "123"}),
                CandidateIds(["id1", "id2", "id3"]),
                CandidateAttributes([{"title": "Item 1", "price": 100}]),
            )
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            assert len(query.get("retrieve", [])) == 5

    def test_all_filter_step_types(self):
        """Test all filter step types can be used."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .filter(
                Expression("price > 100"),
                Expression("category == 'electronics'"),
                Truncate(max_length=500),
                Prebuilt(
                    "ref:data.filters:my_filter", input_user_id="$parameters.userId"
                ),
            )
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            assert len(query.get("filter", [])) == 4

    def test_all_score_config_types(self):
        """Test all score config types can be used."""
        # Test Ensemble
        query1 = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .score(Ensemble("lightgbm", input_user_id="$parameters.userId"))
            .build()
        )
        assert query1 is not None

        # Test Passthrough
        query2 = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .score(Passthrough())
            .build()
        )
        assert query2 is not None

    def test_all_reorder_step_types(self):
        """Test all reorder step types can be used."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .reorder(
                Diversity(diversity_attributes=["category"]),
                Boosted(
                    retriever={"type": "column_order", "columns": []}, strength=0.5
                ),
                Exploration(
                    retriever={"type": "text_search", "input_text_query": "test"},
                    strength=0.3,
                ),
            )
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            assert len(query.get("reorder", [])) == 3

    def test_query_with_all_optional_fields(self):
        """Test query with all optional fields set."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .limit(100)
            .columns(["item_id", "title", "price", "category"])
            .embeddings(["item_embedding", "text_embedding"])
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            assert query.get("limit") == 100
            assert query.get("columns") == ["item_id", "title", "price", "category"]
            assert query.get("embeddings") == [
                "item_embedding",
                "text_embedding",
            ]

    def test_query_builder_fluent_chaining(self):
        """Test that all methods can be chained fluently."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .filter(Expression("price > 100"))
            .score(Ensemble("lightgbm"))
            .reorder(Diversity(diversity_attributes=["category"]))
            .limit(50)
            .columns(["item_id", "title"])
            .embeddings(["emb1"])
            .build()
        )

        assert query is not None

    def test_multiple_calls_to_same_method(self):
        """Test that calling the same method multiple times accumulates steps."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb1", {"user_id": "123"}))
            .retrieve(TextSearch("laptop", mode={"type": "lexical"}))
            .retrieve(CandidateIds(["id1", "id2"]))
            .filter(Expression("price > 100"))
            .filter(Truncate(max_length=500))
            .reorder(Diversity(diversity_attributes=["category"]))
            .reorder(Diversity(diversity_attributes=["brand"], strength=0.3))
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            assert len(query.get("retrieve", [])) == 3
            assert len(query.get("filter", [])) == 2
            assert len(query.get("reorder", [])) == 2

    def test_query_with_complex_nested_configs(self):
        """Test query with complex nested configurations."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                ColumnOrder(
                    [
                        {"name": "popularity", "ascending": False},
                        {"name": "price", "ascending": True},
                    ],
                    limit=1000,
                    where="category == 'electronics'",
                ),
                TextSearch(
                    "laptop",
                    mode={
                        "type": "vector",
                        "text_embedding_ref": "text_emb",
                        "top_k": 10,
                    },
                    limit=500,
                    where="in_stock == true",
                ),
            )
            .filter(
                Expression("price > 100 AND price < 1000"),
                Expression("rating >= 4.0"),
                Truncate(max_length=200),
            )
            .score(
                Ensemble(
                    "0.6 * lightgbm_v1 + 0.4 * xgboost_v2",
                    input_user_id="$parameters.userId",
                    input_user_features={"age": 25, "location": "US"},
                    input_interactions_item_ids=["item1", "item2"],
                )
            )
            .reorder(
                Diversity(
                    diversity_attributes=["category", "brand"],
                    strength=0.7,
                    diversity_lookback_window=50,
                    diversity_lookforward_window=50,
                    text_encoding_embedding_ref="text_emb",
                )
            )
            .limit(50)
            .columns(["item_id", "title", "price", "category", "rating"])
            .embeddings(["item_embedding", "text_embedding"])
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            assert query.get("limit") == 50
            assert len(query.get("retrieve", [])) == 2
            assert len(query.get("filter", [])) == 3
            assert query.get("score") is not None
            assert len(query.get("reorder", [])) == 1

    def test_query_serialization_to_dict(self):
        """Test that queries can be serialized to dictionaries."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .filter(Expression("price > 100"))
            .build()
        )

        if hasattr(query, "model_dump"):
            query_dict = query.model_dump(by_alias=True)
            assert isinstance(query_dict, dict)
            assert query_dict.get("type") == "rank"
            assert query_dict.get("from") == "item"
        elif isinstance(query, dict):
            assert query.get("type") == "rank"
            assert query.get("from") == "item"

    def test_query_with_minimal_config(self):
        """Test query with minimal required configuration."""
        query = RankQueryBuilder().from_entity("item").build()

        assert query is not None
        if isinstance(query, dict):
            assert query.get("type") == "rank"
            assert query.get("from") == "item"

    def test_query_with_only_retrieve(self):
        """Test query with only retrieve steps."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            assert "retrieve" in query
            assert "filter" not in query
            assert "score" not in query
            assert "reorder" not in query

    def test_query_with_only_filter(self):
        """Test query with only filter steps."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .filter(Expression("price > 100"))
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            assert "filter" in query
            assert "score" not in query
            assert "reorder" not in query

    def test_query_with_only_score(self):
        """Test query with only score config."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .score(Ensemble("lightgbm"))
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            assert "score" in query
            assert "reorder" not in query

    def test_query_with_only_reorder(self):
        """Test query with only reorder steps."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .reorder(Diversity(diversity_attributes=["category"]))
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            assert "reorder" in query

    def test_complex_expression_filter(self):
        """Test complex filter expressions."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .filter(
                Expression(
                    "price > 100 AND price < 1000 AND category == 'electronics' AND rating >= 4.0"
                )
            )
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            filter_steps = query.get("filter", [])
            assert len(filter_steps) == 1
            assert filter_steps[0].get("type") == "expression"

    def test_mixed_filter_types(self):
        """Test mixing different filter step types."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .filter(
                Expression("price > 100"),
                Expression("category == 'electronics'"),
                Expression("rating >= 4.0"),
                Truncate(max_length=500),
                Prebuilt("ref:data.filters:global_filter"),
            )
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            filter_steps = query.get("filter", [])
            assert len(filter_steps) == 5
            # Should have expression, truncate, and prebuilt types
            types = [step.get("type") for step in filter_steps]
            assert "expression" in types
            assert "truncate" in types
            assert "prebuilt" in types

    def test_query_with_different_entity_types(self):
        """Test queries with different entity types."""
        for entity in ["item", "user", "item_attribute"]:
            query = (
                RankQueryBuilder()
                .from_entity(entity)
                .retrieve(Similarity("emb", {"user_id": "123"}))
                .build()
            )
            assert query is not None
            if isinstance(query, dict):
                assert query.get("from") == entity

    def test_ensemble_with_all_parameters(self):
        """Test Ensemble score with all optional parameters."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .score(
                Ensemble(
                    "lightgbm",
                    input_user_id="$parameters.userId",
                    input_user_features={"age": 25, "location": "US"},
                    input_interactions_item_ids=["item1", "item2", "item3"],
                    name="my_score",
                )
            )
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            score = query.get("score", {})
            assert score.get("type") == "score_ensemble"
            assert score.get("value_model") == "lightgbm"

    def test_diversity_with_all_parameters(self):
        """Test Diversity reorder with all optional parameters."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(Similarity("emb", {"user_id": "123"}))
            .reorder(
                Diversity(
                    diversity_attributes=["category", "brand"],
                    strength=0.8,
                    diversity_lookback_window=50,
                    diversity_lookforward_window=50,
                    text_encoding_embedding_ref="text_emb",
                    name="my_diversity",
                )
            )
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            reorder_steps = query.get("reorder", [])
            assert len(reorder_steps) == 1
            assert reorder_steps[0].get("type") == "diversity"

    def test_column_order_with_multiple_columns(self):
        """Test ColumnOrder with multiple column orderings."""
        query = (
            RankQueryBuilder()
            .from_entity("item")
            .retrieve(
                ColumnOrder(
                    [
                        {"name": "popularity", "ascending": False},
                        {"name": "price", "ascending": True, "nulls_first": True},
                        {"name": "rating", "ascending": False},
                    ],
                    limit=1000,
                    where="category == 'electronics'",
                )
            )
            .build()
        )

        assert query is not None
        if isinstance(query, dict):
            retrieve_steps = query.get("retrieve", [])
            assert len(retrieve_steps) == 1
            assert retrieve_steps[0].get("type") == "column_order"
            assert len(retrieve_steps[0].get("columns", [])) == 3
