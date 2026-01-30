# SPDX-License-Identifier: Apache-2.0
"""
Batched engine for continuous batching with multiple concurrent users.

This engine wraps AsyncEngineCore to provide continuous batching
for better throughput when serving multiple concurrent requests.

For MLLM models, this engine supports a hybrid approach:
- Text-only requests: Use BatchGenerator for continuous batching
- Multimodal requests (with images/videos): Fall back to MLLM.chat() for correct processing

This is necessary because BatchGenerator only supports token IDs, not pixel_values.
"""

import asyncio
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from .base import BaseEngine, GenerationOutput
from ..api.utils import is_mllm_model, clean_output_text
from ..api.tool_calling import convert_tools_for_template

logger = logging.getLogger(__name__)


def _extract_media_from_messages(messages: List[Dict[str, Any]]) -> tuple:
    """
    Extract images and videos from OpenAI-format messages.

    Returns:
        Tuple of (has_media, images_list, videos_list)
    """
    images = []
    videos = []

    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, list):
            continue

        for item in content:
            # Handle Pydantic models
            if hasattr(item, "model_dump"):
                item = item.model_dump()
            elif hasattr(item, "dict"):
                item = item.dict()

            if not isinstance(item, dict):
                continue

            item_type = item.get("type", "")

            if item_type == "image_url":
                img_url = item.get("image_url", {})
                if isinstance(img_url, str):
                    images.append(img_url)
                elif isinstance(img_url, dict):
                    url = img_url.get("url", "")
                    if url:
                        images.append(url)

            elif item_type == "image":
                img = item.get("image") or item.get("url", "")
                if img:
                    images.append(img)

            elif item_type == "video_url":
                vid_url = item.get("video_url", {})
                if isinstance(vid_url, str):
                    videos.append(vid_url)
                elif isinstance(vid_url, dict):
                    url = vid_url.get("url", "")
                    if url:
                        videos.append(url)

            elif item_type == "video":
                vid = item.get("video") or item.get("url", "")
                if vid:
                    videos.append(vid)

    has_media = bool(images or videos)
    return has_media, images, videos


class MLLMModelWrapper:
    """
    Wrapper for MLLM models to make them compatible with BatchGenerator.

    BatchGenerator expects model output to be subscriptable (logits array),
    but MLLM models return LanguageModelOutput objects. This wrapper extracts
    the logits from the output.

    Also handles Gemma 3's required pixel_values argument by injecting None
    for text-only requests.
    """

    def __init__(self, model):
        self._model = model
        # Detect if this is a Gemma 3 model (requires pixel_values as positional arg)
        self._is_gemma3 = hasattr(model, 'model_type') and 'gemma3' in str(getattr(model, 'model_type', '')).lower()

    def __call__(self, *args, **kwargs):
        """Call the model and extract logits from LanguageModelOutput."""
        # Gemma 3 requires pixel_values as a positional argument, unlike Qwen
        # which makes it optional. Inject pixel_values=None for text-only requests.
        if self._is_gemma3 and 'pixel_values' not in kwargs:
            kwargs['pixel_values'] = None

        output = self._model(*args, **kwargs)
        # If output has logits attribute, return just the logits
        if hasattr(output, 'logits'):
            return output.logits
        return output

    def __getattr__(self, name):
        """Forward all other attributes to the wrapped model."""
        return getattr(self._model, name)


