"""
Copyright (c) 2026 Anthony Mugendi

This software is released under the MIT License.
https://opensource.org/licenses/MIT
"""

from fastapi import Request, Depends, HTTPException, status
from .auth import verify_subscription
from ..models import PlansConfig


class AccessGuard:
    def __init__(self, sub_plan_permissions: dict):
        self.sub_plan_permissions = sub_plan_permissions

    async def __call__(
        self, request: Request, user: dict = Depends(verify_subscription)
    ):
        """
        1. Dependency Injection runs 'verify_subscription' first.
        2. Then this runs to check if the user's plan allows the current path.
        """

        current_path = request.url.path
        user_plans = user.get("plans", [])

        # Debugging (Remove in production)
        # print(f"Checking access for {user_plans} on {current_path}")

        allowed = False

        # Check if ANY of the user's plans allow this path
        for plan in user_plans:
            plan_data = self.sub_plan_permissions.get(plan, [])

            allowed_routes = plan_data["routes"]

            request.state.plan  = plan
            request.state.plan_features  = plan_data.get("features", {})
            request.state.rate_limit  = plan_data.get("rate_limit", {})

            # print(plan_data)
            # print(request.state.plan_features)

            # You might want to allow exact matches OR sub-paths
            # Example: if config is "/rates", allow "/rates/usd"
            # For now, we use exact match to be safe.
            if current_path in allowed_routes:
                allowed = True
                break

        
            

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your current plan ({', '.join(user_plans)}) does not allow access to this feature.",
            )
        
        request.state.user = user
        return user


# Initialize the instance
# PLAN_PERMISSIONS = config['SUBSCRIPTION']['plans']
def validate_access(sub_plan_permissions):
    PlansConfig(sub_plan_permissions)
    return AccessGuard(sub_plan_permissions)
