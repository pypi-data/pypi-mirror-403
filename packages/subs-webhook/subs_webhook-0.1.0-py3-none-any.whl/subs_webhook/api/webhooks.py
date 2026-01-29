"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

from fastapi import APIRouter, Request, HTTPException, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from redis.asyncio import Redis
from datetime import datetime


# Import your setup
from ..db.subscriptions.models import Subscription, Profile, ApiKey
from .models import WebhookPayload
from ..providers.pabbly import run_webhook as run_pabbly_webhook
from ..dependencies import get_db, get_redis, RedisKeyPrefix

def init_router():

    router = APIRouter(tags=["webhooks"])

    # --- HELPER: Cache Invalidation ---
    async def invalidate_user_cache(user_id: str, db: AsyncSession, redis: Redis):
        stmt = select(ApiKey.key).where(ApiKey.user_id == user_id)
        result = await db.execute(stmt)
        keys = result.scalars().all()

        if keys:
            redis_keys = [f"{RedisKeyPrefix}:{key}" for key in keys]
            print('redis_keys', redis_keys)
            await redis.delete(*redis_keys)
            print(f"Invalidated keys for user {user_id}: {redis_keys}")

    # --- ROUTER ---
    @router.post("/subscription-webhook/{provider}")
    async def pabbly_webhook(
        payload: WebhookPayload,
        provider: str,
        db: AsyncSession = Depends(get_db),
        redis: Redis = Depends(get_redis),
    ):

        if provider == "pabbly":
            return await run_pabbly_webhook(
                payload=payload,
                db=db,
                redis=redis,
                invalidate_user_cache=invalidate_user_cache,
            )

    return router
