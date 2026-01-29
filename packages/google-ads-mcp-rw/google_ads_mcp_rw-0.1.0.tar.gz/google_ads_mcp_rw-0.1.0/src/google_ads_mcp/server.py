"""MCP Server for Google Ads with read and write capabilities."""

from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import GoogleAdsApiClient, MatchType

# Initialize the MCP server
mcp = FastMCP(
    "google-ads",
    instructions="""Google Ads MCP Server with read AND write capabilities.

This server provides tools to manage Google Ads accounts, including:
- Querying campaigns, ad groups, keywords, and performance data (GAQL)
- Creating campaigns and ad groups
- Adding keywords and negative keywords
- Creating responsive search ads
- Pausing/enabling campaigns and ad groups
- Updating bids

IMPORTANT SAFETY NOTES:
- Use dry_run=True to validate operations before executing
- New campaigns are created PAUSED by default for safety
- Always verify customer_id before making changes
- Budget amounts are in MICROS (1,000,000 = $1.00)

The server uses google-ads.yaml for authentication. Set GOOGLE_ADS_CONFIG_PATH
environment variable to specify a custom config location.
""",
)


def _get_client(dry_run: bool = False) -> GoogleAdsApiClient:
    """Get a configured Google Ads API client."""
    config_path = os.environ.get("GOOGLE_ADS_CONFIG_PATH")
    return GoogleAdsApiClient(config_path=config_path, dry_run=dry_run)


# =============================================================================
# READ OPERATIONS
# =============================================================================


@mcp.tool()
def list_accounts() -> list[dict[str, Any]]:
    """List all Google Ads accounts accessible by this credential.

    Returns a list of accounts with their customer IDs that you can use
    for subsequent operations.

    Returns:
        List of account dictionaries with customer_id and resource_name
    """
    client = _get_client()
    return client.list_accessible_accounts()


@mcp.tool()
def execute_query(
    query: str,
    customer_id: str | None = None,
) -> list[dict[str, Any]]:
    """Execute a Google Ads Query Language (GAQL) query.

    Use this for any read operation - campaigns, ad groups, keywords,
    ads, metrics, etc.

    Common queries:
    - Campaigns: SELECT campaign.id, campaign.name FROM campaign
    - Ad groups: SELECT ad_group.id, ad_group.name FROM ad_group
    - Keywords: SELECT ad_group_criterion.keyword.text FROM ad_group_criterion
    - Metrics: SELECT campaign.name, metrics.clicks FROM campaign

    Args:
        query: The GAQL query to execute
        customer_id: Target customer ID (optional if set in config).
                    Use digits only, no dashes.

    Returns:
        List of result rows as dictionaries
    """
    client = _get_client()
    return client.execute_query(query, customer_id)


# =============================================================================
# CAMPAIGN OPERATIONS
# =============================================================================


