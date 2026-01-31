from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Usage types that match the NestJS backend
USAGE_TYPE_REWARD_FLASH = "reward_flash"
USAGE_TYPE_REWARD_PRO = "reward_pro"
USAGE_TYPE_LEARNING = "learning"
USAGE_TYPE_COPILOT = "copilot"


class InsufficientCreditsError(Exception):
    """Raised when user has insufficient credits for an operation."""

    def __init__(self, balance: float = 0.0) -> None:
        self.balance = balance
        super().__init__(f"Insufficient credits. Current balance: ${balance:.2f}")


class BillingClient:
    """Client for communicating with the NestJS billing service."""

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or os.getenv("MARLO_BACKEND_URL")
        if not self._base_url:
            raise RuntimeError("MARLO_BACKEND_URL is required for billing.")
        self._client = httpx.AsyncClient(timeout=30.0)

    async def check_credits(self, user_id: str) -> float:
        """
        Check if user has sufficient credits.

        Args:
            user_id: The user's UUID

        Returns:
            Current credit balance

        Raises:
            InsufficientCreditsError if balance is 0 or negative
        """
        try:
            response = await self._client.get(
                f"{self._base_url}/billing/credits/{user_id}",
            )

            if response.status_code == 200:
                result = response.json()
                balance = float(result.get("credits", 0))
                if balance <= 0:
                    raise InsufficientCreditsError(balance)
                return balance
            else:
                logger.warning(
                    f"Failed to check credits: {response.status_code} - {response.text}"
                )
                raise InsufficientCreditsError(0)

        except InsufficientCreditsError:
            raise
        except Exception as e:
            logger.warning(f"Error checking credits: {e}")
            raise InsufficientCreditsError(0)

    async def deduct_credits(
        self,
        *,
        user_id: str,
        input_tokens: int,
        output_tokens: int,
        model: str,
        usage_type: str,
        project_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Deduct credits from a user's account based on token usage.

        Args:
            user_id: The user's UUID
            input_tokens: Number of input tokens used
            output_tokens: Number of output tokens used
            model: The model name (e.g., "gemini-3-flash", "gemini-3-pro")
            usage_type: One of "reward_flash", "reward_pro", "learning", "copilot"
            project_id: Optional project UUID

        Returns:
            Dict with success, cost, and newBalance
        """
        try:
            response = await self._client.post(
                f"{self._base_url}/billing/deduct",
                json={
                    "userId": user_id,
                    "inputTokens": input_tokens,
                    "outputTokens": output_tokens,
                    "model": model,
                    "usageType": usage_type,
                    "projectId": project_id,
                },
            )

            if response.status_code == 200:
                result = response.json()
                logger.debug(
                    f"Credits deducted: cost=${result.get('cost', 0):.6f}, "
                    f"balance=${result.get('newBalance', 0):.2f}"
                )
                return result
            else:
                logger.warning(
                    f"Failed to deduct credits: {response.status_code} - {response.text}"
                )
                return {"success": False, "cost": 0, "newBalance": 0}

        except Exception as e:
            logger.warning(f"Error deducting credits: {e}")
            return {"success": False, "cost": 0, "newBalance": 0}

    async def get_credits(self, user_id: str, auth_token: str) -> float:
        """Get a user's current credit balance."""
        try:
            response = await self._client.get(
                f"{self._base_url}/billing/credits",
                headers={"Authorization": f"Bearer {auth_token}"},
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("credits", 0)
            else:
                return 0

        except Exception as e:
            logger.warning(f"Error getting credits: {e}")
            return 0

    async def check_can_run_reward(self, org_id: str) -> bool:
        """
        Check if organization can run reward processing (free tier + payment check).
        
        Args:
            org_id: The organization's UUID
            
        Returns:
            True if org can run rewards, False otherwise
        """
        try:
            response = await self._client.get(
                f"{self._base_url}/billing/org/{org_id}/can-run-reward",
            )

            if response.status_code == 200:
                result = response.json()
                return result.get("canRunReward", False)
            else:
                logger.warning(
                    f"Failed to check reward eligibility: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.warning(f"Error checking reward eligibility: {e}")
            return False

    async def get_quota(self, org_id: str) -> dict[str, Any]:
        """
        Get quota details for an organization (free tier usage, limits, payment status).
        
        Args:
            org_id: The organization's UUID
            
        Returns:
            Dict with freeTasksUsed, freeTasksLimit, hasPaymentMethod, etc.
        """
        try:
            response = await self._client.get(
                f"{self._base_url}/billing/org/{org_id}/quota",
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(
                    f"Failed to get quota: {response.status_code} - {response.text}"
                )
                return {}

        except Exception as e:
            logger.warning(f"Error getting quota: {e}")
            return {}

    async def record_task_usage(self, org_id: str, project_id: str | None = None) -> dict[str, Any]:
        """
        Record task usage for organization and charge if past free tier.
        
        Args:
            org_id: The organization's UUID
            project_id: Optional project UUID
            
        Returns:
            Dict with success, wasCharged, cost, and task counts
        """
        try:
            response = await self._client.post(
                f"{self._base_url}/billing/org/{org_id}/record-task",
                json={
                    "projectId": project_id,
                },
            )

            if response.status_code == 200:
                result = response.json()
                logger.debug(
                    f"Task usage recorded: charged=${result.get('wasCharged', False)}, "
                    f"cost=${result.get('cost', 0):.2f}, "
                    f"free_remaining={result.get('freeTasksRemaining', 0)}"
                )
                return result
            else:
                logger.warning(
                    f"Failed to record task usage: {response.status_code} - {response.text}"
                )
                return {"success": False, "wasCharged": False, "cost": 0}

        except Exception as e:
            logger.warning(f"Error recording task usage: {e}")
            return {"success": False, "wasCharged": False, "cost": 0}

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()


# Global billing client instance
_billing_client: BillingClient | None = None


def get_billing_client() -> BillingClient:
    """Get the global billing client instance."""
    global _billing_client
    if _billing_client is None:
        _billing_client = BillingClient()
    return _billing_client


async def deduct_credits_for_llm_call(
    *,
    user_id: str,
    input_tokens: int,
    output_tokens: int,
    model: str,
    usage_type: str,
    project_id: str | None = None,
) -> dict[str, Any]:
    """
    Convenience function to deduct credits for an LLM call.

    This should be called after each Gemini API call with the token usage.
    """
    client = get_billing_client()
    return await client.deduct_credits(
        user_id=user_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=model,
        usage_type=usage_type,
        project_id=project_id,
    )


class BillingLLMClient:
    """LLM client wrapper that automatically deducts credits after each call.

    This wrapper intercepts calls to acomplete() and automatically bills
    the user based on token usage returned by the underlying client.
    """

    def __init__(
        self,
        llm_client: Any,
        *,
        user_id: str,
        project_id: str | None = None,
        usage_type: str = USAGE_TYPE_COPILOT,
    ) -> None:
        self._client = llm_client
        self._user_id = user_id
        self._project_id = project_id
        self._usage_type = usage_type

    async def acomplete(
        self,
        messages: list[dict[str, Any]],
        response_format: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Call the underlying LLM and deduct credits based on usage."""
        response = await self._client.acomplete(
            messages=messages,
            response_format=response_format,
            **kwargs,
        )

        usage = getattr(response, "usage", None)
        model = getattr(response, "model", None) or "gemini-3-flash"

        if usage and self._user_id:
            input_tokens = usage.get("input_tokens", 0) if isinstance(usage, dict) else 0
            output_tokens = usage.get("output_tokens", 0) if isinstance(usage, dict) else 0

            if input_tokens > 0 or output_tokens > 0:
                await deduct_credits_for_llm_call(
                    user_id=self._user_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    model=model,
                    usage_type=self._usage_type,
                    project_id=self._project_id,
                )

        return response
