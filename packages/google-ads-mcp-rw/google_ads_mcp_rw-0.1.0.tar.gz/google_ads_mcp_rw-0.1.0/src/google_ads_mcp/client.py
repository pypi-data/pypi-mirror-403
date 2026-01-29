"""Google Ads API client with read and write capabilities."""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException


class MatchType(str, Enum):
    """Keyword match types."""

    BROAD = "BROAD"
    PHRASE = "PHRASE"
    EXACT = "EXACT"


class CampaignStatus(str, Enum):
    """Campaign status values."""

    ENABLED = "ENABLED"
    PAUSED = "PAUSED"


class AdGroupStatus(str, Enum):
    """Ad group status values."""

    ENABLED = "ENABLED"
    PAUSED = "PAUSED"


@dataclass
class MutationResult:
    """Result of a mutation operation."""

    success: bool
    resource_name: str | None = None
    resource_id: str | None = None
    error_message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "resource_name": self.resource_name,
            "resource_id": self.resource_id,
            "error_message": self.error_message,
        }


class GoogleAdsApiClient:
    """Client for Google Ads API with read and write operations."""

    def __init__(
        self,
        config_path: str | None = None,
        dry_run: bool = False,
    ):
        """Initialize the Google Ads client.

        Args:
            config_path: Path to google-ads.yaml config file.
                        Defaults to GOOGLE_ADS_CONFIG_PATH env var or ./google-ads.yaml
            dry_run: If True, mutations will be validated but not executed.
        """
        self.dry_run = dry_run

        if config_path is None:
            config_path = os.environ.get("GOOGLE_ADS_CONFIG_PATH", "google-ads.yaml")

        self.client = GoogleAdsClient.load_from_storage(config_path)

        # Get login_customer_id from config for MCC access
        self._login_customer_id = getattr(
            self.client, "login_customer_id", None
        ) or os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")

    def _get_customer_id(self, customer_id: str | None) -> str:
        """Get the customer ID, stripping any dashes."""
        if customer_id:
            return customer_id.replace("-", "")
        if self._login_customer_id:
            return self._login_customer_id.replace("-", "")
        raise ValueError("customer_id must be provided or set in config/environment")

    # =========================================================================
    # READ OPERATIONS
    # =========================================================================

    def list_accessible_accounts(self) -> list[dict[str, Any]]:
        """List all Google Ads accounts accessible by this credential.

        Returns:
            List of account info dictionaries with id, name, etc.
        """
        customer_service = self.client.get_service("CustomerService")
        accessible_customers = customer_service.list_accessible_customers()

        accounts = []
        for resource_name in accessible_customers.resource_names:
            customer_id = resource_name.split("/")[-1]
            accounts.append(
                {
                    "customer_id": customer_id,
                    "resource_name": resource_name,
                }
            )

        return accounts

    def execute_query(
        self,
        query: str,
        customer_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a GAQL query.

        Args:
            query: The Google Ads Query Language (GAQL) query
            customer_id: Customer ID to query (optional if set in config)

        Returns:
            List of result rows as dictionaries
        """
        ga_service = self.client.get_service("GoogleAdsService")
        cid = self._get_customer_id(customer_id)

        response = ga_service.search(customer_id=cid, query=query)

        results = []
        for row in response:
            # Convert protobuf to dict - simplified extraction
            row_dict = self._proto_to_dict(row)
            results.append(row_dict)

        return results

    def _proto_to_dict(self, proto_obj: Any) -> dict[str, Any]:
        """Convert a protobuf object to a dictionary."""
        from google.protobuf.json_format import MessageToDict

        return MessageToDict(proto_obj._pb, preserving_proto_field_name=True)

    # =========================================================================
    # CAMPAIGN OPERATIONS
    # =========================================================================

    def create_campaign(
        self,
        name: str,
        customer_id: str | None = None,
        budget_amount_micros: int = 10_000_000,  # $10 default
        advertising_channel_type: str = "SEARCH",
        status: CampaignStatus = CampaignStatus.PAUSED,
    ) -> MutationResult:
        """Create a new campaign.

        Args:
            name: Campaign name
            customer_id: Customer ID (optional if set in config)
            budget_amount_micros: Daily budget in micros (1,000,000 = $1)
            advertising_channel_type: Channel type (SEARCH, DISPLAY, etc.)
            status: Initial campaign status (default: PAUSED for safety)

        Returns:
            MutationResult with success status and created resource info
        """
        cid = self._get_customer_id(customer_id)

        try:
            # First create a budget
            campaign_budget_service = self.client.get_service("CampaignBudgetService")
            budget_operation = self.client.get_type("CampaignBudgetOperation")
            budget = budget_operation.create
            budget.name = f"Budget for {name}"
            budget.amount_micros = budget_amount_micros
            budget.delivery_method = self.client.enums.BudgetDeliveryMethodEnum.STANDARD

            if self.dry_run:
                return MutationResult(
                    success=True,
                    error_message="DRY RUN: Campaign would be created",
                )

            budget_response = campaign_budget_service.mutate_campaign_budgets(
                customer_id=cid, operations=[budget_operation]
            )
            budget_resource_name = budget_response.results[0].resource_name

            # Now create the campaign
            campaign_service = self.client.get_service("CampaignService")
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign = campaign_operation.create
            campaign.name = name
            campaign.campaign_budget = budget_resource_name
            campaign.advertising_channel_type = getattr(
                self.client.enums.AdvertisingChannelTypeEnum,
                advertising_channel_type,
            )
            campaign.status = getattr(
                self.client.enums.CampaignStatusEnum, status.value
            )

            # Set manual CPC bidding
            campaign.manual_cpc.enhanced_cpc_enabled = False

            # Set network settings for Search campaigns
            if advertising_channel_type == "SEARCH":
                campaign.network_settings.target_google_search = True
                campaign.network_settings.target_search_network = True
                campaign.network_settings.target_content_network = False

            response = campaign_service.mutate_campaigns(
                customer_id=cid, operations=[campaign_operation]
            )

            resource_name = response.results[0].resource_name
            campaign_id = resource_name.split("/")[-1]

            return MutationResult(
                success=True,
                resource_name=resource_name,
                resource_id=campaign_id,
            )

        except GoogleAdsException as ex:
            return MutationResult(
                success=False,
                error_message=str(ex.failure.errors[0].message),
            )

    def pause_campaign(
        self,
        campaign_id: str,
        customer_id: str | None = None,
    ) -> MutationResult:
        """Pause a campaign.

        Args:
            campaign_id: Campaign ID to pause
            customer_id: Customer ID (optional if set in config)

        Returns:
            MutationResult with success status
        """
        return self._update_campaign_status(
            campaign_id, CampaignStatus.PAUSED, customer_id
        )

    def enable_campaign(
        self,
        campaign_id: str,
        customer_id: str | None = None,
    ) -> MutationResult:
        """Enable a campaign.

        Args:
            campaign_id: Campaign ID to enable
            customer_id: Customer ID (optional if set in config)

        Returns:
            MutationResult with success status
        """
        return self._update_campaign_status(
            campaign_id, CampaignStatus.ENABLED, customer_id
        )

    def _update_campaign_status(
        self,
        campaign_id: str,
        status: CampaignStatus,
        customer_id: str | None = None,
    ) -> MutationResult:
        """Update campaign status."""
        cid = self._get_customer_id(customer_id)

        if self.dry_run:
            return MutationResult(
                success=True,
                resource_name=f"customers/{cid}/campaigns/{campaign_id}",
                error_message=f"DRY RUN: Campaign would be set to {status.value}",
            )

        try:
            campaign_service = self.client.get_service("CampaignService")
            campaign_operation = self.client.get_type("CampaignOperation")
            campaign = campaign_operation.update
            campaign.resource_name = f"customers/{cid}/campaigns/{campaign_id}"
            campaign.status = getattr(
                self.client.enums.CampaignStatusEnum, status.value
            )

            # Set the update mask
            self.client.copy_from(
                campaign_operation.update_mask,
                self.client.get_type("FieldMask")(paths=["status"]),
            )

            response = campaign_service.mutate_campaigns(
                customer_id=cid, operations=[campaign_operation]
            )

            return MutationResult(
                success=True,
                resource_name=response.results[0].resource_name,
                resource_id=campaign_id,
            )

        except GoogleAdsException as ex:
            return MutationResult(
                success=False,
                error_message=str(ex.failure.errors[0].message),
            )

    # =========================================================================
    # AD GROUP OPERATIONS
    # =========================================================================

    def create_ad_group(
        self,
        campaign_id: str,
        name: str,
        customer_id: str | None = None,
        cpc_bid_micros: int = 2_000_000,  # $2 default
        status: AdGroupStatus = AdGroupStatus.ENABLED,
    ) -> MutationResult:
        """Create an ad group in a campaign.

        Args:
            campaign_id: Campaign ID to add the ad group to
            name: Ad group name
            customer_id: Customer ID (optional if set in config)
            cpc_bid_micros: Default CPC bid in micros (1,000,000 = $1)
            status: Initial ad group status

        Returns:
            MutationResult with success status and created resource info
        """
        cid = self._get_customer_id(customer_id)

        if self.dry_run:
            return MutationResult(
                success=True,
                error_message="DRY RUN: Ad group would be created",
            )

        try:
            ad_group_service = self.client.get_service("AdGroupService")
            ad_group_operation = self.client.get_type("AdGroupOperation")
            ad_group = ad_group_operation.create
            ad_group.name = name
            ad_group.campaign = f"customers/{cid}/campaigns/{campaign_id}"
            ad_group.status = getattr(self.client.enums.AdGroupStatusEnum, status.value)
            ad_group.type_ = self.client.enums.AdGroupTypeEnum.SEARCH_STANDARD
            ad_group.cpc_bid_micros = cpc_bid_micros

            response = ad_group_service.mutate_ad_groups(
                customer_id=cid, operations=[ad_group_operation]
            )

            resource_name = response.results[0].resource_name
            ad_group_id = resource_name.split("/")[-1]

            return MutationResult(
                success=True,
                resource_name=resource_name,
                resource_id=ad_group_id,
            )

        except GoogleAdsException as ex:
            return MutationResult(
                success=False,
                error_message=str(ex.failure.errors[0].message),
            )

    def pause_ad_group(
        self,
        ad_group_id: str,
        customer_id: str | None = None,
    ) -> MutationResult:
        """Pause an ad group.

        Args:
            ad_group_id: Ad group ID to pause
            customer_id: Customer ID (optional if set in config)

        Returns:
            MutationResult with success status
        """
        return self._update_ad_group_status(
            ad_group_id, AdGroupStatus.PAUSED, customer_id
        )

    def enable_ad_group(
        self,
        ad_group_id: str,
        customer_id: str | None = None,
    ) -> MutationResult:
        """Enable an ad group.

        Args:
            ad_group_id: Ad group ID to enable
            customer_id: Customer ID (optional if set in config)

        Returns:
            MutationResult with success status
        """
        return self._update_ad_group_status(
            ad_group_id, AdGroupStatus.ENABLED, customer_id
        )

    def _update_ad_group_status(
        self,
        ad_group_id: str,
        status: AdGroupStatus,
        customer_id: str | None = None,
    ) -> MutationResult:
        """Update ad group status."""
        cid = self._get_customer_id(customer_id)

        if self.dry_run:
            return MutationResult(
                success=True,
                resource_name=f"customers/{cid}/adGroups/{ad_group_id}",
                error_message=f"DRY RUN: Ad group would be set to {status.value}",
            )

        try:
            ad_group_service = self.client.get_service("AdGroupService")
            ad_group_operation = self.client.get_type("AdGroupOperation")
            ad_group = ad_group_operation.update
            ad_group.resource_name = f"customers/{cid}/adGroups/{ad_group_id}"
            ad_group.status = getattr(self.client.enums.AdGroupStatusEnum, status.value)

            self.client.copy_from(
                ad_group_operation.update_mask,
                self.client.get_type("FieldMask")(paths=["status"]),
            )

            response = ad_group_service.mutate_ad_groups(
                customer_id=cid, operations=[ad_group_operation]
            )

            return MutationResult(
                success=True,
                resource_name=response.results[0].resource_name,
                resource_id=ad_group_id,
            )

        except GoogleAdsException as ex:
            return MutationResult(
                success=False,
                error_message=str(ex.failure.errors[0].message),
            )

    def update_ad_group_bid(
        self,
        ad_group_id: str,
        cpc_bid_micros: int,
        customer_id: str | None = None,
    ) -> MutationResult:
        """Update the CPC bid for an ad group.

        Args:
            ad_group_id: Ad group ID to update
            cpc_bid_micros: New CPC bid in micros (1,000,000 = $1)
            customer_id: Customer ID (optional if set in config)

        Returns:
            MutationResult with success status
        """
        cid = self._get_customer_id(customer_id)

        if self.dry_run:
            return MutationResult(
                success=True,
                resource_name=f"customers/{cid}/adGroups/{ad_group_id}",
                error_message=f"DRY RUN: Bid would be set to {cpc_bid_micros} micros",
            )

        try:
            ad_group_service = self.client.get_service("AdGroupService")
            ad_group_operation = self.client.get_type("AdGroupOperation")
            ad_group = ad_group_operation.update
            ad_group.resource_name = f"customers/{cid}/adGroups/{ad_group_id}"
            ad_group.cpc_bid_micros = cpc_bid_micros

            self.client.copy_from(
                ad_group_operation.update_mask,
                self.client.get_type("FieldMask")(paths=["cpc_bid_micros"]),
            )

            response = ad_group_service.mutate_ad_groups(
                customer_id=cid, operations=[ad_group_operation]
            )

            return MutationResult(
                success=True,
                resource_name=response.results[0].resource_name,
                resource_id=ad_group_id,
            )

        except GoogleAdsException as ex:
            return MutationResult(
                success=False,
                error_message=str(ex.failure.errors[0].message),
            )

    # =========================================================================
    # KEYWORD OPERATIONS
    # =========================================================================

    def add_keywords(
        self,
        ad_group_id: str,
        keywords: list[str],
        customer_id: str | None = None,
        match_type: MatchType = MatchType.BROAD,
    ) -> MutationResult:
        """Add keywords to an ad group.

        Args:
            ad_group_id: Ad group ID to add keywords to
            keywords: List of keyword texts
            customer_id: Customer ID (optional if set in config)
            match_type: Keyword match type (BROAD, PHRASE, EXACT)

        Returns:
            MutationResult with success status
        """
        cid = self._get_customer_id(customer_id)

        if self.dry_run:
            return MutationResult(
                success=True,
                error_message=f"DRY RUN: {len(keywords)} keywords would be added",
            )

        try:
            ad_group_criterion_service = self.client.get_service(
                "AdGroupCriterionService"
            )

            operations = []
            for keyword in keywords:
                operation = self.client.get_type("AdGroupCriterionOperation")
                criterion = operation.create
                criterion.ad_group = f"customers/{cid}/adGroups/{ad_group_id}"
                criterion.status = self.client.enums.AdGroupCriterionStatusEnum.ENABLED
                criterion.keyword.text = keyword
                criterion.keyword.match_type = getattr(
                    self.client.enums.KeywordMatchTypeEnum, match_type.value
                )
                operations.append(operation)

            response = ad_group_criterion_service.mutate_ad_group_criteria(
                customer_id=cid, operations=operations
            )

            return MutationResult(
                success=True,
                resource_name=(
                    response.results[0].resource_name if response.results else None
                ),
                resource_id=str(len(response.results)),
            )

        except GoogleAdsException as ex:
            return MutationResult(
                success=False,
                error_message=str(ex.failure.errors[0].message),
            )

    def add_negative_keywords(
        self,
        keywords: list[str],
        customer_id: str | None = None,
        campaign_id: str | None = None,
        ad_group_id: str | None = None,
        match_type: MatchType = MatchType.BROAD,
    ) -> MutationResult:
        """Add negative keywords to a campaign or ad group.

        Args:
            keywords: List of negative keyword texts
            customer_id: Customer ID (optional if set in config)
            campaign_id: Campaign ID for campaign-level negatives
            ad_group_id: Ad group ID for ad group-level negatives
            match_type: Keyword match type (BROAD, PHRASE, EXACT)

        Note: Either campaign_id or ad_group_id must be provided, not both.

        Returns:
            MutationResult with success status
        """
        cid = self._get_customer_id(customer_id)

        if not campaign_id and not ad_group_id:
            return MutationResult(
                success=False,
                error_message="Either campaign_id or ad_group_id must be provided",
            )

        if campaign_id and ad_group_id:
            return MutationResult(
                success=False,
                error_message="Provide either campaign_id or ad_group_id, not both",
            )

        if self.dry_run:
            level = "campaign" if campaign_id else "ad group"
            return MutationResult(
                success=True,
                error_message=f"DRY RUN: {len(keywords)} negative keywords "
                f"would be added to {level}",
            )

        try:
            if campaign_id:
                # Campaign-level negative keywords
                campaign_criterion_service = self.client.get_service(
                    "CampaignCriterionService"
                )

                operations = []
                for keyword in keywords:
                    operation = self.client.get_type("CampaignCriterionOperation")
                    criterion = operation.create
                    criterion.campaign = f"customers/{cid}/campaigns/{campaign_id}"
                    criterion.negative = True
                    criterion.keyword.text = keyword
                    criterion.keyword.match_type = getattr(
                        self.client.enums.KeywordMatchTypeEnum, match_type.value
                    )
                    operations.append(operation)

                response = campaign_criterion_service.mutate_campaign_criteria(
                    customer_id=cid, operations=operations
                )
            else:
                # Ad group-level negative keywords
                ad_group_criterion_service = self.client.get_service(
                    "AdGroupCriterionService"
                )

                operations = []
                for keyword in keywords:
                    operation = self.client.get_type("AdGroupCriterionOperation")
                    criterion = operation.create
                    criterion.ad_group = f"customers/{cid}/adGroups/{ad_group_id}"
                    criterion.negative = True
                    criterion.keyword.text = keyword
                    criterion.keyword.match_type = getattr(
                        self.client.enums.KeywordMatchTypeEnum, match_type.value
                    )
                    operations.append(operation)

                response = ad_group_criterion_service.mutate_ad_group_criteria(
                    customer_id=cid, operations=operations
                )

            return MutationResult(
                success=True,
                resource_name=(
                    response.results[0].resource_name if response.results else None
                ),
                resource_id=str(len(response.results)),
            )

        except GoogleAdsException as ex:
            return MutationResult(
                success=False,
                error_message=str(ex.failure.errors[0].message),
            )

    # =========================================================================
    # AD OPERATIONS
    # =========================================================================

    def create_responsive_search_ad(
        self,
        ad_group_id: str,
        headlines: list[str],
        descriptions: list[str],
        final_url: str,
        customer_id: str | None = None,
        path1: str | None = None,
        path2: str | None = None,
    ) -> MutationResult:
        """Create a responsive search ad.

        Args:
            ad_group_id: Ad group ID to add the ad to
            headlines: List of headlines (3-15 required, max 30 chars each)
            descriptions: List of descriptions (2-4 required, max 90 chars each)
            final_url: Landing page URL
            customer_id: Customer ID (optional if set in config)
            path1: Optional display URL path 1 (max 15 chars)
            path2: Optional display URL path 2 (max 15 chars)

        Returns:
            MutationResult with success status and created resource info
        """
        cid = self._get_customer_id(customer_id)

        # Validate inputs
        if len(headlines) < 3:
            return MutationResult(
                success=False,
                error_message="At least 3 headlines required",
            )
        if len(descriptions) < 2:
            return MutationResult(
                success=False,
                error_message="At least 2 descriptions required",
            )

        if self.dry_run:
            return MutationResult(
                success=True,
                error_message="DRY RUN: Responsive search ad would be created",
            )

        try:
            ad_group_ad_service = self.client.get_service("AdGroupAdService")
            operation = self.client.get_type("AdGroupAdOperation")
            ad_group_ad = operation.create
            ad_group_ad.ad_group = f"customers/{cid}/adGroups/{ad_group_id}"
            ad_group_ad.status = self.client.enums.AdGroupAdStatusEnum.ENABLED

            ad = ad_group_ad.ad
            ad.final_urls.append(final_url)

            # Add headlines (max 15, each max 30 chars)
            for headline in headlines[:15]:
                headline_asset = self.client.get_type("AdTextAsset")
                headline_asset.text = headline[:30]
                ad.responsive_search_ad.headlines.append(headline_asset)

            # Add descriptions (max 4, each max 90 chars)
            for description in descriptions[:4]:
                desc_asset = self.client.get_type("AdTextAsset")
                desc_asset.text = description[:90]
                ad.responsive_search_ad.descriptions.append(desc_asset)

            # Add display URL paths if provided
            if path1:
                ad.responsive_search_ad.path1 = path1[:15]
            if path2:
                ad.responsive_search_ad.path2 = path2[:15]

            response = ad_group_ad_service.mutate_ad_group_ads(
                customer_id=cid, operations=[operation]
            )

            resource_name = response.results[0].resource_name
            # Extract ad ID from resource name
            # Format: customers/{cid}/adGroupAds/{ad_group_id}~{ad_id}
            ad_id = resource_name.split("~")[-1] if "~" in resource_name else None

            return MutationResult(
                success=True,
                resource_name=resource_name,
                resource_id=ad_id,
            )

        except GoogleAdsException as ex:
            return MutationResult(
                success=False,
                error_message=str(ex.failure.errors[0].message),
            )
