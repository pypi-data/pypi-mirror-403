"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

import asyncio
import nest_asyncio
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from .dependencies import init_session, init_subscription_models

from fastapi import Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


# Optional: Validation function
async def get_api_key(api_key: str = Security(api_key_header), request:Request=None):
    # Add validation logic here if needed
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
        
    request.state.api_key = api_key
    return api_key


def init_subs(app: FastAPI, sqlite_path: Path, redis_url: str, prefix: str = None):
    # initialize session
    init_session(sqlite_path=sqlite_path, redis_url=redis_url)

    # initialize router
    from .api.webhooks import init_router

    if prefix:
        app.include_router(init_router(), prefix=prefix, include_in_schema=False)
    else:
        app.include_router(init_router(), include_in_schema=False)

    # init models in nested event loop
    nest_asyncio.apply()
    asyncio.run(init_subscription_models())

    return app
