"""
NTLabs SDK - Async Billing Resource Tests
Tests for the AsyncBillingResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

import pytest
from unittest.mock import AsyncMock

from ntlabs.resources.async_billing import AsyncBillingResource
from ntlabs.resources.billing import Credits, Subscription, Usage, ProductPlan, ProductSubscription, PixCharge, PixStatus, ProductUsage


@pytest.mark.asyncio
class TestAsyncBillingResource:
    """Tests for AsyncBillingResource."""

    async def test_initialization(self):
        """AsyncBillingResource initializes with client."""
        mock_client = AsyncMock()
        billing = AsyncBillingResource(mock_client)
        assert billing._client == mock_client


@pytest.mark.asyncio
class TestAsyncBillingUsage:
    """Tests for async billing usage."""

    async def test_get_usage(self, usage_response):
        """Get current usage."""
        mock_client = AsyncMock()
        mock_client.get.return_value = usage_response

        billing = AsyncBillingResource(mock_client)
        result = await billing.get_usage()

        assert isinstance(result, Usage)
        assert result.total_requests == 1000
        assert result.total_tokens == 500000
        assert result.total_cost == 25.50
        assert result.period_start == "2026-01-01"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/api/billing/client/usage"

    async def test_get_subscription(self, subscription_response):
        """Get current subscription."""
        mock_client = AsyncMock()
        mock_client.get.return_value = subscription_response

        billing = AsyncBillingResource(mock_client)
        result = await billing.get_subscription()

        assert isinstance(result, Subscription)
        assert result.id == "sub-123"
        assert result.plan_name == "pro"
        assert result.status == "active"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/api/billing/client/subscription"

    async def test_get_credits(self, credits_response):
        """Get credits balance."""
        mock_client = AsyncMock()
        mock_client.get.return_value = credits_response

        billing = AsyncBillingResource(mock_client)
        result = await billing.get_credits()

        assert isinstance(result, Credits)
        assert result.current_balance == 100.00
        assert result.credit_limit == 500.00
        assert result.available == 100.00
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/api/billing/client/credits"

    async def test_get_invoices(self):
        """Get invoices."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "invoices": [
                {"id": "inv_1", "amount": 99.00, "status": "paid"},
                {"id": "inv_2", "amount": 99.00, "status": "pending"},
            ]
        }

        billing = AsyncBillingResource(mock_client)
        result = await billing.get_invoices(limit=10, offset=0)

        assert len(result) == 2
        assert result[0]["id"] == "inv_1"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/api/billing/client/invoices"
        assert call_args[1]["params"]["limit"] == 10
        assert call_args[1]["params"]["offset"] == 0

    async def test_get_me(self):
        """Get client info."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {"id": "client_123", "name": "Test Client"}

        billing = AsyncBillingResource(mock_client)
        result = await billing.get_me()

        assert result["id"] == "client_123"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/api/billing/client/me"


@pytest.mark.asyncio
class TestAsyncBillingProducts:
    """Tests for async product billing."""

    async def test_get_product_plans(self, product_plans_response):
        """Get product plans."""
        mock_client = AsyncMock()
        mock_client.get.return_value = product_plans_response

        billing = AsyncBillingResource(mock_client)
        result = await billing.get_product_plans("hipocrates")

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(p, ProductPlan) for p in result)
        assert result[0].plan == "basic"
        assert result[1].plan == "professional"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/api/billing/products/plans/hipocrates"

    async def test_get_product_subscription_found(self):
        """Get existing product subscription."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "product": "hipocrates",
            "plan": "professional",
            "status": "active",
            "current_period_start": "2026-01-01",
            "current_period_end": "2026-01-31",
            "payment_method": "pix",
            "limits": {"consultations": 500},
        }

        billing = AsyncBillingResource(mock_client)
        result = await billing.get_product_subscription("hipocrates")

        assert isinstance(result, ProductSubscription)
        assert result.plan == "professional"
        assert result.status == "active"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/api/billing/products/subscription/hipocrates"

    async def test_get_product_subscription_not_found(self):
        """Get non-existent product subscription."""
        mock_client = AsyncMock()
        mock_client.get.return_value = None

        billing = AsyncBillingResource(mock_client)
        result = await billing.get_product_subscription("hipocrates")

        assert result is None

    async def test_create_pix_charge(self):
        """Create PIX charge for product."""
        mock_client = AsyncMock()
        mock_client.post.return_value = {
            "payment_id": "pay_123",
            "txid": "txid_abc",
            "status": "pending",
            "qr_code": "0002012658...",
            "amount": 99.00,
            "expires_at": "2026-01-28T20:00:00Z",
            "product": "hipocrates",
            "plan": "basic",
        }

        billing = AsyncBillingResource(mock_client)
        result = await billing.create_pix_charge("hipocrates", "basic", "monthly")

        assert isinstance(result, PixCharge)
        assert result.payment_id == "pay_123"
        assert result.txid == "txid_abc"
        assert result.amount == 99.00
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/api/billing/products/pix/create"
        assert call_args[1]["json"]["product"] == "hipocrates"
        assert call_args[1]["json"]["plan"] == "basic"
        assert call_args[1]["json"]["billing_cycle"] == "monthly"

    async def test_get_pix_status(self):
        """Get PIX payment status."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "payment_id": "pay_123",
            "txid": "txid_abc",
            "status": "paid",
            "amount": 99.00,
            "product": "hipocrates",
            "plan": "basic",
            "paid_at": "2026-01-27T20:30:00Z",
            "e2e_id": "E123456",
        }

        billing = AsyncBillingResource(mock_client)
        result = await billing.get_pix_status("txid_abc")

        assert isinstance(result, PixStatus)
        assert result.txid == "txid_abc"
        assert result.status == "paid"
        assert result.amount == 99.00
        assert result.e2e_id == "E123456"
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/api/billing/products/pix/status/txid_abc"

    async def test_get_product_usage(self):
        """Get product usage."""
        mock_client = AsyncMock()
        mock_client.get.return_value = {
            "product": "hipocrates",
            "period": "2026-01",
            "reset_at": "2026-02-01T00:00:00Z",
            "metrics": {
                "consultations": {"used": 50, "limit": 100},
                "storage_mb": {"used": 500, "limit": 1000},
            },
        }

        billing = AsyncBillingResource(mock_client)
        result = await billing.get_product_usage("hipocrates")

        assert isinstance(result, ProductUsage)
        assert result.product == "hipocrates"
        assert result.period == "2026-01"
        assert "consultations" in result.metrics
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert call_args[0][0] == "/api/billing/products/usage/hipocrates"
