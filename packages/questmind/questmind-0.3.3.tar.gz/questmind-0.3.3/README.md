<p align="center">
  <img src="https://raw.githubusercontent.com/lubauss/questmind/main/assets/logo.png" width="200">
</p>

<h1 align="center">questmind</h1>

<p align="center">
  <strong>Local VLM server and document processor for Apple Silicon</strong>
</p>

## Features

- **OpenAI-compatible API** - Run local VLMs via HTTP with streaming
- **Document processing** - PDFs, image collections, text files
- **Hybrid intelligence** - Native text extraction + VLM for visual content
- **Multi-turn caching** - KV prefix cache, vision embedding cache
- **Apple Silicon optimized** - MLX backend with Metal acceleration
- **Self-contained** - No external fork dependencies

## Requirements

- Python 3.10+
- macOS with Apple Silicon (M1/M2/M3/M4)
- 16GB+ RAM recommended (32GB+ for 30B models)

## Installation

```bash
# Add to your project (creates .venv automatically)
uv add questmind

# Or run directly without installing
uvx questmind --help

# From source
git clone https://github.com/lubauss/questmind.git
cd questmind
uv sync
```

| Command | Purpose | What it does |
|---------|---------|--------------|
| `uv add questmind` | Add dependency | Creates `.venv`, updates `pyproject.toml`, generates `uv.lock` |
| `uv run questmind serve` | Run CLI | Uses project's venv, auto-syncs deps |
| `uvx questmind` | Run without install | Ephemeral environment, like `npx` |
| `uv sync` | Install from lockfile | Reproducible builds from `uv.lock` |

All features (VLM server, PDF/image processing, embeddings) are included by default.

## Quick Start

### Server Mode

```bash
# Start the VLM server
uv run questmind serve --model mlx-community/Qwen3-VL-4B-Instruct-4bit --port 8000

# With continuous batching (better for multiple users)
uv run questmind serve --model mlx-community/Qwen3-VL-4B-Instruct-4bit --continuous-batching

# Query via curl
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "default", "messages": [{"role": "user", "content": "Hello!"}]}'
```

### Vision Queries

```bash
# Image from URL
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "What is in this image?"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
      ]
    }]
  }'
```

### Document Processing

```bash
# Ingest a document
uv run questmind ingest document.pdf --output doc.pack

# Query a document
uv run questmind query doc.pack "What is this about?"
```

### Library Mode

```python
from questmind import PDFIngestor, QueryEngine

# Ingest a PDF
pack = PDFIngestor().ingest("document.pdf")

# Query with RAG
result = QueryEngine().query(pack, "What is the main topic?")
print(result.answer)
print(f"Pages used: {result.pages_used}")
print(f"Method: {result.method}")  # "text_only" or "text_with_vision"
```

## Supported Models

| Model | Size | Memory | Use Case |
|-------|------|--------|----------|
| `mlx-community/Qwen3-VL-2B-Instruct-4bit` | 2B | ~4GB | Quick responses |
| `mlx-community/Qwen3-VL-4B-Instruct-4bit` | 4B | ~6GB | Balanced |
| `mlx-community/Qwen3-VL-8B-Instruct-4bit` | 8B | ~10GB | High quality |
| `mlx-community/Qwen3-VL-30B-A3B-Instruct-4bit` | 30B MoE | ~20GB | Best quality |

## Performance

Tested on MacBook Pro M4 Max 128GB with Qwen3-VL-30B-A3B:

| Metric | Value |
|--------|-------|
| Generation TPS | 70-75 tok/s |
| Prompt TPS (cached) | 1200-1500 tok/s |
| Prompt TPS (cold) | 400-700 tok/s |
| Multi-turn speedup | 2-21x |

## Architecture

```
questmind/
├── server/          # OpenAI-compatible FastAPI server
├── engine/          # Simple + Batched inference engines
├── models/          # Qwen3-VL model implementations
├── inference/       # Generation, sampling, tokenization
├── cache/           # KV prefix cache, VLM cache
├── scheduler/       # Continuous batching scheduler
└── api/             # Pydantic models, utilities
```

## Caching Layers

| Cache | Purpose | Benefit |
|-------|---------|---------|
| KV Prefix | Reuse computed attention states | 2-21x speedup |
| Vision Embedding | Skip vision encoder on repeated images | 1.3-1.7x speedup |
| Cross-image Prefix | Reuse text prefix across images | Multi-image support |

## API Reference

### Server Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Chat completions (streaming) |
| `/v1/completions` | POST | Text completions |
| `/v1/models` | GET | List available models |
| `/health` | GET | Health check |
| `/metrics` | GET | Server metrics |

### Python API

```python
# Server (programmatic)
from questmind.server import app, load_model
load_model("mlx-community/Qwen3-VL-4B-Instruct-4bit")
# Run with: uvicorn questmind.server:app

# Direct inference
from questmind.inference import load, generate
model, processor = load("mlx-community/Qwen3-VL-4B-Instruct-4bit")
output = generate(model, processor, "Hello!")

# Document processing
from questmind import PDFIngestor, ImageIngestor, TextIngestor, QueryEngine
pack = PDFIngestor().ingest("doc.pdf")
result = QueryEngine().query(pack, "Summary?")
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QUESTMIND_API_KEY` | None | API key for authentication |
| `QUESTMIND_CACHE_DIR` | `~/.questmind/cache` | Cache directory |
| `MLX_METAL_DEVICE` | `0` | GPU device index |

## Changelog

### v0.3.0 (2026-01-26)

- **Integrated vllm-mlx and mlx-vlm** - No more fork dependencies
- Self-contained package with single `pip install`
- Qwen3-VL models (dense and MoE) included
- Simplified installation and deployment

### v0.2.0

- Added CLI commands (serve, ingest, query)
- Backend selection (mlx/cuda)
- Multi-turn caching improvements

### v0.1.0

- Initial release
- PDF processing with hybrid VLM
- RAG pipeline with embeddings

## License

MIT

## Credits

Built on:
- [MLX](https://github.com/ml-explore/mlx) - Apple's ML framework
- [mlx-lm](https://github.com/ml-explore/mlx-lm) - Language model primitives
- [mlx-vlm](https://github.com/Blaizzy/mlx-vlm) by [@Blaizzy](https://github.com/Blaizzy) - Vision-language model inference
- [vllm-mlx](https://github.com/waybarrios/vllm-mlx) by [@waybarrios](https://github.com/waybarrios) - MLX inference server with continuous batching
- [Qwen3-VL](https://huggingface.co/Qwen) - Vision-language models
