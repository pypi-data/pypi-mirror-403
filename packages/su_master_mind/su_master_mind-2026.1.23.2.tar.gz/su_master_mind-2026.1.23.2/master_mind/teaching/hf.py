"""HuggingFace loading utilities with local cache support.

This module provides functions to load HuggingFace datasets and models,
first checking a local cache directory (for unreliable HF caching environments)
and falling back to HuggingFace Hub with a warning.

Usage in notebooks:
    from master_mind.teaching.hf import load_hf_dataset, load_hf_model

Environment Variables:
    MASTER_MIND_DATA_PATH: Path to the shared local cache directory.
        If not set, falls back directly to HuggingFace Hub.
"""

import os
import warnings
from pathlib import Path
from typing import Any, Optional, Type, Union

from master_mind.plugin import DOWNLOAD_MARKER

# Constants
ENV_VAR = "MASTER_MIND_DATA_PATH"


def _is_download_complete(path: Path) -> bool:
    """Check if a download is complete by looking for the marker file."""
    return (path / DOWNLOAD_MARKER).exists()


def _get_cache_path() -> Optional[Path]:
    """Get the local cache path from environment variable."""
    path = os.environ.get(ENV_VAR)
    if path:
        return Path(path)
    return None


def _sanitize_id(hf_id: str) -> str:
    """Convert HuggingFace ID to filesystem-safe directory name.

    Replaces "/" with "-" to create valid directory names.
    """
    return hf_id.replace("/", "-")


def _warn_fallback(resource_type: str, resource_id: str):
    """Emit a warning when falling back to HuggingFace Hub."""
    msg = (
        f"{resource_type} '{resource_id}' not found in local cache. "
        f"Downloading from HuggingFace Hub. "
        f"Set {ENV_VAR} environment variable to use local cache."
    )
    warnings.warn(msg, UserWarning, stacklevel=3)


def load_hf_dataset(
    dataset_id: str,
    name: Optional[str] = None,
    split: Optional[str] = None,
    **kwargs,
) -> Union["Dataset", "DatasetDict"]:
    """Load a HuggingFace dataset, checking local cache first.

    Args:
        dataset_id: HuggingFace dataset identifier (e.g., "imdb", "jxie/flickr8k")
        name: Dataset configuration name (e.g., "sst2" for glue)
        split: Specific split to load (e.g., "train", "validation")
        **kwargs: Additional arguments passed to load_dataset/load_from_disk

    Returns:
        Dataset or DatasetDict depending on whether split is specified

    Example:
        >>> dataset = load_hf_dataset("imdb", split="train")
        >>> flickr = load_hf_dataset("jxie/flickr8k")  # returns DatasetDict
        >>> sst2 = load_hf_dataset("glue", name="sst2", split="validation")
    """
    from datasets import DatasetDict, load_dataset, load_from_disk

    cache_path = _get_cache_path()

    if cache_path:
        # Build local path: datasets/<sanitized-id>[-<name>]/[<split>/]
        safe_id = _sanitize_id(dataset_id)
        if name:
            safe_id = f"{safe_id}-{name}"
        local_base = cache_path / "datasets" / safe_id

        if local_base.exists():
            if split:
                # Load specific split
                split_path = local_base / split
                if _is_download_complete(split_path):
                    return load_from_disk(str(split_path))
            else:
                # Load all splits as DatasetDict
                splits = {}
                for p in sorted(local_base.iterdir()):
                    if p.is_dir() and _is_download_complete(p):
                        splits[p.name] = load_from_disk(str(p))
                if splits:
                    return DatasetDict(splits)

    # Fall back to HuggingFace Hub
    _warn_fallback("Dataset", dataset_id)
    return load_dataset(dataset_id, name, split=split, **kwargs)


def load_hf_model(
    model_id: str,
    model_class: Optional[Type] = None,
    **kwargs,
) -> Any:
    """Load a HuggingFace model, checking local cache first.

    Args:
        model_id: HuggingFace model identifier (e.g., "distilbert-base-uncased")
        model_class: Optional model class to use. If None, uses AutoModel.
        **kwargs: Additional arguments passed to from_pretrained()

    Returns:
        The loaded model

    Example:
        >>> from transformers import AutoModelForCausalLM
        >>> model = load_hf_model("TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        ...                       AutoModelForCausalLM, device_map="auto")
    """
    if model_class is None:
        from transformers import AutoModel

        model_class = AutoModel

    cache_path = _get_cache_path()

    if cache_path:
        safe_id = _sanitize_id(model_id)
        local_path = cache_path / "models" / safe_id

        if _is_download_complete(local_path):
            return model_class.from_pretrained(str(local_path), **kwargs)

    # Fall back to HuggingFace Hub
    _warn_fallback("Model", model_id)
    return model_class.from_pretrained(model_id, **kwargs)


def load_hf_tokenizer(
    model_id: str,
    tokenizer_class: Optional[Type] = None,
    **kwargs,
) -> Any:
    """Load a HuggingFace tokenizer, checking local cache first.

    Args:
        model_id: HuggingFace model identifier
        tokenizer_class: Optional tokenizer class. If None, uses AutoTokenizer.
        **kwargs: Additional arguments passed to from_pretrained()

    Returns:
        The loaded tokenizer

    Example:
        >>> tokenizer = load_hf_tokenizer("distilbert-base-uncased")
    """
    if tokenizer_class is None:
        from transformers import AutoTokenizer

        tokenizer_class = AutoTokenizer

    cache_path = _get_cache_path()

    if cache_path:
        safe_id = _sanitize_id(model_id)
        local_path = cache_path / "models" / safe_id

        if _is_download_complete(local_path):
            return tokenizer_class.from_pretrained(str(local_path), **kwargs)

    # Fall back to HuggingFace Hub
    # If MASTER_MIND_DATA_PATH was set, use fallback cache dir to avoid HF cache issues
    fallback_cache = _get_fallback_cache_dir() if cache_path else None
    _warn_fallback("Tokenizer", model_id, fallback_cache)
    if fallback_cache:
        kwargs.setdefault("cache_dir", fallback_cache)
    return tokenizer_class.from_pretrained(model_id, **kwargs)


def load_hf_processor(
    model_id: str,
    processor_class: Optional[Type] = None,
    **kwargs,
) -> Any:
    """Load a HuggingFace processor, checking local cache first.

    Args:
        model_id: HuggingFace model identifier
        processor_class: Optional processor class. If None, uses AutoProcessor.
        **kwargs: Additional arguments passed to from_pretrained()

    Returns:
        The loaded processor

    Example:
        >>> from transformers import CLIPProcessor
        >>> processor = load_hf_processor("openai/clip-vit-base-patch32", CLIPProcessor)
    """
    if processor_class is None:
        from transformers import AutoProcessor

        processor_class = AutoProcessor

    cache_path = _get_cache_path()

    if cache_path:
        safe_id = _sanitize_id(model_id)
        local_path = cache_path / "models" / safe_id

        if _is_download_complete(local_path):
            return processor_class.from_pretrained(str(local_path), **kwargs)

    # Fall back to HuggingFace Hub
    # If MASTER_MIND_DATA_PATH was set, use fallback cache dir to avoid HF cache issues
    fallback_cache = _get_fallback_cache_dir() if cache_path else None
    _warn_fallback("Processor", model_id, fallback_cache)
    if fallback_cache:
        kwargs.setdefault("cache_dir", fallback_cache)
    return processor_class.from_pretrained(model_id, **kwargs)
