#!/usr/bin/env python3
"""
CLI Tool for Building and Updating Codebase Graph

Usage:
    python scripts/build-codegraph.py [--watch] [--clear] [--path PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codegraph_mcp.builder import CodeGraphBuilder
from codegraph_mcp.neo4j_client import Neo4jClient
from codegraph_mcp.scanner import CodeGraphScanner
from codegraph_mcp.updater import CodeGraphUpdater
from codegraph_mcp.watcher import CodeGraphWatcher


def build_graph(
    codebase_path: str,
    clear_existing: bool = False,
    watch: bool = False,
) -> None:
    """Build or update codebase graph.

    Args:
        codebase_path: Path to codebase directory
        clear_existing: Whether to clear existing graph
        watch: Whether to watch for file changes
    """
    print("Initializing Neo4j client...")
    try:
        client = Neo4jClient()
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        print("Make sure NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD are set")
        sys.exit(1)

    print("Scanning codebase...")
    scanner = CodeGraphScanner(codebase_path)
    nodes, relations = scanner.scan()

    print(f"Found {len(nodes)} nodes and {len(relations)} relationships")

    print("Building graph...")
    builder = CodeGraphBuilder(client)
    builder.build_graph(nodes, relations, clear_existing=clear_existing)

    print("Graph build complete!")

    if watch:
        print("Starting file watcher...")
        updater = CodeGraphUpdater(builder, scanner)

        def on_file_changed(file_path: str) -> None:
            print(f"File changed: {file_path}")
            updater.update_file(file_path)
            print(f"Updated graph for: {file_path}")

        watcher = CodeGraphWatcher(codebase_path, on_file_changed)
        watcher.start()

        try:
            print("Watching for changes (press Ctrl+C to stop)...")
            while True:
                import time

                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping watcher...")
            watcher.stop()

    client.close()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build and update codebase graph in Neo4j"
    )
    parser.add_argument(
        "--path",
        type=str,
        default="src/domolibrary2",
        help="Path to codebase directory (default: src/domolibrary2)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing graph before building",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch for file changes and update graph incrementally",
    )

    args = parser.parse_args()

    codebase_path = Path(args.path)
    if not codebase_path.exists():
        print(f"Error: Path does not exist: {codebase_path}")
        sys.exit(1)

    build_graph(
        str(codebase_path),
        clear_existing=args.clear,
        watch=args.watch,
    )


if __name__ == "__main__":
    main()
