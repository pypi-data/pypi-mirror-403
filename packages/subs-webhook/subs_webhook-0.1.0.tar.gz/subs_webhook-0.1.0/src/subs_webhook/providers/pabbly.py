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

# from ..db.dependencies import get_db, get_redis
from ..db.subscriptions.models import Subscription, Profile, ApiKey
from ..api.models import WebhookPayload


# --- HELPER: Extract Data ---
def extract_pabbly_fields(event_type: str, data: dict):

    normalized = {}

    # 1. Extract Customer
    if "customer" in data and isinstance(data["customer"], dict):
        normalized["email"] = data["customer"].get("email_id")
        normalized["pabbly_customer_id"] = data["customer"].get("id")
    else:
        normalized["email"] = data.get("email_id")
        normalized["pabbly_customer_id"] = data.get("customer_id")

        # Fallback for customer_create where id is at root
        if not normalized["pabbly_customer_id"]:
            normalized["pabbly_customer_id"] = data.get("id")

    # 2. Extract Plan
    if "plan" in data and "plan_code" in data["plan"]:
        normalized["plan_code"] = data["plan"]["plan_code"]
    elif "subscription" in data and "plan" in data["subscription"]:
        normalized["plan_code"] = data["subscription"]["plan"].get("plan_code")

    # 3. Extract Status/Expiry
    if event_type == "invoice_paid" and "subscription" in data:
        normalized["status"] = "live"
        normalized["expiry_date"] = data["subscription"].get("expiry_date")
        normalized["sub_id"] = data.get("subscription_id")
    else:
        normalized["status"] = data.get("status")
        normalized["expiry_date"] = data.get("expiry_date")
        normalized["sub_id"] = data.get("id")

    return normalized


async def run_webhook(
    payload: WebhookPayload,
    db,
    redis,
    invalidate_user_cache
):

    event = payload.event_type
    raw_data = payload.data
    info = extract_pabbly_fields(event, raw_data)

    print(
        f"Received Pabbly Event: {event} | ID: {info.get('sub_id') or info.get('pabbly_customer_id')}"
    )

    # --------------------------------------------------------
    # HANDLE: customer_create
    # --------------------------------------------------------
    if event == "customer_create":
        # Check if user exists
        stmt = select(Profile).where(Profile.email == info["email"])
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user:
            print(f"Creating new user: {info['email']}")
            user = Profile(
                email=info["email"], pabbly_customer_id=info["pabbly_customer_id"]
            )
            db.add(user)
            await db.commit()
        else:
            print(f"User already exists: {info['email']}")
            # Update ID if missing
            if not user.pabbly_customer_id:
                user.pabbly_customer_id = info["pabbly_customer_id"]
                await db.commit()

    # --------------------------------------------------------
    # HANDLE: subscription_create
    # --------------------------------------------------------
    elif event == "subscription_create":
        # 1. Find User (by Pabbly ID or Email)
        stmt = select(Profile).where(
            Profile.pabbly_customer_id == info["pabbly_customer_id"]
        )
        result = await db.execute(stmt)
        user = result.scalars().first()

        if not user and info.get("email"):
            # Try finding by email
            stmt = select(Profile).where(Profile.email == info["email"])
            result = await db.execute(stmt)
            user = result.scalars().first()

        # 2. If User still None, CREATE THEM NOW
        if not user:
            print(f"User not found for subscription. Auto-creating: {info['email']}")
            user = Profile(
                email=info["email"], pabbly_customer_id=info["pabbly_customer_id"]
            )
            db.add(user)
            await db.flush()  # Flush to ensure user.id is generated and available

        # 3. Create Subscription
        stmt = select(Subscription).where(Subscription.id == info["sub_id"])
        existing = (await db.execute(stmt)).scalars().first()

        if not existing:
            print(f"Creating new subscription: {info['sub_id']}")
            new_sub = Subscription(
                id=info["sub_id"],
                user_id=user.id,
                plan_code=info["plan_code"],
                status="pending",
            )
            db.add(new_sub)
            await db.commit()
        else:
            print(f"Subscription already exists: {info['sub_id']}")

    # --------------------------------------------------------
    # HANDLE: subscription_activate / invoice_paid
    # --------------------------------------------------------
    elif event in ["subscription_activate", "invoice_paid"]:
        sub_id = info.get("sub_id")
        expiry = info.get("expiry_date")

        if sub_id and expiry:
            print(f"Activating subscription {sub_id} until {expiry}")

            # Parse Date
            try:
                expiry_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            except Exception as e:
                print(f"Date parse error: {e}")
                expiry_dt = datetime.utcnow()  # Fallback

            stmt = (
                update(Subscription)
                .where(Subscription.id == sub_id)
                .values(
                    status="live",
                    current_period_end=expiry_dt,
                    plan_code=info.get("plan_code"),
                )
                .returning(Subscription.user_id)
            )

            result = await db.execute(stmt)
            user_id = result.scalar()

            await db.commit()

            if user_id:
                await invalidate_user_cache(user_id, db, redis)
            else:
                print(
                    f"Warning: Could not update sub {sub_id} - maybe it wasn't created yet?"
                )

    # --------------------------------------------------------
    # HANDLE: subscription_cancel
    # --------------------------------------------------------
    elif event == "subscription_cancel":
        sub_id = info.get("sub_id")
        print(f"Cancelling subscription {sub_id}")

        stmt = (
            update(Subscription)
            .where(Subscription.id == sub_id)
            .values(status="cancelled")
            .returning(Subscription.user_id)
        )
        result = await db.execute(stmt)
        user_id = result.scalar()

        await db.commit()
        if user_id:
            await invalidate_user_cache(user_id, db, redis)

    return {"status": "processed"}
