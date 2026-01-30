import glob
import importlib
import inspect
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from typing import Any, Dict, List, Optional, Tuple, Union

# Configurable parallel image loading settings
# PARALLEL_IMAGE_WORKERS: Number of threads for parallel image loading/preprocessing
# Set to 0 to disable parallel loading (sequential behavior)
# Set to None to use default (min(32, cpu_count + 4))
PARALLEL_IMAGE_WORKERS = None  # None = auto, 0 = disabled

# Vision Embedding Cache (F10 optimization)
# Caches vision encoder output to skip re-encoding same images
# VISION_CACHE_ENABLED: Enable/disable vision embedding caching
# VISION_CACHE_MAX_SIZE: Maximum number of cached embeddings (LRU eviction)
VISION_CACHE_ENABLED = True
VISION_CACHE_MAX_SIZE = 50  # Cache up to 50 different images

# Global vision embedding cache (LRU-style dict)
_vision_embedding_cache: Dict[str, Tuple[Any, Any]] = {}
_vision_cache_order: List[str] = []  # Track access order for LRU


def _hash_pixel_values(pixel_values) -> str:
    """Create a hash key for pixel_values tensor for cache lookup."""
    import hashlib
    # Use shape + sample of values for fast hashing
    shape_str = str(pixel_values.shape)
    # Sample first, middle, last values for uniqueness
    flat = pixel_values.reshape(-1)
    n = flat.size
    if n > 100:
        # Sample 100 evenly spaced values
        indices = [0, n//4, n//2, 3*n//4, n-1]
        sample = [float(flat[i]) for i in indices]
    else:
        sample = [float(flat[i]) for i in range(min(10, n))]
    sample_str = str(sample)
    combined = f"{shape_str}_{sample_str}"
    return hashlib.md5(combined.encode()).hexdigest()


def get_cached_vision_embedding(pixel_values, cache_key: str = None):
    """
    Get cached vision embedding if available.

    Args:
        pixel_values: The pixel values tensor
        cache_key: Optional pre-computed cache key

    Returns:
        Tuple of (hidden_states, deepstack_embeds) if cached, None otherwise
    """
    if not VISION_CACHE_ENABLED:
        return None

    if cache_key is None:
        cache_key = _hash_pixel_values(pixel_values)

    if cache_key in _vision_embedding_cache:
        # Move to end for LRU
        if cache_key in _vision_cache_order:
            _vision_cache_order.remove(cache_key)
        _vision_cache_order.append(cache_key)
        return _vision_embedding_cache[cache_key]

    return None


def cache_vision_embedding(pixel_values, hidden_states, deepstack_embeds=None, cache_key: str = None):
    """
    Cache vision embedding for future reuse.

    Args:
        pixel_values: The pixel values tensor (used for key if cache_key not provided)
        hidden_states: Vision encoder output
        deepstack_embeds: Optional deepstack embeddings
        cache_key: Optional pre-computed cache key
    """
    if not VISION_CACHE_ENABLED:
        return

    if cache_key is None:
        cache_key = _hash_pixel_values(pixel_values)

    # LRU eviction if at capacity
    while len(_vision_embedding_cache) >= VISION_CACHE_MAX_SIZE:
        if _vision_cache_order:
            oldest_key = _vision_cache_order.pop(0)
            _vision_embedding_cache.pop(oldest_key, None)
        else:
            # Fallback: clear first item
            if _vision_embedding_cache:
                first_key = next(iter(_vision_embedding_cache))
                del _vision_embedding_cache[first_key]
            break

    _vision_embedding_cache[cache_key] = (hidden_states, deepstack_embeds)
    _vision_cache_order.append(cache_key)


def clear_vision_cache():
    """Clear all cached vision embeddings."""
    global _vision_embedding_cache, _vision_cache_order
    _vision_embedding_cache.clear()
    _vision_cache_order.clear()


def get_vision_cache_stats() -> Dict[str, Any]:
    """Get vision cache statistics."""
    return {
        "enabled": VISION_CACHE_ENABLED,
        "size": len(_vision_embedding_cache),
        "max_size": VISION_CACHE_MAX_SIZE,
        "keys": list(_vision_embedding_cache.keys()),
    }


# =============================================================================
# Multimodal KV Cache with Prefix Matching (F10 v3 - LMCache-style approach)
# =============================================================================
# This caches the full KV states after the first forward pass (including vision)
# and supports PREFIX MATCHING for multi-turn conversations.
#
# Key features:
# 1. Cache KV states keyed by (image_hash, token_sequence)
# 2. On lookup, find longest matching prefix (not just exact match)
# 3. Restore KV states for prefix, only process new tokens
# 4. Achieves text-like speedups (10-20x) for multi-turn vision conversations

MULTIMODAL_KV_CACHE_ENABLED = True
MULTIMODAL_KV_CACHE_MAX_SIZE = 0  # 0 = unlimited (context length is the natural limit)
MULTIMODAL_KV_CACHE_TTL_SECONDS = 60  # Cache expires after 60s of inactivity (0 = no expiry)
MULTIMODAL_KV_DEBUG = True  # Enable debug logging for prefix matching

# Cross-Image Prefix Caching with Position-Based Truncation (Option 2)
# Instead of layer-based recomputation (Option 1 - causes hallucination),
# we use position-based truncation:
# - Text tokens BEFORE first image: Safe to reuse (no image dependency)
# - Image tokens and text AFTER: Must be recomputed with new images
#
# This is similar to MPIC (Multimodal Position-Independent Caching) approach:
# Cache only the "pure text" prefix that doesn't depend on any image content.
CROSS_IMAGE_CACHING_ENABLED = True  # Enable cross-image prefix matching
VISION_CRITICAL_LAYERS = 8  # Kept for backward compatibility but not used in Option 2

# Qwen3-VL vision token IDs (used to detect first_image_position)
QWEN3_VISION_START_TOKEN_ID = 151652  # <|vision_start|>
QWEN3_IMAGE_TOKEN_ID = 151655          # <|image_pad|>

# Global multimodal KV cache with prefix matching support
# Structure: {image_hash: [(token_ids, kv_states, num_tokens, first_image_position), ...]}
# Note: first_image_position = -1 means no images (text-only), otherwise it's the
# position of the first <|vision_start|> token
_multimodal_prefix_cache: Dict[str, List[Tuple[List[int], Any, int]]] = {}
_multimodal_cache_access_order: List[str] = []  # Track image_hash access for LRU
_multimodal_cache_last_access: float = 0.0  # Timestamp of last cache access

# Hit/miss tracking for cache statistics
_kv_cache_hits: int = 0
_kv_cache_misses: int = 0
_kv_cache_cross_image_hits: int = 0  # Hits from different image context (text prefix reuse)
_kv_cache_tokens_matched: int = 0  # Total tokens served from cache
_kv_cache_tokens_total: int = 0    # Total tokens requested


def _check_cache_ttl():
    """Check if cache has expired due to inactivity and clear if needed."""
    global _multimodal_cache_last_access
    import time

    if MULTIMODAL_KV_CACHE_TTL_SECONDS <= 0:
        return  # TTL disabled

    current_time = time.time()

    # If cache exists and has expired, clear it
    if _multimodal_prefix_cache and _multimodal_cache_last_access > 0:
        elapsed = current_time - _multimodal_cache_last_access
        if elapsed > MULTIMODAL_KV_CACHE_TTL_SECONDS:
            if MULTIMODAL_KV_DEBUG:
                print(f"[DEBUG] KV Cache EXPIRED: {elapsed:.1f}s since last access (TTL={MULTIMODAL_KV_CACHE_TTL_SECONDS}s)")
            clear_multimodal_kv_cache()

    # Update last access time
    _multimodal_cache_last_access = current_time


def _get_image_hash(pixel_values) -> str:
    """Get hash for image only (without text)."""
    return _hash_pixel_values(pixel_values)


def _find_longest_prefix_match(token_ids: List[int], cached_entries: List) -> Tuple[Any, int, int, int]:
    """
    Find the longest matching prefix among cached entries.

    Returns:
        Tuple of (kv_states, num_matched_tokens, entry_index, first_image_position) or (None, 0, -1, -1) if no match
    """
    best_match = (None, 0, -1, -1)

    for idx, entry in enumerate(cached_entries):
        # Handle both old 3-tuple and new 4-tuple format
        if len(entry) == 4:
            cached_tokens, kv_states, num_tokens, first_image_pos = entry
        else:
            cached_tokens, kv_states, num_tokens = entry
            first_image_pos = -1  # Unknown for legacy entries

        # Find how many tokens match from the start
        match_len = 0
        min_len = min(len(token_ids), len(cached_tokens))

        for i in range(min_len):
            if token_ids[i] == cached_tokens[i]:
                match_len += 1
            else:
                break

        if MULTIMODAL_KV_DEBUG:
            print(f"  [DEBUG] Entry {idx}: cached={len(cached_tokens)}, query={len(token_ids)}, match={match_len}, first_img_pos={first_image_pos}")
            if match_len < len(cached_tokens) and match_len < len(token_ids):
                # Show where mismatch occurred
                if match_len < min_len:
                    print(f"    Mismatch at pos {match_len}: cached={cached_tokens[match_len]}, query={token_ids[match_len]}")

        # We need at least some minimum match to be useful (e.g., 50 tokens)
        # and the match should be the full cached sequence (we can extend from there)
        if match_len >= min(50, len(cached_tokens)) and match_len == len(cached_tokens):
            if match_len > best_match[1]:
                best_match = (kv_states, match_len, idx, first_image_pos)

    return best_match


def get_cached_multimodal_kv_prefix(pixel_values, input_ids) -> Tuple[Any, int, str, bool]:
    """
    Get cached KV states with prefix matching for multimodal input.

    This enables multi-turn conversation speedups by finding the longest
    matching prefix and reusing its KV states.

    Args:
        pixel_values: Image pixel values
        input_ids: Text input token IDs

    Returns:
        Tuple of (kv_states, num_matched_tokens, image_hash, is_position_truncated)
        - kv_states: Cached KV states for the prefix, or None if no match
        - num_matched_tokens: Number of tokens covered by the cache
        - image_hash: Hash of the image for caching new states
        - is_position_truncated: True if this is a cross-image match with position-based truncation
    """
    global _kv_cache_hits, _kv_cache_misses, _kv_cache_cross_image_hits, _kv_cache_tokens_matched, _kv_cache_tokens_total

    if not MULTIMODAL_KV_CACHE_ENABLED:
        return None, 0, "", False

    # Check TTL and clear expired cache (also updates last access time)
    _check_cache_ttl()

    image_hash = _get_image_hash(pixel_values)

    # Convert input_ids to list for comparison
    if hasattr(input_ids, 'tolist'):
        token_list = input_ids.reshape(-1).tolist()
    else:
        token_list = list(input_ids.reshape(-1))

    # Track total tokens requested
    _kv_cache_tokens_total += len(token_list)

    # First, try exact image hash match (fast path)
    kv_states, match_len, entry_idx, first_img_pos = None, 0, -1, -1
    matched_hash = image_hash
    is_position_truncated = False  # Flag for Option 2 position-based truncation

    if image_hash in _multimodal_prefix_cache:
        cached_entries = _multimodal_prefix_cache[image_hash]
        if MULTIMODAL_KV_DEBUG:
            print(f"[DEBUG] KV Cache lookup (exact): image={image_hash[:8]}, query_len={len(token_list)}, num_entries={len(cached_entries)}")
        kv_states, match_len, entry_idx, first_img_pos = _find_longest_prefix_match(token_list, cached_entries)

    # Cross-image prefix matching with POSITION-BASED TRUNCATION (Option 2)
    # Instead of layer-based recomputation (Option 1 - causes hallucination),
    # we truncate the KV cache to only include positions BEFORE the first image.
    #
    # Key insight:
    # - Text tokens before first image: No image dependency, safe to reuse
    # - Image tokens and text after: Have image-dependent attention, must recompute
    #
    # This is more conservative than layer-based but guarantees accuracy.

    is_cross_image_match = False

    if CROSS_IMAGE_CACHING_ENABLED and kv_states is None and len(_multimodal_prefix_cache) > 0:
        if MULTIMODAL_KV_DEBUG:
            print(f"[DEBUG] KV Cache: no exact image match, searching across {len(_multimodal_prefix_cache)} image hashes for position-based reuse...")

        best_cross_match = (None, 0, -1, None, -1)  # (kv_states, match_len, entry_idx, source_hash, first_img_pos)

        for other_hash, other_entries in _multimodal_prefix_cache.items():
            if other_hash == image_hash:
                continue  # Already checked
            cross_kv, cross_len, cross_idx, cross_first_img = _find_longest_prefix_match(token_list, other_entries)
            if cross_len > best_cross_match[1]:
                best_cross_match = (cross_kv, cross_len, cross_idx, other_hash, cross_first_img)

        if best_cross_match[0] is not None:
            full_kv_states, full_match_len, entry_idx, matched_hash, cached_first_img_pos = best_cross_match

            # POSITION-BASED TRUNCATION (Option 2):
            # Only reuse KV for positions BEFORE the first image token
            # This ensures we don't carry over any image-dependent attention patterns

            if cached_first_img_pos > 0:
                # Truncate KV to only include positions [0, first_image_position)
                truncated_kv_states = []
                for layer_idx, layer_kv in enumerate(full_kv_states):
                    if layer_kv is not None:
                        keys, values = layer_kv[0], layer_kv[1]
                        # KV shape: [batch, heads, seq_len, head_dim]
                        truncated_keys = keys[:, :, :cached_first_img_pos, :]
                        truncated_values = values[:, :, :cached_first_img_pos, :]
                        # Update offset if present
                        if len(layer_kv) > 2:
                            truncated_kv_states.append((truncated_keys, truncated_values, cached_first_img_pos))
                        else:
                            truncated_kv_states.append((truncated_keys, truncated_values))
                    else:
                        truncated_kv_states.append(None)

                kv_states = truncated_kv_states
                match_len = cached_first_img_pos  # We only return this many tokens' worth of KV
                first_img_pos = cached_first_img_pos
                is_cross_image_match = True
                is_position_truncated = True

                if MULTIMODAL_KV_DEBUG:
                    print(f"[DEBUG] KV Cache CROSS-IMAGE HIT (position-based): matched from image hash {matched_hash[:8]}")
                    print(f"[DEBUG]   Original cached: {full_match_len} tokens")
                    print(f"[DEBUG]   Truncated to: {match_len} tokens (before first_image_position={cached_first_img_pos})")
                    print(f"[DEBUG]   Will recompute: positions {cached_first_img_pos} to {len(token_list)-1} ({len(token_list) - cached_first_img_pos} tokens)")
            else:
                # No image in cached sequence or position unknown - can't safely truncate
                # Fall back to full forward pass
                if MULTIMODAL_KV_DEBUG:
                    print(f"[DEBUG] KV Cache CROSS-IMAGE: first_image_position={cached_first_img_pos}, cannot truncate - falling back to full forward pass")

    if kv_states is not None:
        # Update LRU order for the matched hash
        if matched_hash in _multimodal_cache_access_order:
            _multimodal_cache_access_order.remove(matched_hash)
        _multimodal_cache_access_order.append(matched_hash)
        # Track hit and tokens matched
        _kv_cache_hits += 1
        _kv_cache_tokens_matched += match_len
        if is_cross_image_match:
            _kv_cache_cross_image_hits += 1
            # Debug output already printed above
        elif MULTIMODAL_KV_DEBUG:
            print(f"[DEBUG] KV Cache HIT: matched {match_len} tokens")
    else:
        _kv_cache_misses += 1
        if MULTIMODAL_KV_DEBUG:
            print(f"[DEBUG] KV Cache MISS: no prefix match found across {len(_multimodal_prefix_cache)} image hashes")

    return kv_states, match_len, image_hash, is_position_truncated


def _find_first_image_position(token_ids: List[int]) -> int:
    """
    Find the position of the first image token in the sequence.

    Returns:
        Position of first <|vision_start|> token, or -1 if no images found.
    """
    try:
        return token_ids.index(QWEN3_VISION_START_TOKEN_ID)
    except ValueError:
        return -1  # No image tokens found


def cache_multimodal_kv_prefix(image_hash: str, token_ids, kv_states, num_tokens: int):
    """
    Cache KV states with prefix matching support.

    IMPORTANT: Call mx.eval() on kv_states before caching to materialize
    the tensors and break computation graph dependencies.

    Args:
        image_hash: Hash of the image (from get_cached_multimodal_kv_prefix)
        token_ids: Token IDs for the sequence
        kv_states: The KV cache states to store
        num_tokens: Number of tokens in the cached sequence
    """
    if not MULTIMODAL_KV_CACHE_ENABLED:
        return

    # Check TTL and clear expired cache (also updates last access time)
    _check_cache_ttl()

    # Convert to list if needed
    if hasattr(token_ids, 'tolist'):
        token_list = token_ids.reshape(-1).tolist()
    else:
        token_list = list(token_ids.reshape(-1))

    # Find first image position for position-based cross-image caching (Option 2)
    first_image_position = _find_first_image_position(token_list)

    # Initialize cache for this image if needed
    if image_hash not in _multimodal_prefix_cache:
        _multimodal_prefix_cache[image_hash] = []

    # Check if we already have this exact sequence cached
    for entry in _multimodal_prefix_cache[image_hash]:
        cached_tokens = entry[0]
        if cached_tokens == token_list:
            if MULTIMODAL_KV_DEBUG:
                print(f"[DEBUG] KV Cache: already cached sequence of {len(token_list)} tokens")
            return  # Already cached

    # Add new entry with first_image_position
    _multimodal_prefix_cache[image_hash].append((token_list, kv_states, num_tokens, first_image_position))
    if MULTIMODAL_KV_DEBUG:
        print(f"[DEBUG] KV Cache STORE: image={image_hash[:8]}, tokens={len(token_list)}, kv_layers={sum(1 for kv in kv_states if kv is not None)}, first_img_pos={first_image_position}")

    # Update LRU order
    if image_hash in _multimodal_cache_access_order:
        _multimodal_cache_access_order.remove(image_hash)
    _multimodal_cache_access_order.append(image_hash)

    # LRU eviction if at capacity (skip if MAX_SIZE=0 for unlimited)
    if MULTIMODAL_KV_CACHE_MAX_SIZE > 0:
        total_entries = sum(len(entries) for entries in _multimodal_prefix_cache.values())
        while total_entries > MULTIMODAL_KV_CACHE_MAX_SIZE and _multimodal_cache_access_order:
            oldest_hash = _multimodal_cache_access_order.pop(0)
            if oldest_hash in _multimodal_prefix_cache:
                # Remove oldest entry for this image
                if _multimodal_prefix_cache[oldest_hash]:
                    _multimodal_prefix_cache[oldest_hash].pop(0)
                    if not _multimodal_prefix_cache[oldest_hash]:
                        del _multimodal_prefix_cache[oldest_hash]
                total_entries = sum(len(entries) for entries in _multimodal_prefix_cache.values())


def clear_multimodal_kv_cache():
    """Clear all cached multimodal KV states."""
    global _multimodal_prefix_cache, _multimodal_cache_access_order, _multimodal_cache_last_access
    global _kv_cache_hits, _kv_cache_misses, _kv_cache_cross_image_hits, _kv_cache_tokens_matched, _kv_cache_tokens_total
    _multimodal_prefix_cache.clear()
    _multimodal_cache_access_order.clear()
    _multimodal_cache_last_access = 0.0
    _kv_cache_hits = 0
    _kv_cache_misses = 0
    _kv_cache_cross_image_hits = 0
    _kv_cache_tokens_matched = 0
    _kv_cache_tokens_total = 0


def get_multimodal_kv_cache_stats() -> Dict[str, Any]:
    """Get multimodal KV cache statistics."""
    import time
    total_entries = sum(len(entries) for entries in _multimodal_prefix_cache.values())

    # Calculate time until expiry
    if MULTIMODAL_KV_CACHE_TTL_SECONDS > 0 and _multimodal_cache_last_access > 0:
        elapsed = time.time() - _multimodal_cache_last_access
        ttl_remaining = max(0, MULTIMODAL_KV_CACHE_TTL_SECONDS - elapsed)
    else:
        ttl_remaining = None

    # Calculate hit rate
    total_lookups = _kv_cache_hits + _kv_cache_misses
    hit_rate = (_kv_cache_hits / total_lookups * 100) if total_lookups > 0 else 0.0
    token_reuse_rate = (_kv_cache_tokens_matched / _kv_cache_tokens_total * 100) if _kv_cache_tokens_total > 0 else 0.0

    return {
        "enabled": MULTIMODAL_KV_CACHE_ENABLED,
        "num_images": len(_multimodal_prefix_cache),
        "total_entries": total_entries,
        "max_size": "unlimited" if MULTIMODAL_KV_CACHE_MAX_SIZE == 0 else MULTIMODAL_KV_CACHE_MAX_SIZE,
        "ttl_seconds": "disabled" if MULTIMODAL_KV_CACHE_TTL_SECONDS <= 0 else MULTIMODAL_KV_CACHE_TTL_SECONDS,
        "ttl_remaining": ttl_remaining,
        "image_hashes": list(_multimodal_prefix_cache.keys()),
        # Hit/miss tracking
        "hits": _kv_cache_hits,
        "misses": _kv_cache_misses,
        "cross_image_hits": _kv_cache_cross_image_hits,
        "hit_rate": round(hit_rate, 1),
        "tokens_matched": _kv_cache_tokens_matched,
        "tokens_total": _kv_cache_tokens_total,
        "token_reuse_rate": round(token_reuse_rate, 1),
    }


# =============================================================================
# Pixel Values Preprocessing Cache (Production Caching - Option 1)
# =============================================================================
# Caches the preprocessed pixel_values tensor to skip image loading/preprocessing
# on repeated requests with the same image. This addresses the gap where image
# preprocessing (~30-60ms) runs on every request even with KV caching.
#
# Key insight: Cloud APIs (Claude Files API, OpenAI) separate "upload/preprocess"
# from "use in conversation". This cache provides similar benefits locally.

PIXEL_VALUES_CACHE_ENABLED = True
PIXEL_VALUES_CACHE_MAX_SIZE = 50  # Cache up to 50 different images
PIXEL_VALUES_CACHE_TTL_SECONDS = 300  # 5 minutes TTL (0 = no expiry)
PIXEL_VALUES_CACHE_DEBUG = False  # Set True to enable debug logging for cache operations

# Cache structure: {source_hash: (pixel_values, timestamp, original_size)}
_pixel_values_cache: Dict[str, Tuple[Any, float, Tuple[int, int]]] = {}
_pixel_values_cache_order: List[str] = []  # LRU order

# PIL Image Cache (forward declaration, used in load_image)
_pil_image_cache: Dict[str, Any] = {}  # source_hash -> PIL Image


def _hash_image_source(source: str) -> str:
    """
    Hash an image source (path, URL, or base64) for cache lookup.

    For base64: Use first 2000 chars (enough for uniqueness, fast to hash)
    For paths/URLs: Hash the full string
    """
    import hashlib
    if len(source) > 2000:
        # Base64 or very long URL - hash prefix
        return hashlib.md5(source[:2000].encode()).hexdigest()
    return hashlib.md5(source.encode()).hexdigest()


def get_cached_pixel_values(source: str) -> Optional[Tuple[Any, Tuple[int, int]]]:
    """
    Get cached preprocessed pixel_values if available.

    Args:
        source: Image source (file path, URL, or base64 string)

    Returns:
        Tuple of (pixel_values, original_size) if cached, None otherwise
    """
    if not PIXEL_VALUES_CACHE_ENABLED:
        return None

    import time
    cache_key = _hash_image_source(source)

    if cache_key not in _pixel_values_cache:
        if PIXEL_VALUES_CACHE_DEBUG:
            print(f"[PIXEL CACHE] MISS: {cache_key[:8]}... (source: {source[:50]}...)")
        return None

    pixel_values, timestamp, original_size = _pixel_values_cache[cache_key]

    # Check TTL
    if PIXEL_VALUES_CACHE_TTL_SECONDS > 0:
        elapsed = time.time() - timestamp
        if elapsed > PIXEL_VALUES_CACHE_TTL_SECONDS:
            # Expired - remove from cache
            _pixel_values_cache.pop(cache_key, None)
            if cache_key in _pixel_values_cache_order:
                _pixel_values_cache_order.remove(cache_key)
            if PIXEL_VALUES_CACHE_DEBUG:
                print(f"[PIXEL CACHE] EXPIRED: {cache_key[:8]}... (elapsed: {elapsed:.1f}s)")
            return None

    # LRU update
    if cache_key in _pixel_values_cache_order:
        _pixel_values_cache_order.remove(cache_key)
    _pixel_values_cache_order.append(cache_key)

    if PIXEL_VALUES_CACHE_DEBUG:
        print(f"[PIXEL CACHE] HIT: {cache_key[:8]}... (size: {original_size})")

    return pixel_values, original_size


def cache_pixel_values(source: str, pixel_values: Any, original_size: Tuple[int, int]):
    """
    Cache preprocessed pixel_values for an image source.

    Args:
        source: Image source (file path, URL, or base64 string)
        pixel_values: Preprocessed pixel values tensor
        original_size: Original image size (height, width)
    """
    if not PIXEL_VALUES_CACHE_ENABLED:
        return

    import time
    cache_key = _hash_image_source(source)

    # LRU eviction if at capacity
    while PIXEL_VALUES_CACHE_MAX_SIZE > 0 and len(_pixel_values_cache) >= PIXEL_VALUES_CACHE_MAX_SIZE:
        if _pixel_values_cache_order:
            oldest = _pixel_values_cache_order.pop(0)
            _pixel_values_cache.pop(oldest, None)
            if PIXEL_VALUES_CACHE_DEBUG:
                print(f"[PIXEL CACHE] EVICT: {oldest[:8]}...")
        else:
            break

    # Evaluate tensor before caching (break computation graph)
    mx.eval(pixel_values)

    _pixel_values_cache[cache_key] = (pixel_values, time.time(), original_size)
    _pixel_values_cache_order.append(cache_key)

    if PIXEL_VALUES_CACHE_DEBUG:
        print(f"[PIXEL CACHE] STORE: {cache_key[:8]}... (size: {original_size}, shape: {pixel_values.shape})")


def clear_pixel_values_cache():
    """Clear all cached pixel values and PIL images."""
    global _pixel_values_cache, _pixel_values_cache_order, _pil_image_cache
    global _pil_cache_hits, _pil_cache_misses
    _pixel_values_cache.clear()
    _pixel_values_cache_order.clear()
    _pil_image_cache.clear()
    _pil_cache_hits = 0
    _pil_cache_misses = 0
    if PIXEL_VALUES_CACHE_DEBUG:
        print("[PIXEL CACHE] CLEARED (pixel_values + PIL images)")


def get_pixel_values_cache_stats() -> Dict[str, Any]:
    """Get pixel values cache statistics."""
    import time

    # Calculate TTL remaining for each entry
    entries_info = []
    current_time = time.time()
    for key, (pv, timestamp, size) in _pixel_values_cache.items():
        if PIXEL_VALUES_CACHE_TTL_SECONDS > 0:
            ttl_remaining = max(0, PIXEL_VALUES_CACHE_TTL_SECONDS - (current_time - timestamp))
        else:
            ttl_remaining = None
        entries_info.append({
            "key": key[:8],
            "size": size,
            "shape": tuple(pv.shape) if hasattr(pv, 'shape') else None,
            "ttl_remaining": ttl_remaining,
        })

    return {
        "enabled": PIXEL_VALUES_CACHE_ENABLED,
        "size": len(_pixel_values_cache),
        "max_size": PIXEL_VALUES_CACHE_MAX_SIZE,
        "ttl_seconds": PIXEL_VALUES_CACHE_TTL_SECONDS,
        "entries": entries_info,
    }


def get_pil_cache_stats() -> Dict[str, Any]:
    """Get PIL image cache statistics."""
    total_lookups = _pil_cache_hits + _pil_cache_misses
    hit_rate = (_pil_cache_hits / total_lookups * 100) if total_lookups > 0 else 0.0

    return {
        "size": len(_pil_image_cache),
        "max_size": _pil_image_cache_max_size,
        "hits": _pil_cache_hits,
        "misses": _pil_cache_misses,
        "hit_rate": round(hit_rate, 1),
    }


# Legacy compatibility - keep old functions working
def _hash_multimodal_input(pixel_values, input_ids) -> str:
    """Legacy: Create a hash key for exact match (deprecated, use prefix matching)."""
    import hashlib
    image_hash = _hash_pixel_values(pixel_values)
    if hasattr(input_ids, 'tolist'):
        token_list = input_ids.reshape(-1).tolist()
    else:
        token_list = list(input_ids.reshape(-1))
    prefix_tokens = token_list[:100]
    text_hash = hashlib.md5(str(prefix_tokens).encode()).hexdigest()[:8]
    return f"{image_hash}_{text_hash}_{len(token_list)}"


def get_cached_multimodal_kv(pixel_values, input_ids, cache_key: str = None):
    """Legacy: Get cached KV states (exact match only, deprecated)."""
    kv_states, match_len, _ = get_cached_multimodal_kv_prefix(pixel_values, input_ids)
    if hasattr(input_ids, 'size'):
        total_tokens = input_ids.size
    else:
        total_tokens = len(input_ids.reshape(-1))
    # Only return if exact match
    if match_len == total_tokens:
        return kv_states, match_len
    return None, 0


def cache_multimodal_kv(pixel_values, input_ids, kv_states, num_tokens: int, cache_key: str = None):
    """Legacy: Cache KV states (deprecated, use cache_multimodal_kv_prefix)."""
    image_hash = _get_image_hash(pixel_values)
    cache_multimodal_kv_prefix(image_hash, input_ids, kv_states, num_tokens)


import mlx.core as mx
import mlx.nn as nn
import numpy as np
import requests
# Audio support is optional (only needed for audio models)
try:
    import soundfile as sf
except ImportError:
    sf = None
from huggingface_hub import snapshot_download
from mlx.utils import tree_flatten
from PIL import Image, ImageOps
from transformers import AutoProcessor, PreTrainedTokenizer, PreTrainedTokenizerFast

from ..models.base import BaseImageProcessor
from .tokenizer_utils import load_tokenizer

# Optional LoRA support
try:
    from mlx_vlm.trainer import apply_lora_layers
except ImportError:
    def apply_lora_layers(model, adapter_path):
        raise ImportError("LoRA support requires mlx-vlm with training support")

# Constants
MODEL_REMAPPING = {
    "llava_qwen2": "fastvlm",  # Apple's FastVLM, note it's different to the one below
    "llava-qwen2": "llava_bunny",
    "bunny-llama": "llava_bunny",
    "lfm2-vl": "lfm2_vl",
    "cohere2_vision": "aya_vision",
    "jvlm": "jina_vlm",
}

MAX_FILE_SIZE_GB = 5

MODEL_CONVERSION_DTYPES = ["float16", "bfloat16", "float32"]


def skip_multimodal_module(path: str) -> bool:
    """
    Check if a multimodal module (vision/audio) should skip quantization.

    Args:
        path: The module path to check

    Returns:
        bool: True if the module is multimodal and should skip quantization, False otherwise
    """
    return (
        "vision_model" in path
        or "vision_tower" in path
        or "vl_connector" in path
        or "sam_model" in path
        or "audio_model" in path
        or "audio_tower" in path
        or "code_predictor" in path
    )


def get_model_and_args(config: dict):
    """
    Retrieve the model object based on the configuration.

    Args:
        config (dict): The model configuration.

    Returns:
        A tuple containing the Model class and the ModelArgs class.
    """
    model_type = config["model_type"].lower()

    model_type = MODEL_REMAPPING.get(model_type, model_type)

    # First, try to load from questmind.models (our integrated models)
    try:
        arch = importlib.import_module(f"questmind.models.{model_type}")
        return arch, model_type
    except ImportError:
        pass

    # Fall back to mlx_vlm.models for other model types
    try:
        arch = importlib.import_module(f"mlx_vlm.models.{model_type}")
    except ImportError:
        msg = f"Model type {model_type} not supported."
        logging.error(msg)
        raise ValueError(msg)

    return arch, model_type


def get_model_path(
    path_or_hf_repo: str, revision: Optional[str] = None, force_download: bool = False
) -> Path:
    """
    Ensures the model is available locally. If the path does not exist locally,
    it is downloaded from the Hugging Face Hub.

    Args:
        path_or_hf_repo (str): The local path or Hugging Face repository ID of the model.
        revision (str, optional): A revision id which can be a branch name, a tag, or a commit hash.

    Returns:
        Path: The path to the model.
    """
    model_path = Path(path_or_hf_repo)
    if not model_path.exists():
        model_path = Path(
            snapshot_download(
                repo_id=path_or_hf_repo,
                revision=revision,
                allow_patterns=[
                    "*.json",
                    "*.safetensors",
                    "*.py",
                    "*.model",
                    "*.tiktoken",
                    "*.txt",
                    "*.jinja",
                ],
                force_download=force_download,
            )
        )
    return model_path


def load_model(model_path: Path, lazy: bool = False, **kwargs) -> nn.Module:
    """
    Load and initialize the model from a given path.

    Args:
        model_path (Path): The path to load the model from.
        lazy (bool): If False eval the model parameters to make sure they are
            loaded in memory before returning, otherwise they will be loaded
            when needed. Default: ``False``
        revision (str, optional): A revision id which can be a branch name,
            a tag, or a commit hash. Default: ``None``.

    Returns:
        nn.Module: The loaded and initialized model.

    Raises:
        FileNotFoundError: If the weight files (.safetensors) are not found.
        ValueError: If the model class or args class are not found or cannot be instantiated.
    """
    config = load_config(model_path, **kwargs)
    quantization = config.get("quantization", None)

    # Find all .safetensors files in the model_path, excluding consolidated model weights
    weight_files = [
        wf
        for wf in glob.glob(str(model_path / "*.safetensors"))
        if not wf.endswith("consolidated.safetensors")
    ]

    if not weight_files:
        logging.error(f"No safetensors found in {model_path}")
        message = f"""
No safetensors found in {model_path}
Create safetensors using the following code:
```
from transformers import AutoModelForCausalLM, AutoProcessor

model_id= "<huggingface_model_id>"
model = AutoModelForCausalLM.from_pretrained(model_id)
processor = AutoProcessor.from_pretrained(model_id)

model.save_pretrained("<local_dir>")
processor.save_pretrained("<local_dir>")
```
Then use the <local_dir> as the --hf-path in the convert script.
```
python -m mlx_vlm.convert --hf-path <local_dir> --mlx-path <mlx_dir>
```
        """
        raise FileNotFoundError(message)

    weights = {}
    for wf in weight_files:
        weights.update(mx.load(wf))

    import safetensors

    with safetensors.safe_open(weight_files[0], framework="np") as f:
        is_mlx_format = f.metadata() and f.metadata().get("format") == "mlx"

    model_class, _ = get_model_and_args(config=config)

    # Initialize text and vision configs if not present
    config.setdefault("text_config", {})
    config.setdefault("vision_config", {})
    config.setdefault("audio_config", {})

    # Initialize model config and update it with module configs
    model_config = model_class.ModelConfig.from_dict(config)
    modules = ["text", "vision", "perceiver", "projector", "audio"]
    model_config = update_module_configs(model_config, model_class, config, modules)

    model = model_class.Model(model_config)

    if not is_mlx_format:
        # Sanitize weights
        weights = sanitize_weights(model, weights)

        if hasattr(model, "thinker") and hasattr(model.thinker, "sanitize"):
            weights = sanitize_weights(model.thinker, weights)
            weights = sanitize_weights(model.thinker.vision_tower, weights)
            weights = sanitize_weights(model.thinker.audio_tower, weights)
            weights = sanitize_weights(model.thinker.language_model, weights)
            weights = sanitize_weights(model.code2wav, weights)
            weights = sanitize_weights(model.talker, weights)
        else:
            weights = sanitize_weights(
                model_class.VisionModel, weights, model_config.vision_config
            )
            weights = sanitize_weights(
                model_class.LanguageModel, weights, model_config.text_config
            )
            if hasattr(model_class, "AudioModel"):
                weights = sanitize_weights(
                    model_class.AudioModel, weights, model_config.audio_config
                )

    if (quantization := config.get("quantization", None)) is not None:
        # Handle legacy models which may or may not have vision quantized
        # TODO: Re-upload the models with the new quantization config and remove this
        skip_vision = config.get("vision_config", {}).get("skip_vision", False)

        def get_class_predicate(p, m):
            # Always skip vision and audio models
            if skip_multimodal_module(p) and skip_vision:
                return False
            # Handle custom per layer quantizations
            if p in config["quantization"]:
                return config["quantization"][p]
            if not hasattr(m, "to_quantized"):
                return False
            # Skip layers not divisible by 64
            if hasattr(m, "weight") and m.weight.size % 64 != 0:
                return False
            # Handle legacy models which may not have everything quantized
            return f"{p}.scales" in weights

        nn.quantize(
            model,
            group_size=quantization["group_size"],
            bits=quantization["bits"],
            mode=quantization.get("mode", "affine"),
            class_predicate=get_class_predicate,
        )

    model.load_weights(list(weights.items()))
    if not lazy:
        mx.eval(model.parameters())

    model.eval()
    return model


def sanitize_weights(model_obj, weights, config=None):
    """Helper function to sanitize weights if the model has a sanitize method"""
    if hasattr(model_obj, "sanitize"):
        if config is not None:
            model_obj = model_obj(config)
        weights = model_obj.sanitize(weights)
    return weights


def update_module_configs(model_config, model_class, config, modules):
    """Updates configuration for model modules like text and vision modules.

    Args:
        model_config: The model configuration object that will be updated
        model_class: The model class containing component config classes
        config: Dictionary containing configuration parameters
        modules: List of module names to update configs for (e.g. ["text", "vision"])

    Returns:
        The updated model_config object
    """
    for config_name in modules:
        config_attr = f"{config_name}_config"
        if hasattr(model_config, config_attr):
            config_class = getattr(model_class, f"{config_name.title()}Config")
            setattr(
                model_config, config_attr, config_class.from_dict(config[config_attr])
            )
    return model_config


def load(
    path_or_hf_repo: str,
    adapter_path: Optional[str] = None,
    lazy: bool = False,
    revision: Optional[str] = None,
    **kwargs,
) -> Tuple[nn.Module, Union[PreTrainedTokenizer, PreTrainedTokenizerFast]]:
    """
    Load the model and tokenizer from a given path or a huggingface repository.

    Args:
        path_or_hf_repo (Path): The path or the huggingface repository to load the model from.
        tokenizer_config (dict, optional): Configuration parameters specifically for the tokenizer.
            Defaults to an empty dictionary.
        adapter_path (str, optional): Path to the LoRA adapters. If provided, applies LoRA layers
            to the model. Default: ``None``.
        lazy (bool): If False eval the model parameters to make sure they are
            loaded in memory before returning, otherwise they will be loaded
            when needed. Default: ``False``
        revision (str, optional): A revision id which can be a branch name,
            a tag, or a commit hash. Default: ``None``.
    Returns:
        Tuple[nn.Module, TokenizerWrapper]: A tuple containing the loaded model and tokenizer.

    Raises:
        FileNotFoundError: If config file or safetensors are not found.
        ValueError: If model class or args class are not found.
    """
    force_download = kwargs.get("force_download", False)
    model_path = get_model_path(
        path_or_hf_repo, force_download=force_download, revision=revision
    )
    model = load_model(model_path, lazy, **kwargs)
    if adapter_path is not None:
        model = apply_lora_layers(model, adapter_path)
        model.eval()

    image_processor = load_image_processor(model_path, **kwargs)

    # Get the eos_token_id from the model config
    eos_token_id = getattr(model.config, "eos_token_id", None)

    processor = load_processor(model_path, True, eos_token_ids=eos_token_id, **kwargs)

    if image_processor is not None:
        processor.image_processor = image_processor

    return model, processor


def load_config(model_path: Union[str, Path], **kwargs) -> dict:
    """Load model configuration from a path or Hugging Face repo.

    Args:
        model_path: Local path or Hugging Face repo ID to load config from
        **kwargs: Additional keyword arguments to pass to the config loader

    Returns:
        dict: Model configuration

    Raises:
        FileNotFoundError: If config.json is not found at the path
    """
    if isinstance(model_path, str):
        model_path = get_model_path(model_path)

    try:
        with open(model_path / "config.json", encoding="utf-8") as f:
            config = json.load(f)

        generation_config_file = model_path / "generation_config.json"
        if generation_config_file.exists():
            generation_config = {}
            try:
                with open(generation_config_file, "r") as f:
                    generation_config = json.load(f)
            except json.JSONDecodeError:
                pass

            if eos_token_id := generation_config.get("eos_token_id", False):
                config["eos_token_id"] = eos_token_id

        return config

    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Config not found at {model_path}") from exc


def load_image_processor(model_path: Union[str, Path], **kwargs) -> BaseImageProcessor:
    if isinstance(model_path, str):
        model_path = get_model_path(model_path)

    if not kwargs:
        config = load_config(model_path, trust_remote_code=True)
    else:
        config = load_config(model_path, **kwargs)

    model_class, _ = get_model_and_args(config)
    image_processor = None

    if hasattr(model_class, "ImageProcessor"):
        init_signature = inspect.signature(model_class.ImageProcessor.__init__)

        if "config" in init_signature.parameters:
            image_processor = model_class.ImageProcessor(config=config)
        else:
            image_processor = model_class.ImageProcessor()

    return image_processor


def load_processor(
    model_path, add_detokenizer=True, eos_token_ids=None, **kwargs
) -> Union[PreTrainedTokenizer, PreTrainedTokenizerFast]:

    processor = AutoProcessor.from_pretrained(model_path, use_fast=True, **kwargs)
    if add_detokenizer:
        detokenizer_class = load_tokenizer(model_path, return_tokenizer=False)

        # Get the tokenizer object
        tokenizer_obj = (
            processor.tokenizer if hasattr(processor, "tokenizer") else processor
        )

        # Instantiate the detokenizer
        processor.detokenizer = detokenizer_class(tokenizer_obj)

        # Determine the EOS token IDs, prioritizing the function argument
        final_eos_token_ids = (
            eos_token_ids if eos_token_ids is not None else tokenizer_obj.eos_token_ids
        )

        # Create and assign the StoppingCriteria
        criteria = StoppingCriteria(final_eos_token_ids, tokenizer_obj)
        if hasattr(processor, "tokenizer"):
            processor.tokenizer.stopping_criteria = criteria
        else:
            processor.stopping_criteria = criteria

    return processor


def fetch_from_hub(
    model_path: Path, lazy: bool = False, **kwargs
) -> Tuple[nn.Module, dict, PreTrainedTokenizer]:
    model = load_model(model_path, lazy, **kwargs)
    config = load_config(model_path, **kwargs)
    processor = load_processor(
        model_path,
        add_detokenizer=False,
        eos_token_ids=config.get("eos_token_id", None),
        **kwargs,
    )
    return model, config, processor


def make_shards(weights: dict, max_file_size_gb: int = MAX_FILE_SIZE_GB) -> list:
    """
    Splits the weights into smaller shards.

    Args:
        weights (dict): Model weights.
        max_file_size_gb (int): Maximum size of each shard in gigabytes.

    Returns:
        list: List of weight shards.
    """
    max_file_size_bytes = max_file_size_gb << 30
    shards = []
    shard, shard_size = {}, 0
    for k, v in weights.items():
        if shard_size + v.nbytes > max_file_size_bytes:
            shards.append(shard)
            shard, shard_size = {}, 0
        shard[k] = v
        shard_size += v.nbytes
    shards.append(shard)
    return shards


def upload_to_hub(path: str, upload_repo: str, hf_path: str):
    """
    Uploads the model to Hugging Face hub.

    Args:
        path (str): Local path to the model.
        upload_repo (str): Name of the HF repo to upload to.
        hf_path (str): Path to the original Hugging Face model.
    """
    import os

    from huggingface_hub import HfApi, ModelCard, logging

    from . import __version__

    card = ModelCard.load(hf_path)
    card.data.tags = ["mlx"] if card.data.tags is None else card.data.tags + ["mlx"]
    card.text = dedent(
        f"""
        # {upload_repo}
        This model was converted to MLX format from [`{hf_path}`]() using mlx-vlm version **{__version__}**.
        Refer to the [original model card](https://huggingface.co/{hf_path}) for more details on the model.
        ## Use with mlx

        ```bash
        pip install -U mlx-vlm
        ```

        ```bash
        python -m mlx_vlm.generate --model {upload_repo} --max-tokens 100 --temperature 0.0 --prompt "Describe this image." --image <path_to_image>
        ```
        """
    )
    card.save(os.path.join(path, "README.md"))

    logging.set_verbosity_info()

    api = HfApi()
    api.create_repo(repo_id=upload_repo, exist_ok=True)
    api.upload_folder(
        folder_path=path,
        repo_id=upload_repo,
        repo_type="model",
    )
    print(f"Upload successful, go to https://huggingface.co/{upload_repo} for details.")


def apply_repetition_penalty(logits: mx.array, generated_tokens: Any, penalty: float):
    """
    Apply repetition penalty to specific logits based on the given context.

    Paper: https://arxiv.org/abs/1909.05858

    Args:
        logits (mx.array): The logits produced by the language model.
        generated_tokens (any): A list of N previous tokens.
        penalty (float): The repetition penalty factor to be applied.

    Returns:
        logits (mx.array): Logits with repetition penalty applied to generated tokens.
    """
    if len(generated_tokens) > 0:
        indices = mx.array([token for token in generated_tokens])
        selected_logits = logits[:, indices]
        selected_logits = mx.where(
            selected_logits < 0, selected_logits * penalty, selected_logits / penalty
        )
        logits[:, indices] = selected_logits
    return logits


def save_weights(
    save_path: Union[str, Path],
    model: nn.Module,
    *,
    donate_weights: bool = False,
) -> None:
    """Save model weights into specified directory."""
    if isinstance(save_path, str):
        save_path = Path(save_path)

    weights = dict(tree_flatten(model.parameters()))
    del model

    save_path.mkdir(parents=True, exist_ok=True)

    shards = make_shards(weights)
    shards_count = len(shards)
    shard_file_format = (
        "model-{:05d}-of-{:05d}.safetensors"
        if shards_count > 1
        else "model.safetensors"
    )

    total_size = sum(v.nbytes for v in weights.values())
    index_data = {"metadata": {"total_size": total_size}, "weight_map": {}}

    # Write the weights and make sure no references are kept other than the
    # necessary ones
    if donate_weights:
        weights.clear()
        del weights

    for i in range(len(shards)):
        shard = shards[i]
        shards[i] = None
        shard_name = shard_file_format.format(i + 1, shards_count)
        shard_path = save_path / shard_name

        mx.save_safetensors(str(shard_path), shard, metadata={"format": "mlx"})

        for weight_name in shard.keys():
            index_data["weight_map"][weight_name] = shard_name
        del shard

    index_data["weight_map"] = {
        k: index_data["weight_map"][k] for k in sorted(index_data["weight_map"])
    }

    with open(save_path / "model.safetensors.index.json", "w") as f:
        json.dump(
            index_data,
            f,
            indent=4,
        )


def save_config(
    config: dict,
    config_path: Union[str, Path],
) -> None:
    """Save the model configuration to the ``config_path``.

    The final configuration will be sorted before saving for better readability.

    Args:
        config (dict): The model configuration.
        config_path (Union[str, Path]): Model configuration file path.
    """
    # Clean unused keys
    config.pop("_name_or_path", None)
    config.pop("torch_dtype", None)

    # sort the config for better readability
    config = dict(sorted(config.items()))

    # write the updated config to the config_path (if provided)
    with open(config_path, "w") as fid:
        json.dump(config, fid, indent=4)


# PIL Image Cache (for skipping disk/network I/O on repeated requests)
_pil_image_cache: Dict[str, Image.Image] = {}
_pil_image_cache_max_size = 20  # Keep 20 most recent images
_pil_cache_hits: int = 0
_pil_cache_misses: int = 0


def load_image(image_source: Union[str, Path, BytesIO], timeout: int = 10):
    """
    Helper function to load an image from either a URL or file.
    Caches PIL images to skip disk/network I/O on repeated requests.
    """
    global _pil_cache_hits, _pil_cache_misses

    # Check PIL image cache for string sources
    cache_key = None
    if isinstance(image_source, str) and PIXEL_VALUES_CACHE_ENABLED:
        cache_key = _hash_image_source(image_source)
        if cache_key in _pil_image_cache:
            if PIXEL_VALUES_CACHE_DEBUG:
                print(f"[PIL CACHE] HIT: {cache_key[:8]}...")
            _pil_cache_hits += 1
            # Return a copy to avoid mutations
            return _pil_image_cache[cache_key].copy()

    if (
        isinstance(image_source, BytesIO)
        or (isinstance(image_source, str) and image_source.startswith("data:image/"))
        or Path(image_source).is_file()
    ):
        # for base64 encoded images
        try:
            if image_source.startswith("data:image/"):
                import base64

                if "," not in image_source:
                    raise ValueError(
                        "Invalid data URI format - missing comma separator"
                    )

                _, data = image_source.split(",", 1)
                image_source = BytesIO(base64.b64decode(data))

            image = Image.open(image_source)
        except IOError as e:
            raise ValueError(
                f"Failed to load image from {image_source} with error: {e}"
            ) from e
    elif image_source.startswith(("http://", "https://")):
        try:
            response = requests.get(image_source, stream=True, timeout=timeout)
            response.raise_for_status()
            image = Image.open(response.raw)
        except Exception as e:
            raise ValueError(
                f"Failed to load image from URL: {image_source} with error {e}"
            ) from e
    else:
        raise ValueError(
            f"The image {image_source} must be a valid URL or existing file."
        )

    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")

    # Cache PIL image for future requests
    if cache_key is not None and PIXEL_VALUES_CACHE_ENABLED:
        _pil_cache_misses += 1  # Track miss (we loaded fresh)
        # LRU eviction
        while len(_pil_image_cache) >= _pil_image_cache_max_size:
            oldest_key = next(iter(_pil_image_cache))
            del _pil_image_cache[oldest_key]
        _pil_image_cache[cache_key] = image.copy()
        if PIXEL_VALUES_CACHE_DEBUG:
            print(f"[PIL CACHE] STORE: {cache_key[:8]}... (size: {image.size})")

    return image


def resize_image(img, max_size):

    ratio = min(max_size[0] / img.width, max_size[1] / img.height)
    new_size = (int(img.width * ratio), int(img.height * ratio))
    return img.resize(new_size)


def process_image(img, resize_shape, image_processor):
    if isinstance(img, str):
        img = load_image(img)
    if resize_shape is not None and not isinstance(image_processor, BaseImageProcessor):
        img = resize_image(img, resize_shape)
    return img


def _load_single_image(args):
    """
    Helper function for parallel image loading.
    Returns (index, pil_image, original_size) tuple.
    """
    idx, img, resize_shape, image_processor = args
    try:
        if isinstance(img, str):
            pil_img = process_image(img, resize_shape, image_processor)
        elif isinstance(img, Image.Image):
            pil_img = img
        else:
            pil_img = img

        # Get original size
        if hasattr(pil_img, "height"):
            original_size = (pil_img.height, pil_img.width)
        else:
            original_size = (0, 0)

        return (idx, pil_img, original_size, None)
    except Exception as e:
        return (idx, None, (0, 0), str(e))


def load_images_parallel(
    images: List[Any],
    image_processor: Any = None,
    resize_shape: Optional[Tuple[int, int]] = None,
    max_workers: Optional[int] = None,
) -> Tuple[List[Any], List[Tuple[int, int]]]:
    """
    Load and preprocess multiple images in parallel using ThreadPoolExecutor.

    This provides significant TTFT (Time To First Token) improvement for:
    - Multiple images in a batch
    - Images loaded from URLs (I/O bound)
    - Large images requiring preprocessing (CPU bound)

    Args:
        images: List of image sources (paths, URLs, PIL Images, or base64 strings)
        image_processor: Optional image processor for preprocessing
        resize_shape: Optional resize dimensions
        max_workers: Number of worker threads. None = auto, 0 = sequential (no parallelism)

    Returns:
        Tuple of (processed_images, original_sizes)

    Example:
        >>> from questmind.inference import utils
        >>> utils.PARALLEL_IMAGE_WORKERS = 4  # Use 4 threads
        >>> images, sizes = utils.load_images_parallel(["img1.jpg", "img2.jpg"])
    """
    if not images:
        return [], []

    # Determine worker count
    if max_workers is None:
        max_workers = PARALLEL_IMAGE_WORKERS

    # If parallelism is disabled or only one image, use sequential loading
    if max_workers == 0 or len(images) == 1:
        processed_images = []
        image_sizes_original = []
        for img in images:
            if isinstance(img, str):
                pil_img = process_image(img, resize_shape, image_processor)
            elif isinstance(img, Image.Image):
                pil_img = img
            else:
                pil_img = img
            processed_images.append(pil_img)
            if hasattr(pil_img, "height"):
                image_sizes_original.append((pil_img.height, pil_img.width))
            else:
                image_sizes_original.append((0, 0))
        return processed_images, image_sizes_original

    # Prepare arguments for parallel execution
    args_list = [
        (idx, img, resize_shape, image_processor)
        for idx, img in enumerate(images)
    ]

    # Execute in parallel
    processed_images = [None] * len(images)
    image_sizes_original = [(0, 0)] * len(images)
    errors = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_load_single_image, args): args[0] for args in args_list}

        for future in as_completed(futures):
            idx, pil_img, original_size, error = future.result()
            if error:
                errors.append(f"Image {idx}: {error}")
            else:
                processed_images[idx] = pil_img
                image_sizes_original[idx] = original_size

    # Raise if any errors occurred
    if errors:
        raise ValueError(f"Failed to load images: {'; '.join(errors)}")

    return processed_images, image_sizes_original