@mcp.tool()
def create_campaign(
    name: str,
    customer_id: str | None = None,
    budget_amount_micros: int = 10_000_000,
    advertising_channel_type: str = "SEARCH",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a new Google Ads campaign.

    Creates a new campaign with the specified settings. For safety, campaigns
    are created in PAUSED status by default - use enable_campaign to start them.

    Args:
        name: Campaign name
        customer_id: Target customer ID (optional if set in config)
        budget_amount_micros: Daily budget in micros (1,000,000 = $1.00).
                             Default is $10/day.
        advertising_channel_type: Channel type - SEARCH, DISPLAY, SHOPPING, etc.
        dry_run: If True, validate but don't execute the operation

    Returns:
        Result with success status, resource_name, and campaign_id
    """
    client = _get_client(dry_run=dry_run)
    result = client.create_campaign(
        name=name,
        customer_id=customer_id,
        budget_amount_micros=budget_amount_micros,
        advertising_channel_type=advertising_channel_type,
    )
    return result.to_dict()


@mcp.tool()
def pause_campaign(
    campaign_id: str,
    customer_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Pause a campaign.

    Pausing stops ad serving but preserves all settings and history.

    Args:
        campaign_id: Campaign ID to pause
        customer_id: Target customer ID (optional if set in config)
        dry_run: If True, validate but don't execute

    Returns:
        Result with success status
    """
    client = _get_client(dry_run=dry_run)
    result = client.pause_campaign(campaign_id, customer_id)
    return result.to_dict()


@mcp.tool()
def enable_campaign(
    campaign_id: str,
    customer_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Enable a campaign.

    Enabling starts ad serving. Make sure budget, targeting, and ads
    are properly configured before enabling.

    Args:
        campaign_id: Campaign ID to enable
        customer_id: Target customer ID (optional if set in config)
        dry_run: If True, validate but don't execute

    Returns:
        Result with success status
    """
    client = _get_client(dry_run=dry_run)
    result = client.enable_campaign(campaign_id, customer_id)
    return result.to_dict()


# =============================================================================
# AD GROUP OPERATIONS
# =============================================================================


@mcp.tool()
def create_ad_group(
    campaign_id: str,
    name: str,
    customer_id: str | None = None,
    cpc_bid_micros: int = 2_000_000,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create an ad group in a campaign.

    Args:
        campaign_id: Campaign ID to add the ad group to
        name: Ad group name
        customer_id: Target customer ID (optional if set in config)
        cpc_bid_micros: Default CPC bid in micros (1,000,000 = $1.00).
                       Default is $2.00.
        dry_run: If True, validate but don't execute

    Returns:
        Result with success status, resource_name, and ad_group_id
    """
    client = _get_client(dry_run=dry_run)
    result = client.create_ad_group(
        campaign_id=campaign_id,
        name=name,
        customer_id=customer_id,
        cpc_bid_micros=cpc_bid_micros,
    )
    return result.to_dict()


@mcp.tool()
def pause_ad_group(
    ad_group_id: str,
    customer_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Pause an ad group.

    Args:
        ad_group_id: Ad group ID to pause
        customer_id: Target customer ID (optional if set in config)
        dry_run: If True, validate but don't execute

    Returns:
        Result with success status
    """
    client = _get_client(dry_run=dry_run)
    result = client.pause_ad_group(ad_group_id, customer_id)
    return result.to_dict()


@mcp.tool()
def enable_ad_group(
    ad_group_id: str,
    customer_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Enable an ad group.

    Args:
        ad_group_id: Ad group ID to enable
        customer_id: Target customer ID (optional if set in config)
        dry_run: If True, validate but don't execute

    Returns:
        Result with success status
    """
    client = _get_client(dry_run=dry_run)
    result = client.enable_ad_group(ad_group_id, customer_id)
    return result.to_dict()


@mcp.tool()
def update_ad_group_bid(
    ad_group_id: str,
    cpc_bid_micros: int,
    customer_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Update the CPC bid for an ad group.

    Args:
        ad_group_id: Ad group ID to update
        cpc_bid_micros: New CPC bid in micros (1,000,000 = $1.00)
        customer_id: Target customer ID (optional if set in config)
        dry_run: If True, validate but don't execute

    Returns:
        Result with success status
    """
    client = _get_client(dry_run=dry_run)
    result = client.update_ad_group_bid(
        ad_group_id=ad_group_id,
        cpc_bid_micros=cpc_bid_micros,
        customer_id=customer_id,
    )
    return result.to_dict()


# =============================================================================
# KEYWORD OPERATIONS
# =============================================================================


@mcp.tool()
def add_keywords(
    ad_group_id: str,
    keywords: list[str],
    customer_id: str | None = None,
    match_type: str = "BROAD",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Add keywords to an ad group.

    Args:
        ad_group_id: Ad group ID to add keywords to
        keywords: List of keyword texts to add
        customer_id: Target customer ID (optional if set in config)
        match_type: Keyword match type - BROAD, PHRASE, or EXACT.
                   BROAD matches related searches, PHRASE matches
                   the phrase with words before/after, EXACT matches
                   the exact query only.
        dry_run: If True, validate but don't execute

    Returns:
        Result with success status and count of keywords added
    """
    client = _get_client(dry_run=dry_run)
    result = client.add_keywords(
        ad_group_id=ad_group_id,
        keywords=keywords,
        customer_id=customer_id,
        match_type=MatchType(match_type),
    )
    return result.to_dict()


@mcp.tool()
def add_negative_keywords(
    keywords: list[str],
    customer_id: str | None = None,
    campaign_id: str | None = None,
    ad_group_id: str | None = None,
    match_type: str = "BROAD",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Add negative keywords to block irrelevant searches.

    Negative keywords prevent your ads from showing for certain searches.
    Add them at campaign level to affect all ad groups, or at ad group
    level for more targeted exclusions.

    Args:
        keywords: List of negative keyword texts
        customer_id: Target customer ID (optional if set in config)
        campaign_id: Campaign ID for campaign-level negatives
        ad_group_id: Ad group ID for ad group-level negatives
        match_type: Match type - BROAD, PHRASE, or EXACT
        dry_run: If True, validate but don't execute

    Note: Provide EITHER campaign_id OR ad_group_id, not both.

    Returns:
        Result with success status and count of negatives added
    """
    client = _get_client(dry_run=dry_run)
    result = client.add_negative_keywords(
        keywords=keywords,
        customer_id=customer_id,
        campaign_id=campaign_id,
        ad_group_id=ad_group_id,
        match_type=MatchType(match_type),
    )
    return result.to_dict()


# =============================================================================
# AD OPERATIONS
# =============================================================================


@mcp.tool()
def create_responsive_search_ad(
    ad_group_id: str,
    headlines: list[str],
    descriptions: list[str],
    final_url: str,
    customer_id: str | None = None,
    path1: str | None = None,
    path2: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a responsive search ad (RSA).

    RSAs dynamically combine headlines and descriptions to show the
    best performing combinations. Google recommends providing many
    variations for optimal performance.

    Args:
        ad_group_id: Ad group ID to add the ad to
        headlines: List of headline variations (3-15 required).
                  Each headline max 30 characters.
        descriptions: List of description variations (2-4 required).
                     Each description max 90 characters.
        final_url: Landing page URL where users go after clicking
        customer_id: Target customer ID (optional if set in config)
        path1: Display URL path 1 (max 15 chars, e.g., "products")
        path2: Display URL path 2 (max 15 chars, e.g., "shoes")
        dry_run: If True, validate but don't execute

    Returns:
        Result with success status, resource_name, and ad_id
    """
    client = _get_client(dry_run=dry_run)
    result = client.create_responsive_search_ad(
        ad_group_id=ad_group_id,
        headlines=headlines,
        descriptions=descriptions,
        final_url=final_url,
        customer_id=customer_id,
        path1=path1,
        path2=path2,
    )
    return result.to_dict()


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
