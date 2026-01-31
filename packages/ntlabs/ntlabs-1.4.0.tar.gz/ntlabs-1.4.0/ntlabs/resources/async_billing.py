"""
Neural LAB - AI Solutions Platform
Async Billing Resource - Unified usage, subscription, and PIX payment management.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from typing import Any

from .billing import (
    Credits,
    PixCharge,
    PixStatus,
    ProductPlan,
    ProductSubscription,
    ProductUsage,
    Subscription,
    Usage,
)


class AsyncBillingResource:
    """Async billing resource for usage, subscription, and PIX management."""

    def __init__(self, client):
        self._client = client

    async def get_usage(self) -> Usage:
        """Get current usage for billing period."""
        response = await self._client.get("/api/billing/client/usage")

        return Usage(
            total_requests=response.get("total_requests", 0),
            total_tokens=response.get("total_tokens", 0),
            total_cost=response.get("total_cost", 0),
            included_requests=response.get("included_requests"),
            included_tokens=response.get("included_tokens"),
            requests_percentage=response.get("requests_percentage", 0),
            tokens_percentage=response.get("tokens_percentage", 0),
            period_start=response.get("period_start", ""),
            period_end=response.get("period_end", ""),
            days_remaining=response.get("days_remaining", 0),
        )

    async def get_subscription(self) -> Subscription:
        """Get current subscription."""
        response = await self._client.get("/api/billing/client/subscription")
        plan = response.get("plan", {})

        return Subscription(
            id=response.get("id", ""),
            plan_name=plan.get("name", "free"),
            status=response.get("status", "active"),
            billing_cycle=response.get("billing_cycle", "monthly"),
            current_period_start=response.get("current_period_start", ""),
            current_period_end=response.get("current_period_end", ""),
        )

    async def get_credits(self) -> Credits:
        """Get current credits balance."""
        response = await self._client.get("/api/billing/client/credits")

        return Credits(
            current_balance=response.get("current_balance", 0),
            credit_limit=response.get("credit_limit", 0),
            available=response.get("available", 0),
        )

    async def get_invoices(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get invoices with pagination."""
        response = await self._client.get(
            "/api/billing/client/invoices",
            params={"limit": limit, "offset": offset},
        )
        return response.get("invoices", [])

    async def get_me(self) -> dict[str, Any]:
        """Get current client info."""
        return await self._client.get("/api/billing/client/me")

    # =========================================================================
    # Product Billing (Hipócrates, Mercúrius, Pólis)
    # =========================================================================

    async def get_product_plans(self, product: str) -> list[ProductPlan]:
        """
        Get available plans for a product.

        Args:
            product: Product name (hipocrates, mercurius, polis)

        Returns:
            List of available plans
        """
        response = await self._client.get(f"/api/billing/products/plans/{product}")

        return [
            ProductPlan(
                id=p.get("id", ""),
                product=p.get("product", product),
                plan=p.get("plan", ""),
                name=p.get("name", ""),
                price_monthly=p.get("price_monthly", 0),
                price_annual=p.get("price_annual", 0),
                limits=p.get("limits", {}),
                features=p.get("features", []),
            )
            for p in response
        ]

    async def get_product_subscription(
        self, product: str
    ) -> ProductSubscription | None:
        """
        Get current subscription for a product.

        Args:
            product: Product name (hipocrates, mercurius, polis)

        Returns:
            Product subscription or None if not subscribed
        """
        response = await self._client.get(
            f"/api/billing/products/subscription/{product}"
        )

        if not response:
            return None

        return ProductSubscription(
            product=response.get("product", product),
            plan=response.get("plan", "free"),
            status=response.get("status", "active"),
            current_period_start=response.get("current_period_start", ""),
            current_period_end=response.get("current_period_end", ""),
            payment_method=response.get("payment_method", "pix"),
            limits=response.get("limits", {}),
        )

    async def create_pix_charge(
        self,
        product: str,
        plan: str,
        billing_cycle: str = "monthly",
    ) -> PixCharge:
        """
        Create PIX charge for product subscription.

        Args:
            product: Product name (hipocrates, mercurius, polis)
            plan: Plan name (basic, professional, enterprise)
            billing_cycle: Billing cycle (monthly or annual)

        Returns:
            PIX charge with QR code
        """
        response = await self._client.post(
            "/api/billing/products/pix/create",
            json={
                "product": product,
                "plan": plan,
                "billing_cycle": billing_cycle,
            },
        )

        return PixCharge(
            payment_id=response.get("payment_id", ""),
            txid=response.get("txid", ""),
            status=response.get("status", ""),
            qr_code=response.get("qr_code", ""),
            qr_code_base64=response.get("qr_code_base64"),
            amount=response.get("amount", 0),
            expires_at=response.get("expires_at", ""),
            product=response.get("product", product),
            plan=response.get("plan", plan),
        )

    async def get_pix_status(self, txid: str) -> PixStatus:
        """
        Get PIX payment status.

        Args:
            txid: Transaction ID

        Returns:
            PIX payment status
        """
        response = await self._client.get(f"/api/billing/products/pix/status/{txid}")

        return PixStatus(
            payment_id=response.get("payment_id", ""),
            txid=response.get("txid", txid),
            status=response.get("status", ""),
            amount=response.get("amount", 0),
            product=response.get("product", ""),
            plan=response.get("plan", ""),
            paid_at=response.get("paid_at"),
            e2e_id=response.get("e2e_id"),
        )

    async def get_product_usage(self, product: str) -> ProductUsage:
        """
        Get usage summary for a product.

        Args:
            product: Product name (hipocrates, mercurius, polis)

        Returns:
            Product usage with limits and percentages
        """
        response = await self._client.get(f"/api/billing/products/usage/{product}")

        return ProductUsage(
            product=response.get("product", product),
            period=response.get("period", ""),
            reset_at=response.get("reset_at", ""),
            metrics=response.get("metrics", {}),
        )
