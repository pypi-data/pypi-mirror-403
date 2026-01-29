"""Tests for the HuggingFace loading utilities."""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from master_mind.teaching.hf import (
    _get_cache_path,
    _get_hf_cache_dir,
    _sanitize_id,
    make_hf_model_resource,
    make_hf_dataset_resource,
    ENV_VAR,
)


class TestGetCachePath:
    """Tests for _get_cache_path function."""

    def test_returns_none_when_env_not_set(self):
        """Test that None is returned when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert _get_cache_path() is None

    def test_returns_path_when_env_set(self):
        """Test that Path is returned when env var is set."""
        with patch.dict(os.environ, {ENV_VAR: "/some/path"}):
            result = _get_cache_path()
            assert result == Path("/some/path")


class TestGetHfCacheDir:
    """Tests for _get_hf_cache_dir function."""

    def test_returns_none_when_env_not_set(self):
        """Test that None is returned when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            assert _get_hf_cache_dir() is None

    def test_returns_huggingface_subdir(self, tmp_path):
        """Test that huggingface subdirectory is returned."""
        with patch.dict(os.environ, {ENV_VAR: str(tmp_path)}):
            result = _get_hf_cache_dir()
            expected = tmp_path / "huggingface"
            assert result == str(expected)
            assert expected.exists()


class TestSanitizeId:
    """Tests for _sanitize_id function."""

    def test_replaces_slash_with_dash(self):
        """Test that / is replaced with -."""
        assert _sanitize_id("org/model") == "org-model"

    def test_handles_multiple_slashes(self):
        """Test handling of multiple slashes."""
        assert _sanitize_id("org/sub/model") == "org-sub-model"

    def test_no_change_without_slash(self):
        """Test that IDs without slash are unchanged."""
        assert _sanitize_id("model-name") == "model-name"


class TestMakeHfModelResource:
    """Tests for make_hf_model_resource function."""

    def test_creates_resource_with_correct_key(self):
        """Test that resource has correct key."""
        resource = make_hf_model_resource(
            "bert-base-uncased",
            "BERT model",
            "AutoTokenizer",
        )
        assert resource.key == "bert-base-uncased"

    def test_creates_resource_with_correct_description(self):
        """Test that resource has correct description."""
        resource = make_hf_model_resource(
            "bert-base-uncased",
            "BERT model",
            "AutoTokenizer",
        )
        assert resource.description == "BERT model"

    def test_optional_flag(self):
        """Test that optional flag is set correctly."""
        resource = make_hf_model_resource(
            "bert-base-uncased",
            "BERT model",
            "AutoTokenizer",
            optional=True,
        )
        assert resource.optional is True

    def test_download_uses_local_cache_when_complete(self, tmp_path):
        """Test that download uses local cache when download is complete."""
        model_path = tmp_path / "huggingface" / "models" / "bert-base-uncased"
        model_path.mkdir(parents=True)
        (model_path / ".downloaded.ok").touch()

        mock_transformers = MagicMock()

        with patch.dict(os.environ, {ENV_VAR: str(tmp_path)}):
            with patch.dict("sys.modules", {"transformers": mock_transformers}):
                resource = make_hf_model_resource(
                    "bert-base-uncased",
                    "BERT model",
                    "AutoTokenizer",
                )
                result = resource.download()
                assert "Already exists" in result
                # Ensure no HF calls were made
                mock_transformers.AutoTokenizer.from_pretrained.assert_not_called()

    def test_download_falls_back_to_hf_when_no_cache_path(self):
        """Test that download falls back to HF when no cache path."""
        mock_tokenizer = MagicMock()
        mock_transformers = MagicMock()
        mock_transformers.AutoTokenizer = mock_tokenizer

        with patch.dict(os.environ, {}, clear=True):
            with patch.dict("sys.modules", {"transformers": mock_transformers}):
                resource = make_hf_model_resource(
                    "bert-base-uncased",
                    "BERT model",
                    "AutoTokenizer",
                )
                result = resource.download()
                assert "Cached" in result
                mock_tokenizer.from_pretrained.assert_called_once()


class TestMakeHfDatasetResource:
    """Tests for make_hf_dataset_resource function."""

    def test_creates_resource_with_correct_key_single_split(self):
        """Test that resource has correct key for single split."""
        resource = make_hf_dataset_resource(
            "imdb",
            "IMDB dataset",
            splits="train",
        )
        assert resource.key == "imdb/train"

    def test_creates_resource_with_correct_key_multiple_splits(self):
        """Test that resource has correct key for multiple splits."""
        resource = make_hf_dataset_resource(
            "imdb",
            "IMDB dataset",
            splits=["train", "test"],
        )
        assert resource.key == "imdb/train+test"

    def test_creates_resource_with_name_in_key(self):
        """Test that config name is included in key."""
        resource = make_hf_dataset_resource(
            "glue",
            "GLUE SST-2",
            splits="validation",
            name="sst2",
        )
        assert resource.key == "glue/sst2/validation"

    def test_creates_resource_with_correct_description(self):
        """Test that resource has correct description."""
        resource = make_hf_dataset_resource(
            "imdb",
            "IMDB dataset",
            splits="train",
        )
        assert resource.description == "IMDB dataset"

    def test_optional_flag(self):
        """Test that optional flag is set correctly."""
        resource = make_hf_dataset_resource(
            "imdb",
            "IMDB dataset",
            splits="train",
            optional=True,
        )
        assert resource.optional is True

    def test_download_uses_local_cache_when_complete(self, tmp_path):
        """Test that download uses local cache when download is complete."""
        dataset_path = tmp_path / "huggingface" / "datasets" / "imdb" / "train"
        dataset_path.mkdir(parents=True)
        (dataset_path / ".downloaded.ok").touch()

        mock_datasets = MagicMock()

        with patch.dict(os.environ, {ENV_VAR: str(tmp_path)}):
            with patch.dict("sys.modules", {"datasets": mock_datasets}):
                resource = make_hf_dataset_resource(
                    "imdb",
                    "IMDB dataset",
                    splits="train",
                )
                result = resource.download()
                assert "already exists" in result
                # Ensure no HF calls were made
                mock_datasets.load_dataset.assert_not_called()

    def test_download_falls_back_to_hf_when_no_cache_path(self):
        """Test that download falls back to HF when no cache path."""
        mock_datasets = MagicMock()

        with patch.dict(os.environ, {}, clear=True):
            with patch.dict("sys.modules", {"datasets": mock_datasets}):
                resource = make_hf_dataset_resource(
                    "imdb",
                    "IMDB dataset",
                    splits="train",
                )
                result = resource.download()
                assert "Cached" in result
                mock_datasets.load_dataset.assert_called_once()