def resample_audio(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """Resample audio using linear interpolation."""
    if orig_sr == target_sr:
        return audio

    # Calculate the resampling ratio
    ratio = target_sr / orig_sr

    # Handle different audio shapes
    if audio.ndim == 1:
        # Mono audio - simple case
        new_length = int(len(audio) * ratio)
        old_indices = np.arange(len(audio))
        new_indices = np.linspace(0, len(audio) - 1, new_length)
        resampled = np.interp(new_indices, old_indices, audio)

    elif audio.ndim == 2:
        # Multi-channel audio - transpose to (samples, channels) if needed
        if audio.shape[0] < audio.shape[1]:
            audio = audio.T

        # Resample each channel
        n_samples, n_channels = audio.shape
        new_length = int(n_samples * ratio)
        old_indices = np.arange(n_samples)
        new_indices = np.linspace(0, n_samples - 1, new_length)

        resampled = np.zeros((new_length, n_channels))
        for i in range(n_channels):
            resampled[:, i] = np.interp(new_indices, old_indices, audio[:, i])
    else:
        raise ValueError(f"Audio array has unsupported shape: {audio.shape}")

    return resampled


def load_audio(
    file: str,
    sr: int,
    timeout: int = 10,
):
    """
    Helper function to load audio from either a URL or file.
    """
    if file.startswith(("http://", "https://")):
        try:
            response = requests.get(file, stream=True, timeout=timeout)
            response.raise_for_status()
            audio, sample_rate = sf.read(BytesIO(response.content), always_2d=True)
        except Exception as e:
            raise ValueError(
                f"Failed to load audio from URL: {file} with error {e}"
            ) from e
    else:
        audio, sample_rate = sf.read(file, always_2d=True)

    if sample_rate != sr:
        audio = resample_audio(audio, sample_rate, sr)
    return np.array(audio).mean(axis=1)


def process_inputs(
    processor,
    prompts,
    images=None,
    audio=None,
    add_special_tokens=False,
    padding=True,
    padding_side="left",
    return_tensors="mlx",
    **kwargs,
):
    # Get the process method from the processor
    process_method = getattr(processor, "process", processor)
    parameters = inspect.signature(process_method).parameters

    # Prepare arguments
    args = {
        "text": prompts,
        "images": images,
        "padding": padding,
        "return_tensors": return_tensors,
    }
    if "padding_side" in parameters:
        args["padding_side"] = padding_side

    # Add special tokens if supported
    if "add_special_tokens" in parameters:
        args["add_special_tokens"] = add_special_tokens

    for param in parameters.keys():
        if param in kwargs.keys():
            args[param] = kwargs.get(param, None)
            break

    # Add audio if provided and supported
    if audio is not None and len(audio) > 0:
        if "audio" in parameters:
            args["audio"] = audio
        else:
            raise ValueError(f"Processor {processor} does not support audio parameter")

    return process_method(**args)


def process_inputs_with_fallback(
    processor,
    prompts,
    images,
    audio,
    add_special_tokens=False,
    return_tensors="mlx",
    **kwargs,
):
    # First attempt with specified return_tensors
    try:
        return process_inputs(
            processor,
            prompts=prompts,
            images=images,
            audio=audio,
            add_special_tokens=add_special_tokens,
            return_tensors=return_tensors,
            **kwargs,
        )
    except Exception as e:
        # Fallback to PyTorch tensors if MLX fails
        if return_tensors != "pt":
            try:
                return process_inputs(
                    processor,
                    prompts=prompts,
                    images=images,
                    audio=audio,
                    add_special_tokens=add_special_tokens,
                    return_tensors="pt",
                    **kwargs,
                )
            except Exception as fallback_error:
                raise ValueError(
                    f"Failed to process inputs with error: {fallback_error}"
                ) from fallback_error

        raise ValueError(f"Failed to process inputs with error: {e}")


def prepare_inputs(
    processor,
    images=None,
    audio=None,
    prompts=None,
    image_token_index=None,
    resize_shape=None,
    add_special_tokens=False,
    padding=True,
    padding_side="left",
    pad_to_uniform_size=False,
    **kwargs,
):

    if not images and not audio:
        tokenizer = (
            processor.tokenizer if hasattr(processor, "tokenizer") else processor
        )
        # Ensure pad_token exists when padding text-only inputs
        if padding and tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        inputs = tokenizer(
            prompts,
            add_special_tokens=add_special_tokens,
            padding=padding,
            padding_side=padding_side,
        )
        input_ids = mx.array([inputs.input_ids])
        mask = mx.array([inputs.attention_mask])
        return {
            "input_ids": input_ids,
            "attention_mask": mask,
        }

    # Process images
    original_image_sources = None  # Track for pixel values caching
    if images is not None:
        if not isinstance(images, list):
            images = [images]

        # Save original sources for pixel values caching (before they become PIL images)
        original_image_sources = [
            img if isinstance(img, str) else None
            for img in images
        ]

        # Check pixel values cache BEFORE loading images (Production Caching Option 1)
        # This can skip expensive image loading entirely on cache hits
        cached_pixel_values_early = None
        can_use_early_cache = (
            PIXEL_VALUES_CACHE_ENABLED
            and original_image_sources
            and all(src is not None for src in original_image_sources)
            and len(original_image_sources) == 1
            # Only skip loading for BaseImageProcessor path (detected by checking processor type)
            and hasattr(processor, "image_processor")
            and isinstance(processor.image_processor, BaseImageProcessor)
        )

        if can_use_early_cache:
            cached = get_cached_pixel_values(original_image_sources[0])
            if cached is not None:
                cached_pixel_values_early, _ = cached
                if PIXEL_VALUES_CACHE_DEBUG:
                    print(f"[PIXEL CACHE] EARLY HIT - skipping image loading")

        image_processor = (
            processor.image_processor if hasattr(processor, "image_processor") else None
        )

        # Skip image loading if we have cached pixel_values (only for BaseImageProcessor path)
        if cached_pixel_values_early is None:
            # Use parallel loading for TTFT improvement (F3 optimization)
            images, _ = load_images_parallel(images, image_processor, resize_shape)
        else:
            # We have cached pixel_values, but still need a placeholder for control flow
            # The actual pixel_values will be injected later
            images = [None]  # Placeholder

        # For batching, we need uniform image sizes. Instead of padding to the
        # largest image (which adds white borders that hurt accuracy), we resize
        # all images to the model's expected input size.
        if len(images) > 1 and pad_to_uniform_size:
            # Get target size from image processor if available
            target_size = None
            if image_processor is not None and hasattr(image_processor, "size"):
                size = image_processor.size
                if isinstance(size, tuple):
                    target_size = size
                elif isinstance(size, dict):
                    target_size = (size.get("height", 384), size.get("width", 384))
                elif isinstance(size, int):
                    target_size = (size, size)

            if target_size is not None:
                # Resize all images to the target size
                resized_images = []
                for img in images:
                    if img.size != (
                        target_size[1],
                        target_size[0],
                    ):  # PIL uses (width, height)
                        img = img.resize(
                            (target_size[1], target_size[0]), Image.Resampling.BICUBIC
                        )
                    resized_images.append(img)
                images = resized_images
            else:
                # Fallback: pad to largest size (original behavior)
                max_width = max(img.width for img in images)
                max_height = max(img.height for img in images)

                padded_images = []
                for img in images:
                    if img.width != max_width or img.height != max_height:
                        padded_img = Image.new(
                            "RGB", (max_width, max_height), (255, 255, 255)
                        )
                        x_offset = (max_width - img.width) // 2
                        y_offset = (max_height - img.height) // 2
                        padded_img.paste(img, (x_offset, y_offset))
                        padded_images.append(padded_img)
                    else:
                        padded_images.append(img)
                images = padded_images

    # Process audio
    audio_inputs = None
    audio_feature_lengths = None
    is_qwen3_omni_moe = False
    processor_class_name = (
        processor.__class__.__name__ if hasattr(processor, "__class__") else ""
    )
    if (
        "qwen3" in processor_class_name.lower()
        and "omni" in processor_class_name.lower()
    ):
        is_qwen3_omni_moe = True

    if audio is not None and len(audio) > 0:
        if not isinstance(audio, list):
            audio = [audio]

        if len(audio) > 1:
            print(
                "\033[33mWarning\033[0m: Single prompt with multiple audio files is not supported yet. Using the first audio file.\n"
            )
            audio = audio[:1]

        if is_qwen3_omni_moe:
            audio_arrays = [
                load_audio(audio_file, sr=processor.feature_extractor.sampling_rate)
                for audio_file in audio
            ]
            audio_arrays = [
                audio_array.astype(np.float32) for audio_array in audio_arrays
            ]

            feature_extractor = getattr(processor, "feature_extractor", None)
            if feature_extractor is None:
                raise ValueError("Processor missing feature_extractor for audio prep.")

            audio_inputs = feature_extractor(
                audio_arrays,
                sampling_rate=feature_extractor.sampling_rate,
                padding=True,
                return_attention_mask=True,
            )

            audio_feature_lengths = np.sum(
                audio_inputs["attention_mask"], axis=-1, dtype=np.int32
            )
        else:
            feature_extractor = getattr(processor, "feature_extractor", None)
            if feature_extractor is not None:
                audio = [
                    load_audio(audio_file, sr=feature_extractor.sampling_rate)
                    for audio_file in audio
                ]
            else:
                audio = [
                    load_audio(audio_file, sr=processor.feature_extractor.sampling_rate)
                    for audio_file in audio
                ]

    model_inputs = {}

    # Check if processor is Qwen2VL/Qwen3VL type which uses a different image placeholder format
    # These processors have their own image token insertion logic and should use process_inputs_with_fallback
    processor_class_name = processor.__class__.__name__.lower()
    is_qwen_vl_processor = "qwen2vl" in processor_class_name or "qwen3vl" in processor_class_name

    # Check if prompts use <image> placeholder format
    prompts_list = [prompts] if not isinstance(prompts, list) else prompts
    uses_image_placeholder = any("<image>" in p for p in prompts_list) if prompts_list else False

    if hasattr(processor, "image_processor") and isinstance(
        processor.image_processor, BaseImageProcessor
    ) and uses_image_placeholder and not is_qwen_vl_processor:
        # This path is for processors that use <image> as the image placeholder
        # Qwen2VL/3VL and similar models use different format and should use process_inputs_with_fallback
        if not isinstance(prompts, list):
            prompts = [prompts]

        if processor.pad_token is None:
            processor.pad_token = processor.eos_token
        text_chunks = [
            [processor(chunk).input_ids for chunk in prompt.split("<image>")]
            for prompt in prompts
        ]

        # Find the maximum length for padding
        max_length = max(
            sum(len(chunk) for chunk in chunks) + 1 for chunks in text_chunks
        )

        # Pad and create input_ids
        input_ids = []
        for chunks in text_chunks:
            ids = chunks[0] + [image_token_index] + chunks[1]
            padding = [processor.pad_token_id] * (max_length - len(ids))
            input_ids.append(mx.array(ids + padding))

        model_inputs["input_ids"] = mx.array(input_ids)

        # Use early cached pixel_values if available (skipped image loading)
        if cached_pixel_values_early is not None:
            # Cache HIT - use cached pixel_values, already skipped image loading
            model_inputs["pixel_values"] = cached_pixel_values_early
        else:
            # Cache MISS - preprocess and cache
            pixel_values = processor.image_processor.preprocess(images=images)
            model_inputs["pixel_values"] = mx.array(np.stack(pixel_values))

            # Cache the result for future requests
            if (
                PIXEL_VALUES_CACHE_ENABLED
                and original_image_sources
                and all(src is not None for src in original_image_sources)
                and len(original_image_sources) == 1
            ):
                original_size = (images[0].height, images[0].width) if hasattr(images[0], 'height') else (0, 0)
                cache_pixel_values(original_image_sources[0], model_inputs["pixel_values"], original_size)

        model_inputs["attention_mask"] = mx.array(
            [(ids != processor.pad_token_id) for ids in input_ids]
        ).astype(mx.int32)

    else:
        if hasattr(processor, "tokenizer") and processor.tokenizer.pad_token is None:
            processor.tokenizer.pad_token = processor.tokenizer.eos_token

        # For Qwen2VL/3VL processors, apply chat template to format prompts correctly
        # These processors expect <|vision_start|><|image_pad|><|vision_end|> format
        # Skip if prompt is already templated (e.g., when called from server which applies its own template)
        formatted_prompts = prompts
        if is_qwen_vl_processor and hasattr(processor, 'apply_chat_template'):
            # Check if prompt is already chat-templated (contains Qwen VL markers)
            prompts_check = prompts if isinstance(prompts, str) else prompts[0] if prompts else ""
            already_templated = "<|vision_start|>" in prompts_check or "<|im_start|>" in prompts_check

            if not already_templated:
                num_images = len(images) if images else 0
                # Build messages in the format expected by Qwen VL chat template
                if not isinstance(prompts, list):
                    prompts_list = [prompts]
                else:
                    prompts_list = prompts

                formatted_prompts = []
                for p in prompts_list:
                    messages = [{'role': 'user', 'content': []}]
                    # Add image placeholders
                    for _ in range(num_images):
                        messages[0]['content'].append({'type': 'image'})
                    messages[0]['content'].append({'type': 'text', 'text': p})

                    try:
                        formatted = processor.apply_chat_template(
                            messages, tokenize=False, add_generation_prompt=True
                        )
                        formatted_prompts.append(formatted)
                    except Exception:
                        # Fallback to original prompt if chat template fails
                        formatted_prompts.append(p)

                if not isinstance(prompts, list):
                    formatted_prompts = formatted_prompts[0]

        inputs = process_inputs_with_fallback(
            processor,
            images=images,
            audio=audio,
            prompts=formatted_prompts,
            add_special_tokens=add_special_tokens,
            **kwargs,
        )

        if "images" in inputs:
            inputs["pixel_values"] = inputs["images"]
            inputs.pop("images")

        model_inputs["attention_mask"] = (
            mx.array(inputs["attention_mask"]) if "attention_mask" in inputs else None
        )

        # Convert inputs to model_inputs with mx.array if present
        for key, value in inputs.items():
            if key not in model_inputs:
                if isinstance(value, (str, list, mx.array)):
                    model_inputs[key] = value
                else:
                    model_inputs[key] = mx.array(value)

        # Pixel values caching for regular processor path (Production Caching Option 1)
        # For this path, we still need to run the processor for tokenization, but we can
        # replace the pixel_values with cached ones (already evaluated tensors = faster)
        if (
            PIXEL_VALUES_CACHE_ENABLED
            and "pixel_values" in model_inputs
            and original_image_sources
            and all(src is not None for src in original_image_sources)
            and len(original_image_sources) == 1
        ):
            cached = get_cached_pixel_values(original_image_sources[0])
            if cached is not None:
                # Cache HIT - use cached pixel_values (already evaluated)
                cached_pv, _ = cached
                model_inputs["pixel_values"] = cached_pv
                if PIXEL_VALUES_CACHE_DEBUG:
                    print(f"[PIXEL CACHE] REPLACED processor pixel_values with cached tensor")
            else:
                # Cache MISS - cache the pixel_values for next time
                original_size = (images[0].height, images[0].width) if images and hasattr(images[0], 'height') else (0, 0)
                cache_pixel_values(original_image_sources[0], model_inputs["pixel_values"], original_size)

    if audio_inputs is not None:
        model_inputs["input_features"] = mx.array(audio_inputs["input_features"])
        model_inputs["feature_attention_mask"] = mx.array(
            audio_inputs["attention_mask"]
        ).astype(mx.int32)
        model_inputs["audio_feature_lengths"] = mx.array(
            audio_feature_lengths, dtype=mx.int32
        )

    return model_inputs


def group_images_by_shape(
    images: List[Image.Image],
    disable_grouping: bool = False,
) -> Tuple[Dict[Tuple[int, int], List[Image.Image]], Dict[Tuple[int, int], List[int]]]:
    """
    Group images by their dimensions for efficient batch processing.

    Images with the same dimensions can be stacked and processed together,
    which is much faster than processing individually (especially on GPU).

    Args:
        images: List of PIL images to group
        disable_grouping: If True, each image gets its own group (useful for debugging)

    Returns:
        grouped_images: Dict mapping shape -> list of images with that shape
        grouped_indices: Dict mapping shape -> list of original indices

    Example:
        >>> images = [img_400x300, img_800x600, img_400x300_2]
        >>> grouped, indices = group_images_by_shape(images)
        >>> grouped
        {(300, 400): [img_400x300, img_400x300_2], (600, 800): [img_800x600]}
        >>> indices
        {(300, 400): [0, 2], (600, 800): [1]}
    """
    if disable_grouping:
        # Each image in its own group
        grouped_images = {}
        grouped_indices = {}
        for i, img in enumerate(images):
            shape = (img.height, img.width)
            # Make each shape unique by adding index
            unique_shape = (img.height, img.width, i)
            grouped_images[unique_shape] = [img]
            grouped_indices[unique_shape] = [i]
        return grouped_images, grouped_indices

    grouped_images: Dict[Tuple[int, int], List[Image.Image]] = {}
    grouped_indices: Dict[Tuple[int, int], List[int]] = {}

    for i, img in enumerate(images):
        shape = (img.height, img.width)
        if shape not in grouped_images:
            grouped_images[shape] = []
            grouped_indices[shape] = []
        grouped_images[shape].append(img)
        grouped_indices[shape].append(i)

    return grouped_images, grouped_indices


class StoppingCriteria:
    def __init__(self, eos_token_ids: List[int], tokenizer=None):

        if isinstance(eos_token_ids, int):
            self.eos_token_ids = [eos_token_ids]
        else:
            self.eos_token_ids = eos_token_ids

        self.tokenizer = tokenizer

    def add_eos_token_ids(self, new_eos_token_ids: Union[int, List[int]] = None):
        """
        Add new token IDs to the list of EOS token IDs.

        Args:
            new_eos_token_ids: Integer, string, or list of integers/strings representing token IDs to add.
                               If strings are provided, they will be converted to integers if possible.
        """
        if new_eos_token_ids is None:
            return

        if self.tokenizer is None:
            raise ValueError("Processor is not provided")

        if new_eos_token_ids is not None:
            if isinstance(new_eos_token_ids, str):
                new_eos_token_ids = [new_eos_token_ids]
            new_eos_token_ids = [
                self.tokenizer.encode(" " + token, add_special_tokens=False)[-1]
                for token in new_eos_token_ids
            ]
            self.eos_token_ids.extend(new_eos_token_ids)

    def reset(self, eos_token_ids: List[int] = None):
        eos_token_ids = (
            eos_token_ids if eos_token_ids is not None else self.tokenizer.eos_token_ids
        )

        if isinstance(eos_token_ids, int):
            eos_token_ids = [eos_token_ids]

        if self.eos_token_ids != eos_token_ids:
            self.eos_token_ids = eos_token_ids

    def __call__(self, input_ids: mx.array) -> bool:
        return input_ids in self.eos_token_ids


def print_array_report(t: mx.array, label: Optional[str]) -> dict:
    """
    Return a dictionary report of an MLX array similar to PyTorch's tensor representation.
    Args:
        arr: MLX array to analyze
    Returns:
        Dictionary containing shape, dtype, value representation, and statistics
    """

    # Get basic statistics
    mean_val = mx.mean(t)
    std_val = mx.std(t)
    min_val = mx.min(t)
    max_val = mx.max(t)

    report = {
        "shape": f"{tuple(t.shape)}",
        "dtype": str(t.dtype),
        "value": repr(t),
        "mean": f"array({mean_val}, dtype={t.dtype})",
        "std": f"array({std_val}, dtype={t.dtype})",
        "min": f"array({min_val}, dtype={t.dtype})",
        "max": f"array({max_val}, dtype={t.dtype})",
        "label": label if label else "array",
    }

    # Print each field, handling 'value' specially
    print("{")
    for key, value in report.items():
        if key == "value":
            print(f" '{key}': {value},")  # No quotes around value
        else:
            print(f" '{key}': {repr(value)},")
    print("}")
    return report
