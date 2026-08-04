"""Tests for the Day 9 embeddings module."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.llm.embeddings import serialize_for_embedding, embed_text


# ---------------------------------------------------------------------------
# Serializer
# ---------------------------------------------------------------------------

def test_serializer_determinism() -> None:
    components = {"street_line": "3400 W Plano Pkwy", "city": "Plano", "state": "TX", "postal_code": "75075", "country": "US"}
    t1 = serialize_for_embedding("3400 W Plano Pkwy, Plano, TX 75075", components)
    t2 = serialize_for_embedding("3400 W Plano Pkwy, Plano, TX 75075", components)
    assert t1 == t2


def test_serializer_field_order_stable() -> None:
    full = {"street_line": "A", "city": "B", "state": "C", "postal_code": "D", "country": "E"}
    text = serialize_for_embedding("raw", full)
    assert "A" in text and "B" in text and "C" in text


def test_serializer_handles_missing_fields() -> None:
    components = {"street_line": None, "city": "Plano", "state": None, "postal_code": None, "country": None}
    text = serialize_for_embedding("raw", components)
    assert "Plano" in text
    assert "None" not in text  # None fields become empty string, not the literal "None"


# ---------------------------------------------------------------------------
# Local model embedding
# ---------------------------------------------------------------------------

def test_local_embedding_returns_correct_dimension() -> None:
    """Requires sentence-transformers to be installed; mocked to avoid download in CI."""
    mock_model = MagicMock()
    import numpy as np
    mock_model.encode.return_value = np.zeros(384)
    with patch("app.llm.embeddings._local_model", mock_model):
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.embeddings_provider = "local"
            mock_settings.return_value.embeddings_api_base_url = ""
            mock_settings.return_value.embeddings_api_key = ""
            mock_settings.return_value.embeddings_model = "all-MiniLM-L6-v2"
            mock_settings.return_value.embeddings_dimension = 384
            mock_settings.return_value.embeddings_fallback_enabled = True
            result = embed_text("3400 W Plano Pkwy", {"city": "Plano"})
    assert len(result) == 384
    assert all(isinstance(v, float) for v in result)


# ---------------------------------------------------------------------------
# Provider fallback
# ---------------------------------------------------------------------------

def test_api_failure_falls_back_to_local() -> None:
    """When company API raises, local model should be used if fallback enabled."""
    mock_model = MagicMock()
    import numpy as np
    mock_model.encode.return_value = np.zeros(384)

    with patch("app.llm.embeddings._local_model", mock_model):
        with patch("app.llm.embeddings._embed_via_company_api", side_effect=Exception("timeout")):
            with patch("app.core.config.get_settings") as mock_settings:
                mock_settings.return_value.embeddings_provider = "company_api"
                mock_settings.return_value.embeddings_api_base_url = "https://fake.api"
                mock_settings.return_value.embeddings_api_key = "key"
                mock_settings.return_value.embeddings_model = "model"
                mock_settings.return_value.embeddings_dimension = 384
                mock_settings.return_value.embeddings_fallback_enabled = True
                result = embed_text("test", {})
    assert len(result) == 384


def test_api_failure_no_fallback_raises() -> None:
    with patch("app.llm.embeddings._embed_via_company_api", side_effect=Exception("timeout")):
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.embeddings_provider = "company_api"
            mock_settings.return_value.embeddings_api_base_url = "https://fake.api"
            mock_settings.return_value.embeddings_api_key = "key"
            mock_settings.return_value.embeddings_model = "model"
            mock_settings.return_value.embeddings_dimension = 384
            mock_settings.return_value.embeddings_fallback_enabled = False
            with pytest.raises(Exception):
                embed_text("test", {})


# ---------------------------------------------------------------------------
# Dimension validation
# ---------------------------------------------------------------------------

def test_dimension_mismatch_raises() -> None:
    mock_model = MagicMock()
    import numpy as np
    mock_model.encode.return_value = np.zeros(128)  # wrong dim

    with patch("app.llm.embeddings._local_model", mock_model):
        with patch("app.core.config.get_settings") as mock_settings:
            mock_settings.return_value.embeddings_provider = "local"
            mock_settings.return_value.embeddings_api_base_url = ""
            mock_settings.return_value.embeddings_api_key = ""
            mock_settings.return_value.embeddings_model = "model"
            mock_settings.return_value.embeddings_dimension = 384  # expects 384, gets 128
            mock_settings.return_value.embeddings_fallback_enabled = True
            with pytest.raises(ValueError, match="dimension mismatch"):
                embed_text("test", {})
