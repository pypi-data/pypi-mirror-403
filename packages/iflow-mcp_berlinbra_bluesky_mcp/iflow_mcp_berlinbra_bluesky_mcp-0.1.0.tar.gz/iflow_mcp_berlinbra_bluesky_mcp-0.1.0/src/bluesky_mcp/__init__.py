import asyncio
from .server import main

__all__ = ["main"]

def cli():
    """CLI entry point"""
    asyncio.run(main())

if __name__ == "__main__":
    cli()