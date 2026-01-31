"""
Neural LAB - AI Solutions Platform
Billing Resource - Unified usage, subscription, and PIX payment management.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-24
"""

from dataclasses import dataclass, field
from typing import Any

from ..base import DataclassMixin


@dataclass
class Usage(DataclassMixin):
    """Current usage information."""

    total_requests: int
    total_tokens: int
    total_cost: float
    included_requests: int | None
    included_tokens: int | None
    requests_percentage: float
    tokens_percentage: float
    period_start: str
    period_end: str
    days_remaining: int


@dataclass
class Subscription(DataclassMixin):
    """Subscription information."""

    id: str
    plan_name: str
    status: str
    billing_cycle: str
    current_period_start: str
    current_period_end: str


@dataclass
class Credits(DataclassMixin):
    """Credits balance."""

    current_balance: float
    credit_limit: float
    available: float


@dataclass
class ProductPlan(DataclassMixin):
    """Product plan information."""

    id: str
    product: str
    plan: str
    name: str
    price_monthly: float
    price_annual: float
    limits: dict[str, Any] = field(default_factory=dict)
    features: list[str] = field(default_factory=list)


@dataclass
class ProductSubscription(DataclassMixin):
    """Product subscription information."""

    product: str
    plan: str
    status: str
    current_period_start: str
    current_period_end: str
    payment_method: str
    limits: dict[str, Any] = field(default_factory=dict)


@dataclass
class PixCharge(DataclassMixin):
    """PIX charge information."""

    payment_id: str
    txid: str
    status: str
    qr_code: str
    qr_code_base64: str | None
    amount: float
    expires_at: str
    product: str
    plan: str


@dataclass
class PixStatus(DataclassMixin):
    """PIX payment status."""

    payment_id: str
    txid: str
    status: str
    amount: float
    product: str
    plan: str
    paid_at: str | None = None
    e2e_id: str | None = None


@dataclass
class ProductUsage(DataclassMixin):
    """Product-specific usage information."""

    product: str
    period: str
    reset_at: str
    metrics: dict[str, dict[str, Any]] = field(default_factory=dict)


class BillingResource:
    """
    Billing resource for usage and subscription management.

    Usage:
        # Check usage
        usage = client.billing.get_usage()

        # Get subscription
        sub = client.billing.get_subscription()

        # Check credits
        credits = client.billing.get_credits()
    """

    def __init__(self, client):
        self._client = client

    def get_usage(self) -> Usage:
        """
        Get current usage for billing period.

        Returns:
            Usage information
        """
        response = self._client.get("/api/billing/client/usage")

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

    def get_subscription(self) -> Subscription:
        """
        Get current subscription.

        Returns:
            Subscription information
        """
        response = self._client.get("/api/billing/client/subscription")

        plan = response.get("plan", {})
        return Subscription(
            id=response.get("id", ""),
            plan_name=plan.get("name", "free"),
            status=response.get("status", "active"),
            billing_cycle=response.get("billing_cycle", "monthly"),
            current_period_start=response.get("current_period_start", ""),
            current_period_end=response.get("current_period_end", ""),
        )

    def get_credits(self) -> Credits:
        """
        Get current credits balance.

        Returns:
            Credits balance
        """
        response = self._client.get("/api/billing/client/credits")

        return Credits(
            current_balance=response.get("current_balance", 0),
            credit_limit=response.get("credit_limit", 0),
            available=response.get("available", 0),
        )

    def get_invoices(
        self,
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Get invoices.

        Args:
            limit: Number of invoices to return
            offset: Offset for pagination

        Returns:
            List of invoices
        """
        response = self._client.get(
            "/api/billing/client/invoices",
            params={"limit": limit, "offset": offset},
        )

        return response.get("invoices", [])

    def get_me(self) -> dict[str, Any]:
        """
        Get current client info.

        Returns:
            Client information
        """
        return self._client.get("/api/billing/client/me")

    # =========================================================================
    # Product Billing (Hipócrates, Mercúrius, Pólis)
    # =========================================================================

    def get_product_plans(self, product: str) -> list[ProductPlan]:
        """
        Get available plans for a product.

        Args:
            product: Product name (hipocrates, mercurius, polis)

        Returns:
            List of available plans
        """
        response = self._client.get(f"/api/billing/products/plans/{product}")

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

    def get_product_subscription(self, product: str) -> ProductSubscription | None:
        """
        Get current subscription for a product.

        Args:
            product: Product name (hipocrates, mercurius, polis)

        Returns:
            Product subscription or None if not subscribed
        """
        response = self._client.get(f"/api/billing/products/subscription/{product}")

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

    def create_pix_charge(
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
        response = self._client.post(
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

    def get_pix_status(self, txid: str) -> PixStatus:
        """
        Get PIX payment status.

        Args:
            txid: Transaction ID

        Returns:
            PIX payment status
        """
        response = self._client.get(f"/api/billing/products/pix/status/{txid}")

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

    def get_product_usage(self, product: str) -> ProductUsage:
        """
        Get usage summary for a product.

        Args:
            product: Product name (hipocrates, mercurius, polis)

        Returns:
            Product usage with limits and percentages
        """
        response = self._client.get(f"/api/billing/products/usage/{product}")

        return ProductUsage(
            product=response.get("product", product),
            period=response.get("period", ""),
            reset_at=response.get("reset_at", ""),
            metrics=response.get("metrics", {}),
        )
