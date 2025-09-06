#!/usr/bin/env python3
"""Main entry point for document ingestion."""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    from rag_agent.data.ingestion.ingest import main
    main()