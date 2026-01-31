"""
NTLabs SDK - Billing Resource Tests
Tests for the BillingResource class.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
"""

from ntlabs.resources.billing import (
    BillingResource,
    Credits,
    Subscription,
    Usage,
)


class TestUsage:
    """Tests for Usage dataclass."""

    def test_create_usage(self, usage_response):
        """Create usage."""
        usage = Usage(
            total_requests=usage_response["total_requests"],
            total_tokens=usage_response["total_tokens"],
            total_cost=usage_response["total_cost"],
            included_requests=usage_response["included_requests"],
            included_tokens=usage_response["included_tokens"],
            requests_percentage=usage_response["requests_percentage"],
            tokens_percentage=usage_response["tokens_percentage"],
            period_start=usage_response["period_start"],
            period_end=usage_response["period_end"],
            days_remaining=usage_response["days_remaining"],
        )
        assert usage.total_requests == 1000
        assert usage.total_tokens == 500000
        assert usage.days_remaining == 15


class TestSubscription:
    """Tests for Subscription dataclass."""

    def test_create_subscription(self, subscription_response):
        """Create subscription."""
        sub = Subscription(
            id=subscription_response["id"],
            plan_name=subscription_response["plan"]["name"],
            status=subscription_response["status"],
            billing_cycle=subscription_response["billing_cycle"],
            current_period_start=subscription_response["current_period_start"],
            current_period_end=subscription_response["current_period_end"],
        )
        assert sub.id == "sub-123"
        assert sub.plan_name == "pro"
        assert sub.status == "active"


class TestCredits:
    """Tests for Credits dataclass."""

    def test_create_credits(self, credits_response):
        """Create credits."""
        credits = Credits(
            current_balance=credits_response["current_balance"],
            credit_limit=credits_response["credit_limit"],
            available=credits_response["available"],
        )
        assert credits.current_balance == 100.00
        assert credits.credit_limit == 500.00


class TestBillingResource:
    """Tests for BillingResource."""

    def test_initialization(self, mock_client):
        """BillingResource initializes with client."""
        billing = BillingResource(mock_client)
        assert billing._client == mock_client

    def test_get_usage(self, mock_client, mock_response, usage_response):
        """Get current usage."""
        mock_client._mock_http.request.return_value = mock_response(usage_response)

        result = mock_client.billing.get_usage()

        assert isinstance(result, Usage)
        assert result.total_requests == 1000
        assert result.total_tokens == 500000
        assert result.total_cost == 25.50
        assert result.requests_percentage == 10.0
        assert result.tokens_percentage == 50.0
        assert result.days_remaining == 15

    def test_get_usage_percentages(self, mock_client, mock_response, usage_response):
        """Usage includes usage percentages."""
        mock_client._mock_http.request.return_value = mock_response(usage_response)

        result = mock_client.billing.get_usage()

        assert result.included_requests == 10000
        assert result.included_tokens == 1000000

    def test_get_subscription(self, mock_client, mock_response, subscription_response):
        """Get current subscription."""
        mock_client._mock_http.request.return_value = mock_response(
            subscription_response
        )

        result = mock_client.billing.get_subscription()

        assert isinstance(result, Subscription)
        assert result.plan_name == "pro"
        assert result.status == "active"
        assert result.billing_cycle == "monthly"

    def test_get_subscription_free_tier(self, mock_client, mock_response):
        """Get free tier subscription."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "id": "sub-free",
                "plan": {"name": "free", "id": "plan-free"},
                "status": "active",
                "billing_cycle": "monthly",
                "current_period_start": "2026-01-01",
                "current_period_end": "2026-01-31",
            }
        )

        result = mock_client.billing.get_subscription()

        assert result.plan_name == "free"

    def test_get_credits(self, mock_client, mock_response, credits_response):
        """Get credits balance."""
        mock_client._mock_http.request.return_value = mock_response(credits_response)

        result = mock_client.billing.get_credits()

        assert isinstance(result, Credits)
        assert result.current_balance == 100.00
        assert result.credit_limit == 500.00
        assert result.available == 100.00

    def test_get_credits_zero_balance(self, mock_client, mock_response):
        """Handle zero credits balance."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "current_balance": 0.0,
                "credit_limit": 100.0,
                "available": 0.0,
            }
        )

        result = mock_client.billing.get_credits()

        assert result.current_balance == 0.0
        assert result.available == 0.0

    def test_get_invoices(self, mock_client, mock_response):
        """Get invoices."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "invoices": [
                    {
                        "id": "inv-1",
                        "amount": 99.90,
                        "status": "paid",
                        "period_start": "2025-12-01",
                        "period_end": "2025-12-31",
                    },
                    {
                        "id": "inv-2",
                        "amount": 99.90,
                        "status": "open",
                        "period_start": "2026-01-01",
                        "period_end": "2026-01-31",
                    },
                ]
            }
        )

        result = mock_client.billing.get_invoices()

        assert len(result) == 2
        assert result[0]["id"] == "inv-1"
        assert result[0]["status"] == "paid"

    def test_get_invoices_with_pagination(self, mock_client, mock_response):
        """Get invoices with pagination."""
        mock_client._mock_http.request.return_value = mock_response({"invoices": []})

        result = mock_client.billing.get_invoices(limit=5, offset=10)

        assert result == []

    def test_get_invoices_empty(self, mock_client, mock_response):
        """Handle no invoices."""
        mock_client._mock_http.request.return_value = mock_response({})

        result = mock_client.billing.get_invoices()
        assert result == []

    def test_get_me(self, mock_client, mock_response):
        """Get current client info."""
        mock_client._mock_http.request.return_value = mock_response(
            {
                "id": "client-123",
                "name": "Test Client",
                "email": "client@example.com",
                "created_at": "2026-01-01T00:00:00Z",
            }
        )

        result = mock_client.billing.get_me()

        assert result["id"] == "client-123"
        assert result["name"] == "Test Client"

    def test_empty_response_handling(self, mock_client, mock_response):
        """Handle empty responses gracefully."""
        mock_client._mock_http.request.return_value = mock_response({})

        # Usage
        result = mock_client.billing.get_usage()
        assert result.total_requests == 0
        assert result.total_cost == 0
        assert result.days_remaining == 0

        # Subscription
        result = mock_client.billing.get_subscription()
        assert result.plan_name == "free"
        assert result.status == "active"

        # Credits
        result = mock_client.billing.get_credits()
        assert result.current_balance == 0
