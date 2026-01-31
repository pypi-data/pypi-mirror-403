"""Integration test to validate SDK against live API.

This test ensures that SDK models and endpoints match the actual API.
Run this before every release to catch breaking changes.
"""

import asyncio
import os

import pytest

from rencom import AsyncRencomClient


@pytest.mark.integration
class TestAPIValidation:
    """Validate SDK against live API."""

    @pytest.fixture
    async def client(self):
        """Create test client."""
        api_key = os.getenv("RENCOM_API_KEY", "test_key")
        async with AsyncRencomClient(api_key=api_key) as client:
            yield client

    async def test_ucp_merchant_search_response_structure(self, client):
        """Validate MerchantSearchResponse has correct fields."""
        response = await client.ucp.merchants.search(limit=1)

        # Check response structure
        assert hasattr(response, "merchants"), "Response should have 'merchants' attribute"
        assert hasattr(response, "total"), "Response should have 'total' attribute"
        assert hasattr(response, "has_more"), "Response should have 'has_more' attribute"
        assert hasattr(response, "limit"), "Response should have 'limit' attribute"
        assert hasattr(response, "offset"), "Response should have 'offset' attribute"

        # Check it's a list
        assert isinstance(response.merchants, list), "'merchants' should be a list"

        # If there are merchants, check structure
        if response.merchants:
            merchant = response.merchants[0]
            assert hasattr(merchant, "id")
            assert hasattr(merchant, "domain")
            assert hasattr(merchant, "name")
            assert hasattr(merchant, "capabilities")
            assert hasattr(merchant, "endpoints")

    async def test_ucp_product_search_response_structure(self, client):
        """Validate ProductSearchResponse has correct fields."""
        response = await client.ucp.products.search("test", limit=1)

        # Check response structure
        assert hasattr(response, "products"), "Response should have 'products' attribute"
        assert hasattr(response, "total"), "Response should have 'total' attribute"
        assert hasattr(response, "has_more"), "Response should have 'has_more' attribute"
        assert hasattr(response, "limit"), "Response should have 'limit' attribute"
        assert hasattr(response, "offset"), "Response should have 'offset' attribute"
        assert hasattr(response, "query"), "Response should have 'query' attribute"

        # Check it's a list
        assert isinstance(response.products, list), "'products' should be a list"

    async def test_x402_search_response_structure(self, client):
        """Validate x402 SearchResponse has correct fields."""
        response = await client.x402.search("test", limit=1)

        # Check response structure
        assert hasattr(response, "results"), "Response should have 'results' attribute"
        assert hasattr(response, "has_more"), "Response should have 'has_more' attribute"
        assert hasattr(response, "limit"), "Response should have 'limit' attribute"
        assert hasattr(response, "offset"), "Response should have 'offset' attribute"

        # Check it's a list
        assert isinstance(response.results, list), "'results' should be a list"

    async def test_all_endpoints_accessible(self, client):
        """Verify all SDK endpoints are accessible."""
        # UCP endpoints
        await client.ucp.merchants.search(limit=1)
        await client.ucp.products.search("test", limit=1)

        # x402 endpoints
        await client.x402.search("test", limit=1)

        print("✓ All endpoints accessible")
