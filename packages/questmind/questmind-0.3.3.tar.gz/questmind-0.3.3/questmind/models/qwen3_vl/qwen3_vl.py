from typing import Optional

import mlx.core as mx
import mlx.nn as nn
import numpy as np

from .config import ModelConfig
from .language import LanguageModel
from .vision import VisionModel

# Import vision embedding cache (F10 optimization)
from questmind.inference.utils import (
    get_cached_vision_embedding,
    cache_vision_embedding,
    _hash_pixel_values,
    VISION_CACHE_ENABLED,
)


def masked_scatter(
    final_embedding: mx.array,
    image_mask_expanded: mx.array,
    scaled_image_features: mx.array,
):
    # Reshape the tensors to 1D
    final_embedding_shape = final_embedding.shape
    scaled_image_features_flattened = mx.flatten(scaled_image_features)
    final_embedding_flattened = mx.flatten(final_embedding)
    image_mask_expanded_flattened = mx.flatten(image_mask_expanded)

    # Scatter the scaled image features into the special image token positions
    image_positions = mx.array(np.where(image_mask_expanded_flattened)[0], mx.uint32)
    final_embedding_flattened[image_positions] = scaled_image_features_flattened

    # Reshape back to the original shape
    final_embedding = mx.reshape(final_embedding_flattened, final_embedding_shape)

    return final_embedding


class Model(nn.Module):
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.vision_tower = VisionModel(config.vision_config)
        self.language_model = LanguageModel(config.text_config, config)

    def get_input_embeddings(
        self,
        input_ids: Optional[mx.array] = None,
        pixel_values: Optional[mx.array] = None,
        **kwargs,
    ):
        image_grid_thw = kwargs.get("image_grid_thw", None)
        video_grid_thw = kwargs.get("video_grid_thw", None)
        grid_thw = image_grid_thw if image_grid_thw is not None else video_grid_thw

        if pixel_values is None:
            return {
                "inputs_embeds": self.language_model.model.embed_tokens(input_ids),
                "visual_pos_masks": None,
                "deepstack_visual_embeds": None,
            }

        # Check if input_ids has image tokens - if not, just return text embeddings
        # This handles decode steps where pixel_values is passed but input_ids only has text
        has_image_tokens = int((input_ids == self.config.image_token_index).sum()) > 0
        has_video_tokens = int((input_ids == self.config.video_token_index).sum()) > 0 if hasattr(self.config, 'video_token_index') else False


        if not has_image_tokens and not has_video_tokens:
            # No image/video tokens in input_ids - just return text embeddings
            return {
                "inputs_embeds": self.language_model.model.embed_tokens(input_ids),
                "visual_pos_masks": None,
                "deepstack_visual_embeds": None,
            }

        dtype = self.vision_tower.patch_embed.proj.weight.dtype
        pixel_values = pixel_values.astype(dtype)

        # Get the input embeddings from the language model
        inputs_embeds = self.language_model.model.embed_tokens(input_ids)

        # F10: Check vision embedding cache before encoding
        cache_key = None
        cached_result = None
        if VISION_CACHE_ENABLED:
            cache_key = _hash_pixel_values(pixel_values)
            cached_result = get_cached_vision_embedding(pixel_values, cache_key)

        if cached_result is not None:
            # Cache hit - skip vision encoding
            hidden_states, deepstack_image_embeds = cached_result
        else:
            # Cache miss - run vision encoder
            hidden_states, deepstack_image_embeds = self.vision_tower(
                pixel_values, grid_thw
            )
            # Evaluate tensors before caching to break computation graph dependency
            mx.eval(hidden_states)
            if deepstack_image_embeds is not None:
                mx.eval(deepstack_image_embeds)
            # Cache the result for future use
            if VISION_CACHE_ENABLED:
                cache_vision_embedding(pixel_values, hidden_states, deepstack_image_embeds, cache_key)

        visual_pos_masks = None
        deepstack_visual_embeds = None

        # Insert special image tokens in the input_ids
        inputs_embeds, image_mask = self.merge_input_ids_with_image_features(
            hidden_states,
            inputs_embeds,
            input_ids,
            self.config.image_token_index,
            self.config.video_token_index,
        )

        image_mask = image_mask[..., 0]
        visual_pos_masks = image_mask
        deepstack_visual_embeds = deepstack_image_embeds

        return {
            "inputs_embeds": inputs_embeds,
            "visual_pos_masks": visual_pos_masks,
            "deepstack_visual_embeds": deepstack_visual_embeds,
        }

    @staticmethod
    def merge_input_ids_with_image_features(
        image_features, inputs_embeds, input_ids, image_token_index, video_token_index
    ):
        special_image_mask = input_ids == image_token_index
        special_video_mask = input_ids == video_token_index
        special_image_mask = special_image_mask | special_video_mask
        n_image_tokens = special_image_mask.sum()
        special_image_mask = special_image_mask[..., None]
        special_image_mask = mx.broadcast_to(special_image_mask, inputs_embeds.shape)

        n_image_features = image_features.shape[0]
        n_image_mask_elements = special_image_mask.sum()
        if n_image_mask_elements != image_features.size:
            raise ValueError(
                f"Image features and image tokens do not match: tokens: {n_image_tokens}, features {n_image_features}"
            )

        inputs_embeds = masked_scatter(
            inputs_embeds, special_image_mask, image_features
        )

        return inputs_embeds, special_image_mask

    @property
    def layers(self):
        return self.language_model.model.layers

    def __call__(
        self,
        input_ids: mx.array,
        pixel_values: Optional[mx.array] = None,
        mask: Optional[mx.array] = None,
        cache=None,
        **kwargs,
    ):

        inputs_embeds = self.get_input_embeddings(input_ids, pixel_values, **kwargs)

        kwargs.update(
            {
                "pixel_values": pixel_values,
                **inputs_embeds,
            }
        )

        logits = self.language_model(input_ids, mask=mask, cache=cache, **kwargs)
        return logits

    def sanitize(self, weights):
        sanitized_weights = {}
        for key, value in weights.items():
            if "model" in key:
                if "model.language_model" in key:
                    key = key.replace("model.language_model", "language_model.model")

                elif "model.visual" in key:
                    key = key.replace("model.visual", "vision_tower")
            elif "lm_head" in key:
                key = key.replace("lm_head", "language_model.lm_head")

            sanitized_weights[key] = value

        return sanitized_weights
