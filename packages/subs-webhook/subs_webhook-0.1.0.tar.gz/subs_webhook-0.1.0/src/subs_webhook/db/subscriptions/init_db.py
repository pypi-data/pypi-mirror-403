"""
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
"""

import asyncio
from sqlalchemy import text
from ..dependencies import engine
from .subscriptions.models import Base

async def init_models():
    print(f"Checking Subscriptions DB...")
    
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    
    # Enable Write-Ahead Logging (WAL) for concurrency
    # This must be done on a direct connection, not a transaction block
    async with engine.connect() as conn:
        await conn.execute(text("PRAGMA journal_mode=WAL;"))
        await conn.execute(text("PRAGMA synchronous=NORMAL;"))
        print("SQLite WAL Mode Enabled.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_models())