class BatchedEngine(BaseEngine):
    """
    Batched engine for continuous batching.

    This engine provides better throughput when serving multiple
    concurrent users by batching requests together.
    """

    def __init__(
        self,
        model_name: str,
        trust_remote_code: bool = True,
        scheduler_config: Optional[Any] = None,
        stream_interval: int = 1,
    ):
        """
        Initialize the batched engine.

        Args:
            model_name: HuggingFace model name or local path
            trust_remote_code: Whether to trust remote code
            scheduler_config: Optional scheduler configuration
            stream_interval: Tokens to batch before streaming (1=every token)
        """
        self._model_name = model_name
        self._trust_remote_code = trust_remote_code
        self._scheduler_config = scheduler_config
        self._stream_interval = stream_interval
        self._is_mllm = is_mllm_model(model_name)

        self._model = None
        self._tokenizer = None
        self._engine = None
        self._mllm = None  # Keep reference to MLLM for multimodal requests
        self._loaded = False

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    @property
    def is_mllm(self) -> bool:
        """Check if this is a multimodal model."""
        return self._is_mllm

    @property
    def tokenizer(self) -> Any:
        """Get the tokenizer."""
        return self._tokenizer

    async def start(self) -> None:
        """Start the engine (load model if not loaded)."""
        if self._loaded:
            return

        from ..scheduler.engine_core import EngineConfig, AsyncEngineCore
        from ..scheduler import SchedulerConfig
        import os

        # Note on Gemma 3 sliding window configuration:
        # - Default sliding_window=1024 works for multimodal (image+text)
        # - GEMMA3_SLIDING_WINDOW=0 (full KVCache) enables extended text context
        #   but BREAKS multimodal generation with longer prompts (~1300+ tokens)
        #
        # Do NOT auto-set GEMMA3_SLIDING_WINDOW=0 for MLLM models.
        # Users who need extended text-only context can manually set:
        #   GEMMA3_SLIDING_WINDOW=0 (but avoid multimodal with long prompts)
        if ("gemma-3" in self._model_name.lower() or "gemma3" in self._model_name.lower()):
            sliding_window = os.environ.get("GEMMA3_SLIDING_WINDOW")
            if sliding_window is not None:
                logger.info(
                    f"Gemma 3: Using GEMMA3_SLIDING_WINDOW={sliding_window} "
                    f"(Note: value 0 may cause issues with multimodal + long prompts)"
                )
            else:
                logger.info(
                    "Gemma 3: Using default sliding_window=1024 (optimal for multimodal)"
                )

        # Load model and tokenizer
        if self._is_mllm:
            from ..models.mllm import MLXMultimodalLM
            mllm = MLXMultimodalLM(
                self._model_name,
                trust_remote_code=self._trust_remote_code,
            )
            mllm.load()
            # Keep reference to MLLM for multimodal requests
            # (BatchGenerator can't handle pixel_values, so we use MLLM.chat() for images)
            self._mllm = mllm
            # Wrap MLLM model so BatchGenerator can use it for text-only requests
            # (MLLM returns LanguageModelOutput, BatchGenerator expects logits)
            self._model = MLLMModelWrapper(mllm.model)
            self._tokenizer = mllm.processor
        else:
            from ..utils.tokenizer import load_model_with_fallback

            # Build tokenizer config
            tokenizer_config = {"trust_remote_code": self._trust_remote_code}

            # Qwen3 fix
            if "qwen3" in self._model_name.lower() or "Qwen3" in self._model_name:
                tokenizer_config["eos_token"] = "<|im_end|>"

            self._model, self._tokenizer = load_model_with_fallback(
                self._model_name,
                tokenizer_config=tokenizer_config,
            )

        # Create engine config
        scheduler_config = self._scheduler_config or SchedulerConfig()
        engine_config = EngineConfig(
            model_name=self._model_name,
            scheduler_config=scheduler_config,
            stream_interval=self._stream_interval,
        )

        # Create async engine
        self._engine = AsyncEngineCore(
            model=self._model,
            tokenizer=self._tokenizer,
            config=engine_config,
        )

        await self._engine.engine.start()
        self._loaded = True
        logger.info(f"BatchedEngine loaded: {self._model_name}")

    async def stop(self) -> None:
        """Stop the engine and cleanup resources."""
        if self._engine:
            await self._engine.stop()
            self._engine.engine.close()
        self._engine = None
        self._model = None
        self._mllm = None
        self._tokenizer = None
        self._loaded = False
        logger.info("BatchedEngine stopped")

    def _apply_chat_template(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[dict]] = None,
    ) -> str:
        """Apply chat template to messages."""
        if hasattr(self._tokenizer, 'apply_chat_template'):
            template_kwargs = {
                "tokenize": False,
                "add_generation_prompt": True,
                "enable_thinking": True,  # Enable thinking mode for reasoning models
            }
            if tools:
                template_kwargs["tools"] = tools

            try:
                return self._tokenizer.apply_chat_template(messages, **template_kwargs)
            except TypeError:
                # Some templates don't support all kwargs
                for key in ["tools", "enable_thinking"]:
                    if key in template_kwargs:
                        del template_kwargs[key]
                return self._tokenizer.apply_chat_template(messages, **template_kwargs)
        else:
            prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
            return prompt + "\nassistant:"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> GenerationOutput:
        """
        Generate a complete response (non-streaming).

        Args:
            prompt: Input text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling
            stop: Stop sequences
            **kwargs: Additional model-specific parameters

        Returns:
            GenerationOutput with complete text
        """
        if not self._loaded:
            await self.start()

        from .request import SamplingParams

        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or [],
        )

        output = await self._engine.generate(
            prompt=prompt,
            sampling_params=sampling_params,
        )

        text = clean_output_text(output.output_text)

        return GenerationOutput(
            text=text,
            prompt_tokens=output.prompt_tokens,
            completion_tokens=output.completion_tokens,
            finish_reason=output.finish_reason,
        )

    async def stream_generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop: Optional[List[str]] = None,
        **kwargs,
    ) -> AsyncIterator[GenerationOutput]:
        """
        Stream generation token by token.

        Args:
            prompt: Input text
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling
            stop: Stop sequences
            **kwargs: Additional model-specific parameters

        Yields:
            GenerationOutput with incremental text
        """
        if not self._loaded:
            await self.start()

        from .request import SamplingParams

        sampling_params = SamplingParams(
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop or [],
        )

        request_id = await self._engine.add_request(
            prompt=prompt,
            sampling_params=sampling_params,
        )

        async for output in self._engine.stream_outputs(request_id):
            text = clean_output_text(output.output_text)

            yield GenerationOutput(
                text=text,
                new_text=output.new_text,
                prompt_tokens=output.prompt_tokens,
                completion_tokens=output.completion_tokens,
                finished=output.finished,
                finish_reason=output.finish_reason,
            )

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        tools: Optional[List[dict]] = None,
        images: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        **kwargs,
    ) -> GenerationOutput:
        """
        Chat completion (non-streaming).

        For MLLM models with images/videos, uses the native MLLM.chat() method
        which properly processes multimodal content through the vision encoder.
        For text-only requests, uses BatchGenerator for continuous batching.

        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling
            tools: Optional tool definitions
            images: Optional image URLs/paths
            videos: Optional video URLs/paths
            **kwargs: Additional model-specific parameters

        Returns:
            GenerationOutput with assistant response
        """
        if not self._loaded:
            await self.start()

        # Check for multimodal content in messages
        has_media, extracted_images, extracted_videos = _extract_media_from_messages(messages)

        # Also check explicit images/videos parameters
        if images:
            extracted_images.extend(images)
            has_media = True
        if videos:
            extracted_videos.extend(videos)
            has_media = True

        # For MLLM with multimodal content, use native MLLM.chat() for correct processing
        # BatchGenerator doesn't support pixel_values, so we can't batch multimodal requests
        if self._is_mllm and has_media and self._mllm is not None:
            logger.debug(f"Routing multimodal request to MLLM.chat() ({len(extracted_images)} images, {len(extracted_videos)} videos)")

            # Run MLLM.chat() in thread pool to avoid blocking
            output = await asyncio.to_thread(
                self._mllm.chat,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

            return GenerationOutput(
                text=clean_output_text(output.text),
                prompt_tokens=output.prompt_tokens,
                completion_tokens=output.completion_tokens,
                finish_reason=output.finish_reason or "stop",
            )

        # For text-only requests, use BatchGenerator for continuous batching
        # Convert tools for template
        template_tools = convert_tools_for_template(tools) if tools else None

        # Apply chat template
        prompt = self._apply_chat_template(messages, template_tools)

        return await self.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs,
        )

    async def stream_chat(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: int = 256,
        temperature: float = 0.7,
        top_p: float = 0.9,
        tools: Optional[List[dict]] = None,
        images: Optional[List[str]] = None,
        videos: Optional[List[str]] = None,
        **kwargs,
    ) -> AsyncIterator[GenerationOutput]:
        """
        Stream chat completion token by token.

        For MLLM models with images/videos, uses the native MLLM.stream_chat() method
        which properly processes multimodal content through the vision encoder.
        For text-only requests, uses BatchGenerator for continuous batching.

        Args:
            messages: List of chat messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling
            tools: Optional tool definitions
            images: Optional image URLs/paths
            videos: Optional video URLs/paths
            **kwargs: Additional model-specific parameters

        Yields:
            GenerationOutput with incremental text
        """
        if not self._loaded:
            await self.start()

        # Check for multimodal content in messages
        has_media, extracted_images, extracted_videos = _extract_media_from_messages(messages)

        # Also check explicit images/videos parameters
        if images:
            extracted_images.extend(images)
            has_media = True
        if videos:
            extracted_videos.extend(videos)
            has_media = True

        # For MLLM with multimodal content, use native MLLM.stream_chat() for correct processing
        if self._is_mllm and has_media and self._mllm is not None:
            logger.debug(f"Routing multimodal streaming request to MLLM.stream_chat() ({len(extracted_images)} images)")

            # Run MLLM.stream_chat() in thread pool, yielding results
            import queue
            import threading

            result_queue = queue.Queue()
            error_holder = [None]

            def stream_worker():
                try:
                    for chunk in self._mllm.stream_chat(
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        **kwargs,
                    ):
                        result_queue.put(chunk)
                    result_queue.put(None)  # Signal completion
                except Exception as e:
                    error_holder[0] = e
                    result_queue.put(None)

            thread = threading.Thread(target=stream_worker)
            thread.start()

            accumulated_text = ""
            while True:
                # Use asyncio.to_thread for non-blocking queue get
                chunk = await asyncio.to_thread(result_queue.get)
                if chunk is None:
                    if error_holder[0]:
                        raise error_holder[0]
                    break

                new_text = chunk.text
                accumulated_text += new_text

                yield GenerationOutput(
                    text=accumulated_text,
                    new_text=new_text,
                    prompt_tokens=chunk.prompt_tokens,
                    completion_tokens=chunk.completion_tokens,
                    finished=False,
                    finish_reason=None,
                )

            thread.join()

            # Final yield with finished=True
            yield GenerationOutput(
                text=clean_output_text(accumulated_text),
                new_text="",
                prompt_tokens=chunk.prompt_tokens if chunk else 0,
                completion_tokens=chunk.completion_tokens if chunk else 0,
                finished=True,
                finish_reason="stop",
            )
            return

        # For text-only requests, use BatchGenerator for continuous batching
        # Convert tools for template
        template_tools = convert_tools_for_template(tools) if tools else None

        # Apply chat template
        prompt = self._apply_chat_template(messages, template_tools)

        async for output in self.stream_generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            **kwargs,
        ):
            yield output

    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        stats = {
            "engine_type": "batched",
            "model_name": self._model_name,
            "is_mllm": self._is_mllm,
            "loaded": self._loaded,
            "stream_interval": self._stream_interval,
        }
        if self._engine:
            stats.update(self._engine.get_stats())
        return stats

    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """Get cache statistics."""
        if self._engine:
            return self._engine.get_cache_stats()
        return None
