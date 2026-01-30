"""Tests for models.py - model registry and configuration."""

import pytest

from claude_lfr_mcp.models import (
    DEFAULT_MODEL,
    MODEL_REGISTRY,
    ModelConfig,
    get_collection_name_for_model,
    get_model_config,
    list_models,
)


class TestModelConfig:
    """Tests for ModelConfig dataclass."""

    def test_model_config_fields(self):
        """Test that ModelConfig has all required fields."""
        config = ModelConfig(
            name="test/model",
            dimension=384,
            query_prefix="query: ",
            doc_prefix="doc: ",
            short_name="test-model",
            description="A test model",
        )

        assert config.name == "test/model"
        assert config.dimension == 384
        assert config.query_prefix == "query: "
        assert config.doc_prefix == "doc: "
        assert config.short_name == "test-model"
        assert config.description == "A test model"
        assert config.trust_remote_code is False

    def test_model_config_trust_remote_code(self):
        """Test that trust_remote_code can be set."""
        config = ModelConfig(
            name="test/model",
            dimension=768,
            query_prefix="",
            doc_prefix="",
            short_name="test-model",
            description="A test model",
            trust_remote_code=True,
        )
        assert config.trust_remote_code is True


class TestModelRegistry:
    """Tests for MODEL_REGISTRY."""

    def test_registry_not_empty(self):
        """Test that model registry is not empty."""
        assert len(MODEL_REGISTRY) > 0

    def test_all_models_have_valid_config(self):
        """Test that all models in registry have valid configuration."""
        for short_name, config in MODEL_REGISTRY.items():
            assert isinstance(config, ModelConfig)
            assert config.short_name == short_name
            assert config.dimension > 0
            assert config.name  # Non-empty HuggingFace name
            assert config.description  # Non-empty description

    def test_default_model_exists(self):
        """Test that DEFAULT_MODEL is in registry."""
        assert DEFAULT_MODEL in MODEL_REGISTRY

    @pytest.mark.parametrize(
        "model_name,expected_dim",
        [
            ("all-MiniLM-L6-v2", 384),
            ("bge-small-en-v1.5", 384),
            ("bge-base-en-v1.5", 768),
            ("nomic-embed-text-v1.5", 768),
            ("snowflake-arctic-embed-xs", 384),
            ("snowflake-arctic-embed-s", 384),
        ],
    )
    def test_model_dimensions(self, model_name, expected_dim):
        """Test that each model has the correct dimension."""
        config = MODEL_REGISTRY[model_name]
        assert config.dimension == expected_dim

    def test_bge_models_have_query_prefix(self):
        """Test that BGE models use the query prefix."""
        for name in ["bge-small-en-v1.5", "bge-base-en-v1.5"]:
            config = MODEL_REGISTRY[name]
            assert config.query_prefix == "query: "
            assert config.doc_prefix == ""

    def test_nomic_model_has_search_prefixes(self):
        """Test that nomic model uses search prefixes."""
        config = MODEL_REGISTRY["nomic-embed-text-v1.5"]
        assert config.query_prefix == "search_query: "
        assert config.doc_prefix == "search_document: "
        assert config.trust_remote_code is True


class TestGetModelConfig:
    """Tests for get_model_config function."""

    def test_get_valid_model(self):
        """Test getting a valid model configuration."""
        config = get_model_config("bge-base-en-v1.5")
        assert config.short_name == "bge-base-en-v1.5"
        assert config.dimension == 768

    def test_get_all_models(self):
        """Test that all registered models can be retrieved."""
        for model_name in MODEL_REGISTRY:
            config = get_model_config(model_name)
            assert config.short_name == model_name

    def test_get_unknown_model_raises(self):
        """Test that unknown model raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_model_config("nonexistent-model")

        error_msg = str(exc_info.value)
        assert "Unknown model: nonexistent-model" in error_msg
        assert "Available models:" in error_msg

    def test_error_message_lists_available_models(self):
        """Test that error message includes available models."""
        with pytest.raises(ValueError) as exc_info:
            get_model_config("fake-model")

        error_msg = str(exc_info.value)
        # Check that some known models are listed
        assert "bge-base-en-v1.5" in error_msg
        assert "all-MiniLM-L6-v2" in error_msg


class TestGetCollectionNameForModel:
    """Tests for get_collection_name_for_model function."""

    def test_basic_collection_name(self):
        """Test basic collection name generation."""
        name = get_collection_name_for_model("bge-base-en-v1.5")
        assert name == "code_bge_base_en_v15"

    def test_override_takes_precedence(self):
        """Test that override parameter takes precedence."""
        name = get_collection_name_for_model("bge-base-en-v1.5", override="custom_name")
        assert name == "custom_name"

    def test_override_with_none(self):
        """Test that None override uses auto-generated name."""
        name = get_collection_name_for_model("bge-base-en-v1.5", override=None)
        assert name == "code_bge_base_en_v15"

    @pytest.mark.parametrize(
        "model_name,expected_collection",
        [
            ("all-MiniLM-L6-v2", "code_all_MiniLM_L6_v2"),
            ("bge-small-en-v1.5", "code_bge_small_en_v15"),
            ("snowflake-arctic-embed-xs", "code_snowflake_arctic_embed_xs"),
            ("nomic-embed-text-v1.5", "code_nomic_embed_text_v15"),
        ],
    )
    def test_collection_names_for_all_models(self, model_name, expected_collection):
        """Test collection name generation for all models."""
        name = get_collection_name_for_model(model_name)
        assert name == expected_collection


class TestListModels:
    """Tests for list_models function."""

    def test_returns_string(self):
        """Test that list_models returns a string."""
        result = list_models()
        assert isinstance(result, str)

    def test_contains_header(self):
        """Test that output contains header."""
        result = list_models()
        assert "Available embedding models" in result

    def test_contains_all_models(self):
        """Test that output contains all registered models."""
        result = list_models()
        for model_name in MODEL_REGISTRY:
            assert model_name in result

    def test_shows_dimensions(self):
        """Test that output shows dimensions."""
        result = list_models()
        assert "384" in result
        assert "768" in result

    def test_marks_default_model(self):
        """Test that default model is marked."""
        result = list_models()
        assert "(default)" in result
        # Default marker should be on the correct line
        lines = result.split("\n")
        default_line = [l for l in lines if "(default)" in l][0]
        assert DEFAULT_MODEL in default_line

    def test_includes_descriptions(self):
        """Test that descriptions are included."""
        result = list_models()
        for config in MODEL_REGISTRY.values():
            # At least part of description should be present
            assert config.description[:20] in result
