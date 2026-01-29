"""Tests for the Google Ads API client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from google_ads_mcp.client import (
    GoogleAdsApiClient,
    MatchType,
    MutationResult,
)


class TestMutationResult:
    """Tests for MutationResult dataclass."""

    def test_success_result(self):
        result = MutationResult(
            success=True,
            resource_name="customers/123/campaigns/456",
            resource_id="456",
        )
        assert result.success is True
        assert result.resource_id == "456"
        assert result.error_message is None

    def test_error_result(self):
        result = MutationResult(
            success=False,
            error_message="Something went wrong",
        )
        assert result.success is False
        assert result.error_message == "Something went wrong"

    def test_to_dict(self):
        result = MutationResult(
            success=True,
            resource_name="customers/123/campaigns/456",
            resource_id="456",
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["resource_id"] == "456"
        assert d["resource_name"] == "customers/123/campaigns/456"


class TestMatchType:
    """Tests for MatchType enum."""

    def test_values(self):
        assert MatchType.BROAD.value == "BROAD"
        assert MatchType.PHRASE.value == "PHRASE"
        assert MatchType.EXACT.value == "EXACT"


class TestDryRunMode:
    """Tests for dry run mode."""

    @patch("google_ads_mcp.client.GoogleAdsClient")
    def test_create_campaign_dry_run(self, mock_client_class):
        """Test that dry run mode returns without executing mutations."""
        mock_client = MagicMock()
        mock_client_class.load_from_storage.return_value = mock_client
        mock_client.login_customer_id = "123456789"

        client = GoogleAdsApiClient(config_path="fake.yaml", dry_run=True)
        result = client.create_campaign(name="Test Campaign")

        assert result.success is True
        assert "DRY RUN" in result.error_message
        # In dry run mode, the mutation methods should not be called
        budget_service = mock_client.get_service.return_value
        budget_service.mutate_campaign_budgets.assert_not_called()

    @patch("google_ads_mcp.client.GoogleAdsClient")
    def test_add_keywords_dry_run(self, mock_client_class):
        """Test adding keywords in dry run mode."""
        mock_client = MagicMock()
        mock_client_class.load_from_storage.return_value = mock_client
        mock_client.login_customer_id = "123456789"

        client = GoogleAdsApiClient(config_path="fake.yaml", dry_run=True)
        result = client.add_keywords(
            ad_group_id="12345",
            keywords=["test keyword 1", "test keyword 2"],
        )

        assert result.success is True
        assert "2 keywords would be added" in result.error_message


class TestCustomerIdHandling:
    """Tests for customer ID handling."""

    @patch("google_ads_mcp.client.GoogleAdsClient")
    def test_strips_dashes(self, mock_client_class):
        """Test that dashes are stripped from customer IDs."""
        mock_client = MagicMock()
        mock_client_class.load_from_storage.return_value = mock_client
        mock_client.login_customer_id = None

        client = GoogleAdsApiClient(config_path="fake.yaml", dry_run=True)
        cid = client._get_customer_id("123-456-7890")
        assert cid == "1234567890"

    @patch("google_ads_mcp.client.GoogleAdsClient")
    def test_uses_login_customer_id_as_default(self, mock_client_class):
        """Test that login_customer_id is used when no customer_id provided."""
        mock_client = MagicMock()
        mock_client_class.load_from_storage.return_value = mock_client
        mock_client.login_customer_id = "9876543210"

        client = GoogleAdsApiClient(config_path="fake.yaml", dry_run=True)
        cid = client._get_customer_id(None)
        assert cid == "9876543210"

    @patch("google_ads_mcp.client.GoogleAdsClient")
    def test_raises_without_customer_id(self, mock_client_class):
        """Test that error is raised when no customer ID available."""
        mock_client = MagicMock()
        mock_client_class.load_from_storage.return_value = mock_client
        mock_client.login_customer_id = None

        client = GoogleAdsApiClient(config_path="fake.yaml", dry_run=True)
        client._login_customer_id = None

        with pytest.raises(ValueError, match="customer_id must be provided"):
            client._get_customer_id(None)


class TestNegativeKeywordValidation:
    """Tests for negative keyword parameter validation."""

    @patch("google_ads_mcp.client.GoogleAdsClient")
    def test_requires_campaign_or_ad_group(self, mock_client_class):
        """Test that either campaign_id or ad_group_id is required."""
        mock_client = MagicMock()
        mock_client_class.load_from_storage.return_value = mock_client
        mock_client.login_customer_id = "123456789"

        client = GoogleAdsApiClient(config_path="fake.yaml", dry_run=True)
        result = client.add_negative_keywords(
            keywords=["test"],
            # Neither campaign_id nor ad_group_id provided
        )

        assert result.success is False
        assert "Either campaign_id or ad_group_id" in result.error_message

    @patch("google_ads_mcp.client.GoogleAdsClient")
    def test_rejects_both_campaign_and_ad_group(self, mock_client_class):
        """Test that providing both campaign_id and ad_group_id is rejected."""
        mock_client = MagicMock()
        mock_client_class.load_from_storage.return_value = mock_client
        mock_client.login_customer_id = "123456789"

        client = GoogleAdsApiClient(config_path="fake.yaml", dry_run=True)
        result = client.add_negative_keywords(
            keywords=["test"],
            campaign_id="123",
            ad_group_id="456",
        )

        assert result.success is False
        assert "not both" in result.error_message


class TestResponsiveSearchAdValidation:
    """Tests for RSA parameter validation."""

    @patch("google_ads_mcp.client.GoogleAdsClient")
    def test_requires_minimum_headlines(self, mock_client_class):
        """Test that at least 3 headlines are required."""
        mock_client = MagicMock()
        mock_client_class.load_from_storage.return_value = mock_client
        mock_client.login_customer_id = "123456789"

        client = GoogleAdsApiClient(config_path="fake.yaml", dry_run=True)
        result = client.create_responsive_search_ad(
            ad_group_id="12345",
            headlines=["Only two", "headlines"],
            descriptions=["Desc 1", "Desc 2"],
            final_url="https://example.com",
        )

        assert result.success is False
        assert "At least 3 headlines" in result.error_message

    @patch("google_ads_mcp.client.GoogleAdsClient")
    def test_requires_minimum_descriptions(self, mock_client_class):
        """Test that at least 2 descriptions are required."""
        mock_client = MagicMock()
        mock_client_class.load_from_storage.return_value = mock_client
        mock_client.login_customer_id = "123456789"

        client = GoogleAdsApiClient(config_path="fake.yaml", dry_run=True)
        result = client.create_responsive_search_ad(
            ad_group_id="12345",
            headlines=["H1", "H2", "H3"],
            descriptions=["Only one description"],
            final_url="https://example.com",
        )

        assert result.success is False
        assert "At least 2 descriptions" in result.error_message
