#!/usr/bin/env python3
"""
Synth-Fuse CLI Entry Point
"""

import sys
import asyncio
import argparse
from pathlib import Path

from synthfuse.cabinet.cabinet_orchestrator import CabinetOrchestrator
from synthfuse.ingest.watcher import LibrarianWatcher


def print_banner():
    banner = """
    ┌────────────────────────────────────────────────────────────┐
    │                Synth-Fuse v0.2.0 - Cabinet                 │
    │         Unified Field Engineering - Deterministic          │
    └────────────────────────────────────────────────────────────┘
    """
    print(banner)


async def start_cabinet(watch_ingest: bool = True):
    """Start the Cabinet of Alchemists."""
    print_banner()
    
    # Initialize Cabinet
    cabinet = CabinetOrchestrator()
    
    try:
        print("🛡️  Initializing Cabinet of Alchemists...")
        success = await cabinet.initialize()
        
        if not success:
            print("❌ Cabinet failed to initialize")
            return 1
        
        print("✅ Cabinet initialized successfully!")
        
        # Start ingestion watcher if requested
        if watch_ingest:
            ingest_dir = Path.cwd() / "ingest" / "raw"
            ingest_dir.mkdir(parents=True, exist_ok=True)
            
            watcher = LibrarianWatcher(ingest_dir, cabinet.librarian)
            print(f"📚 Librarian watching: {ingest_dir.absolute()}")
            
            watcher_task = asyncio.create_task(watcher.watch())
        
        # Keep running
        print("\n🚀 Cabinet operational. Press Ctrl+C to exit.")
        await asyncio.Future()  # Run forever
        
    except KeyboardInterrupt:
        print("\n🛑 Cabinet shutdown initiated...")
        return 0
    except Exception as e:
        print(f"💥 Error: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Synth-Fuse v0.2.0 - Unified Field Engineering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  synthfuse                    # Start Cabinet with ingestion watcher
  synthfuse --no-watch         # Start Cabinet without watching ingest
  synthfuse --version          # Show version information
        """,
    )
    
    parser.add_argument(
        "--no-watch",
        action="store_true",
        help="Do not watch ingest directory",
    )
    
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information",
    )
    
    args = parser.parse_args()
    
    # Show version
    if args.version:
        from synthfuse import __version__
        print(f"Synth-Fuse v{__version__}")
        return 0
    
    # Start Cabinet
    return asyncio.run(start_cabinet(not args.no_watch))


if __name__ == "__main__":
    sys.exit(main())
