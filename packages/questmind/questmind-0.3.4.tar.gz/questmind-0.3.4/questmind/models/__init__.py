# SPDX-License-Identifier: Apache-2.0
"""Models module for questmind - VLM model implementations."""

from questmind.models.base import (
    BaseModelConfig,
    BaseImageProcessor,
    LanguageModelOutput,
)
from questmind.models.cache import KVCache, RotatingKVCache
from questmind.models.llm import MLXLanguageModel
from questmind.models.mllm import MLXMultimodalLM

# Model registry for auto-loading
MODEL_REGISTRY = {
    "qwen3_vl": "questmind.models.qwen3_vl",
    "qwen3_vl_moe": "questmind.models.qwen3_vl_moe",
}

__all__ = [
    "BaseModelConfig",
    "BaseImageProcessor",
    "LanguageModelOutput",
    "KVCache",
    "RotatingKVCache",
    "MLXLanguageModel",
    "MLXMultimodalLM",
    "MODEL_REGISTRY",
]
