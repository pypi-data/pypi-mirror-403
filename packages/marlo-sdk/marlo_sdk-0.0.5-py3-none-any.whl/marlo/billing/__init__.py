from __future__ import annotations

from marlo.billing.client import (
    USAGE_TYPE_COPILOT,
    USAGE_TYPE_LEARNING,
    USAGE_TYPE_REWARD_FLASH,
    USAGE_TYPE_REWARD_PRO,
    BillingClient,
    BillingLLMClient,
    InsufficientCreditsError,
    deduct_credits_for_llm_call,
    get_billing_client,
)


async def require_credits(org_id: str) -> bool:
    """
    Check if organization can run reward processing (free tier + payment check).

    Use this at the start of API routes that need reward processing.

    Args:
        org_id: The organization's UUID

    Returns:
        True if org can run rewards

    Raises:
        InsufficientCreditsError if org cannot run rewards
    """
    client = get_billing_client()
    can_run = await client.check_can_run_reward(org_id)
    if not can_run:
        raise InsufficientCreditsError(0.0)  # Balance 0 to indicate no access
    return can_run


__all__ = [
    "BillingClient",
    "BillingLLMClient",
    "InsufficientCreditsError",
    "get_billing_client",
    "deduct_credits_for_llm_call",
    "require_credits",
    "USAGE_TYPE_REWARD_FLASH",
    "USAGE_TYPE_REWARD_PRO",
    "USAGE_TYPE_LEARNING",
    "USAGE_TYPE_COPILOT",
]
