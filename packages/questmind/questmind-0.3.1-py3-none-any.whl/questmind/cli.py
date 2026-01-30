"""
QuestMind CLI - Unified entry point for server and document processing.

Usage:
    questmind serve [OPTIONS]     Start the VLM server
    questmind ingest [OPTIONS]    Ingest a document
    questmind query [OPTIONS]     Query a document
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="QuestMind - Local VLM server and document processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Start server on Apple Silicon (MLX)
    questmind serve --backend mlx --model Qwen3-VL-4B --port 8000

    # Start server on NVIDIA GPU (CUDA)
    questmind serve --backend cuda --model Qwen2.5-VL-7B --port 8000

    # Short form (MLX is default)
    questmind serve -m Qwen3-VL-4B -p 8000

    # Ingest a document
    questmind ingest document.pdf --output doc.pack

    # Query a document
    questmind query doc.pack "What is this about?"
""",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Start the VLM server")
    serve_parser.add_argument(
        "--backend", "-b",
        type=str,
        choices=["mlx", "cuda"],
        default="mlx",
        help="Hardware backend: mlx (Apple Silicon) or cuda (NVIDIA) (default: mlx)"
    )
    serve_parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="Model to load (default: auto based on backend)"
    )
    serve_parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port to listen on (default: 8000)"
    )
    serve_parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    serve_parser.add_argument(
        "--continuous-batching",
        action="store_true",
        help="Enable continuous batching"
    )

    # ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest a document")
    ingest_parser.add_argument("source", help="Document path or directory")
    ingest_parser.add_argument(
        "--output", "-o",
        type=str,
        help="Output path for DocumentPack"
    )
    ingest_parser.add_argument(
        "--type", "-t",
        choices=["pdf", "image", "text", "auto"],
        default="auto",
        help="Document type (default: auto-detect)"
    )

    # query command
    query_parser = subparsers.add_parser("query", help="Query a document")
    query_parser.add_argument("document", help="DocumentPack path or source file")
    query_parser.add_argument("question", help="Question to ask")
    query_parser.add_argument(
        "--server", "-s",
        type=str,
        default="http://localhost:8000",
        help="Server URL (default: http://localhost:8000)"
    )
    query_parser.add_argument(
        "--force-vision",
        action="store_true",
        help="Force VLM for visual understanding"
    )

    args = parser.parse_args()

    if args.command == "serve":
        serve(args)
    elif args.command == "ingest":
        ingest(args)
    elif args.command == "query":
        query(args)
    else:
        parser.print_help()
        sys.exit(1)


def serve(args):
    """Start the VLM server."""
    backend = args.backend

    # Default models per backend
    default_models = {
        "mlx": "mlx-community/Qwen3-VL-4B-Instruct-4bit",
        "cuda": "Qwen/Qwen2.5-VL-7B-Instruct",
    }

    # Model name mappings per backend
    model_maps = {
        "mlx": {
            "Qwen3-VL-2B": "mlx-community/Qwen3-VL-2B-Instruct-4bit",
            "Qwen3-VL-4B": "mlx-community/Qwen3-VL-4B-Instruct-4bit",
            "Qwen3-VL-8B": "mlx-community/Qwen3-VL-8B-Instruct-4bit",
            "Qwen3-VL-30B": "mlx-community/Qwen3-VL-30B-A3B-Instruct-4bit",
            "Qwen2.5-VL-3B": "mlx-community/Qwen2.5-VL-3B-Instruct-4bit",
            "Qwen2.5-VL-7B": "mlx-community/Qwen2.5-VL-7B-Instruct-4bit",
        },
        "cuda": {
            "Qwen3-VL-2B": "Qwen/Qwen3-VL-2B-Instruct",
            "Qwen3-VL-4B": "Qwen/Qwen3-VL-4B-Instruct",
            "Qwen3-VL-8B": "Qwen/Qwen3-VL-8B-Instruct",
            "Qwen3-VL-32B": "Qwen/Qwen3-VL-32B-Instruct",
            "Qwen2.5-VL-3B": "Qwen/Qwen2.5-VL-3B-Instruct",
            "Qwen2.5-VL-7B": "Qwen/Qwen2.5-VL-7B-Instruct",
            "Qwen2.5-VL-72B": "Qwen/Qwen2.5-VL-72B-Instruct",
        },
    }

    # Resolve model
    model = args.model or default_models[backend]
    if "/" not in model:
        # Short name -> full path
        model = model_maps[backend].get(model, model)

    print(f"Starting QuestMind server...")
    print(f"  Backend: {backend}")
    print(f"  Model:   {model}")
    print(f"  Host:    {args.host}")
    print(f"  Port:    {args.port}")
    print()

    if backend == "mlx":
        _serve_mlx(args, model)
    elif backend == "cuda":
        _serve_cuda(args, model)


def _serve_mlx(args, model: str):
    """Start server with MLX backend (Apple Silicon)."""
    # Import and start questmind server
    from questmind.server.app import load_model, app

    # Load the model
    load_model(
        model_name=model,
        use_batching=args.continuous_batching,
    )

    # Start server with uvicorn
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)


def _serve_cuda(args, model: str):
    """Start server with CUDA backend (NVIDIA GPUs)."""
    import subprocess

    # Use vLLM for CUDA
    # TODO: Update to use lubauss/vllm fork when available
    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model", model,
        "--host", args.host,
        "--port", str(args.port),
        "--trust-remote-code",
    ]

    print(f"Running: {' '.join(cmd)}")
    print()
    print("Note: CUDA backend requires vLLM. Install with:")
    print("  pip install vllm")
    print()

    try:
        subprocess.run(cmd)
    except FileNotFoundError:
        print("Error: vLLM not found. Install with: pip install vllm")
        sys.exit(1)


def ingest(args):
    """Ingest a document into a DocumentPack."""
    from questmind import create_ingestor

    print(f"Ingesting: {args.source}")

    # Create appropriate ingestor
    ingestor = create_ingestor(args.source, document_type=args.type if args.type != "auto" else None)
    pack = ingestor.ingest(args.source)

    print(f"  Type: {pack.document_type}")
    print(f"  Pages/Units: {pack.total_pages}")

    if args.output:
        # Save the pack
        import pickle
        with open(args.output, "wb") as f:
            pickle.dump(pack, f)
        print(f"  Saved to: {args.output}")
    else:
        print(f"  (Use --output to save the DocumentPack)")


def query(args):
    """Query a document."""
    from questmind import QueryEngine, create_ingestor
    import pickle
    import os

    # Load or ingest the document
    if args.document.endswith(".pack"):
        print(f"Loading DocumentPack: {args.document}")
        with open(args.document, "rb") as f:
            pack = pickle.load(f)
    else:
        print(f"Ingesting: {args.document}")
        ingestor = create_ingestor(args.document)
        pack = ingestor.ingest(args.document)

    print(f"  Type: {pack.document_type}")
    print(f"  Pages/Units: {pack.total_pages}")
    print()

    # Query
    engine = QueryEngine(server_url=args.server)
    result = engine.query(
        pack,
        args.question,
        force_vision=args.force_vision
    )

    print(f"Question: {args.question}")
    print(f"Method: {result.method}")
    print(f"Pages used: {result.pages_used}")
    print()
    print("Answer:")
    print(result.answer)


if __name__ == "__main__":
    main()
