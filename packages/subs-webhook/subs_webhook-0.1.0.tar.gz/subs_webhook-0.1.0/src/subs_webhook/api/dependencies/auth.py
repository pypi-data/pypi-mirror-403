"""
 Copyright (c) 2026 Anthony Mugendi
 
 This software is released under the MIT License.
 https://opensource.org/licenses/MIT
"""

import json
from datetime import datetime
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis

# Imports
from ...dependencies import get_db, get_redis, RedisKeyPrefix
from ...db.subscriptions.models import ApiKey, Subscription, Profile

# Define the header key (e.g., "X-API-Key: sk_live_...")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

ERR_MISSING_API_HEADER = {
    "code": "AUTH_MISSING_HEADER",
    "message": "Missing X-API-Key header.",
    "doc_url": "/docs#authentication"
}

ERR_API_ACCESS_DENIED = {
    "code": "AUTH_ACCESS_DENIED",
    "message": "Invalid API Key or no active subscription found.",
    "resolution": "Please check your subscription status in the dashboard."
}

async def verify_subscription(
    api_key_str: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    Dependency that verifies:
    1. API Key exists and is active.
    2. User has at least one 'live' subscription.
    3. Subscription has not expired.
    
    Returns: A dict containing user_id and active plans.
    """
    if not api_key_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERR_MISSING_API_HEADER
        )

    # --- STEP 1: CHECK REDIS (Fast Path) ---
    cache_key = f"{RedisKeyPrefix}:{api_key_str}"
    cached_data = await redis.get(cache_key)

    if cached_data:
        # print('cache hit',cache_key)
        data = json.loads(cached_data)
        # Redis has TTL, but double-check expiry time in logic for safety
        valid_until = datetime.fromisoformat(data["valid_until"])
        
        if datetime.utcnow() < valid_until:
            return data # Fast return!

    # --- STEP 2: CHECK DATABASE (Slow Path) ---
    # We join ApiKey -> Profile -> Subscription
    # We want ALL active subscriptions for this user
    stmt = (
        select(ApiKey, Subscription)
        .join(Profile, ApiKey.user_id == Profile.id)
        .join(Subscription, Subscription.user_id == Profile.id)
        .where(
            ApiKey.key == api_key_str,
            ApiKey.status == "active",
            Subscription.status == "live",
            Subscription.current_period_end > datetime.utcnow()
        )
    )
    
    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        # Check why it failed to give a specific error
        # (Optional: just return 403 Generic to prevent enumeration)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ERR_API_ACCESS_DENIED
        )

    # --- STEP 3: AGGREGATE PERMISSIONS ---
    # A user might have multiple subs. We allow access if ANY is valid.
    # We set the Cache TTL to the *earliest* expiry date.
    
    user_id = rows[0][0].user_id # Get user_id from ApiKey object
    active_plans = []
    earliest_expiry = None

    for _, sub in rows:
        active_plans.append(sub.plan_code)
        
        # Track earliest expiry for cache TTL
        if earliest_expiry is None or sub.current_period_end < earliest_expiry:
            earliest_expiry = sub.current_period_end

    # Data to return to the endpoint
    auth_context = {
        "user_id": user_id,
        "plans": list(set(active_plans)), # Deduplicate
        "valid_until": earliest_expiry.isoformat()
    }

    # --- STEP 4: CACHE RESULT ---
    # Calculate TTL in seconds
    now = datetime.utcnow()
    ttl_seconds = int((earliest_expiry - now).total_seconds())
    
    # Safety buffer: If TTL is somehow negative (race condition), don't cache
    if ttl_seconds > 0:
        await redis.set(cache_key, json.dumps(auth_context), ex=ttl_seconds)

    return auth_context



