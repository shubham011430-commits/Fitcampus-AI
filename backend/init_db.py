"""Create tables without touching existing data (safe, unlike seed_data.py)."""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.database import init_db, engine


async def main():
    await init_db()
    await engine.dispose()
    print("✅ Tables created (existing data untouched).")


if __name__ == "__main__":
    asyncio.run(main())
