"""Linkup Company Research MCP Server.

A comprehensive company research platform powered by Linkup's agentic search API.
Provides 10 research tools with dual output format support (natural language or structured JSON).
"""

import json
import os
from typing import Literal, Optional

import httpx
from mcp.server.fastmcp import FastMCP

from .prompts import get_prompt
from .schemas import get_schema
from .types import OutputFormat, SearchParams, build_search_params

mcp = FastMCP("linkup-company-research")

LINKUP_API_URL = "https://api.linkup.so/v1/search"


# =============================================================================
# CORE FUNCTIONS
# =============================================================================


async def _search(
    query: str,
    depth: Literal["standard", "deep"] = "deep",
    params: Optional[SearchParams] = None,
    schema: Optional[dict] = None,
) -> dict:
    """Execute a Linkup search query with full parameter support.

    Args:
        query: The search query/prompt
        depth: Search depth - "standard" (fast) or "deep" (comprehensive)
        params: Search parameters (dates, domains, output format, etc.)
        schema: JSON schema for structured output (required when output_format is STRUCTURED)

    Returns:
        API response dictionary
    """
    params = params or SearchParams()

    # Build API payload
    payload: dict = {
        "q": query,
        "depth": depth,
    }

    # Set output type based on format choice
    if params.output_format == OutputFormat.STRUCTURED:
        if not schema:
            raise ValueError("Schema required for structured output")
        payload["outputType"] = "structured"
        payload["structuredOutputSchema"] = json.dumps(schema)
    else:
        payload["outputType"] = "sourcedAnswer"

    # Add optional parameters
    if params.from_date:
        payload["fromDate"] = params.from_date
    if params.to_date:
        payload["toDate"] = params.to_date
    if params.include_domains:
        payload["includeDomains"] = params.include_domains[:50]
    if params.exclude_domains:
        payload["excludeDomains"] = params.exclude_domains[:50]
    if params.include_images:
        payload["includeImages"] = True
    if params.max_results:
        payload["maxResults"] = params.max_results

    # Execute request with increased timeout for deep searches
    timeout = 120.0 if depth == "deep" else 60.0
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            LINKUP_API_URL,
            headers={"Authorization": f"Bearer {os.environ['LINKUP_API_KEY']}"},
            json=payload,
        )
        response.raise_for_status()
        return response.json()


def _format_response(data: dict, output_format: OutputFormat) -> str:
    """Format Linkup response based on output type.

    Args:
        data: API response dictionary
        output_format: ANSWER for natural language, STRUCTURED for JSON

    Returns:
        Formatted response string
    """
    if output_format == OutputFormat.STRUCTURED:
        # For structured output, the response IS the structured data directly
        # (not wrapped in a "structuredOutput" field)
        return json.dumps(data, indent=2)
    else:
        # Format sourcedAnswer with sources
        result = data.get("answer", "No answer found.")
        sources = data.get("sources", [])
        if sources:
            result += "\n\n**Sources:**\n"
            for src in sources[:5]:
                name = src.get("name") or src.get("title", "Source")
                url = src.get("url", "")
                result += f"- [{name}]({url})\n"
        return result


# =============================================================================
# EXISTING TOOLS - ENHANCED
# =============================================================================


@mcp.tool()
async def company_overview(
    company_name: str,
    output_format: str = "answer",
    include_images: bool = False,
    max_results: int = 10,
) -> str:
    """Get a comprehensive overview of a company.

    Researches the company's website, LinkedIn, and press coverage to provide
    detailed information about what they do, their industry, size, and business model.

    Args:
        company_name: The name of the company to research
        output_format: "answer" for natural language with sources, "structured" for JSON
        include_images: Include relevant company images (logos, office, products)
        max_results: Maximum number of sources to consider (1-50)
    """
    params = build_search_params(
        output_format=output_format,
        include_images=include_images,
        max_results=max_results,
    )

    prompt = get_prompt("company_overview", company_name=company_name)
    schema = get_schema("company_overview") if params.output_format == OutputFormat.STRUCTURED else None

    data = await _search(prompt, depth="deep", params=params, schema=schema)
    return _format_response(data, params.output_format)


@mcp.tool()
async def company_news(
    company_name: str,
    topic: str = "",
    output_format: str = "answer",
    from_date: str = "",
    to_date: str = "",
    include_domains: str = "",
    exclude_domains: str = "",
    max_results: int = 10,
) -> str:
    """Get the latest news and developments about a company.

    Searches news sources, press releases, and publications for recent
    coverage of the company. Supports filtering by date range and topic.

    Args:
        company_name: The name of the company to research
        topic: Optional topic filter (e.g., 'funding', 'product launch', 'earnings', 'partnerships')
        output_format: "answer" for natural language with sources, "structured" for JSON
        from_date: Start date for news (YYYY-MM-DD format)
        to_date: End date for news (YYYY-MM-DD format)
        include_domains: Comma-separated domains to include (e.g., "techcrunch.com,reuters.com")
        exclude_domains: Comma-separated domains to exclude
        max_results: Maximum number of news items (1-50)
    """
    params = build_search_params(
        output_format=output_format,
        from_date=from_date,
        to_date=to_date,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
        max_results=max_results,
    )

    prompt = get_prompt(
        "company_news",
        company_name=company_name,
        topic=topic,
        from_date=from_date,
        to_date=to_date,
    )
    schema = get_schema("company_news") if params.output_format == OutputFormat.STRUCTURED else None

    data = await _search(prompt, depth="standard", params=params, schema=schema)
    return _format_response(data, params.output_format)


@mcp.tool()
async def competitive_landscape(
    company_name: str,
    output_format: str = "answer",
    include_images: bool = False,
    max_results: int = 15,
) -> str:
    """Analyze a company's competitive position in their market.

    Identifies competitors, market positioning, differentiators, and competitive
    advantages through research of industry reports, review sites, and company materials.

    Args:
        company_name: The name of the company to research
        output_format: "answer" for natural language with sources, "structured" for JSON
        include_images: Include competitor logos and comparison visuals
        max_results: Maximum sources to consider (1-50)
    """
    params = build_search_params(
        output_format=output_format,
        include_images=include_images,
        max_results=max_results,
    )

    prompt = get_prompt("competitive_landscape", company_name=company_name)
    schema = get_schema("competitive_landscape") if params.output_format == OutputFormat.STRUCTURED else None

    data = await _search(prompt, depth="deep", params=params, schema=schema)
    return _format_response(data, params.output_format)


@mcp.tool()
async def company_financials(
    company_name: str,
    output_format: str = "answer",
    from_date: str = "",
    to_date: str = "",
    max_results: int = 15,
) -> str:
    """Get financial information about a company.

    Researches funding history, valuation, revenue, investors, and financial
    health through Crunchbase, press releases, and financial news.

    Args:
        company_name: The name of the company to research
        output_format: "answer" for natural language with sources, "structured" for JSON
        from_date: Start date for financial news (YYYY-MM-DD)
        to_date: End date for financial news (YYYY-MM-DD)
        max_results: Maximum sources to consider (1-50)
    """
    params = build_search_params(
        output_format=output_format,
        from_date=from_date,
        to_date=to_date,
        max_results=max_results,
    )

    prompt = get_prompt(
        "company_financials",
        company_name=company_name,
        from_date=from_date,
        to_date=to_date,
    )
    schema = get_schema("company_financials") if params.output_format == OutputFormat.STRUCTURED else None

    data = await _search(prompt, depth="deep", params=params, schema=schema)
    return _format_response(data, params.output_format)


@mcp.tool()
async def company_leadership(
    company_name: str,
    output_format: str = "answer",
    include_images: bool = False,
    max_results: int = 10,
) -> str:
    """Get information about a company's leadership team.

    Identifies executives, founders, board members, and advisors through
    company pages, LinkedIn, and press releases.

    Args:
        company_name: The name of the company to research
        output_format: "answer" for natural language with sources, "structured" for JSON
        include_images: Include executive headshots
        max_results: Maximum sources to consider (1-50)
    """
    params = build_search_params(
        output_format=output_format,
        include_images=include_images,
        max_results=max_results,
    )

    prompt = get_prompt("company_leadership", company_name=company_name)
    schema = get_schema("company_leadership") if params.output_format == OutputFormat.STRUCTURED else None

    data = await _search(prompt, depth="standard", params=params, schema=schema)
    return _format_response(data, params.output_format)


# =============================================================================
# NEW TOOLS
# =============================================================================


@mcp.tool()
async def company_clients(
    company_name: str,
    output_format: str = "answer",
    max_results: int = 15,
) -> str:
    """Find known clients, customers, and case studies for a company.

    Researches customer pages, case studies, press releases, and review sites
    to identify verified customers and their use cases.

    Args:
        company_name: The name of the company to research
        output_format: "answer" for natural language with sources, "structured" for JSON
        max_results: Maximum sources to consider (1-50)
    """
    params = build_search_params(
        output_format=output_format,
        max_results=max_results,
    )

    prompt = get_prompt("company_clients", company_name=company_name)
    schema = get_schema("company_clients") if params.output_format == OutputFormat.STRUCTURED else None

    data = await _search(prompt, depth="deep", params=params, schema=schema)
    return _format_response(data, params.output_format)


@mcp.tool()
async def company_technology(
    company_name: str,
    output_format: str = "answer",
    max_results: int = 15,
) -> str:
    """Research a company's technology stack, patents, and technical approach.

    Analyzes engineering blogs, job postings, tech detection tools, patents,
    and open source contributions to understand technical capabilities.

    Args:
        company_name: The name of the company to research
        output_format: "answer" for natural language with sources, "structured" for JSON
        max_results: Maximum sources to consider (1-50)
    """
    params = build_search_params(
        output_format=output_format,
        max_results=max_results,
    )

    prompt = get_prompt("company_technology", company_name=company_name)
    schema = get_schema("company_technology") if params.output_format == OutputFormat.STRUCTURED else None

    data = await _search(prompt, depth="deep", params=params, schema=schema)
    return _format_response(data, params.output_format)


@mcp.tool()
async def company_hiring(
    company_name: str,
    department: str = "",
    output_format: str = "answer",
    max_results: int = 15,
) -> str:
    """Get information about a company's hiring activity, job openings, and growth.

    Researches careers pages, job boards, LinkedIn, and Glassdoor to understand
    hiring patterns and employee growth signals.

    Args:
        company_name: The name of the company to research
        department: Optional department filter (e.g., "engineering", "sales", "marketing")
        output_format: "answer" for natural language with sources, "structured" for JSON
        max_results: Maximum sources to consider (1-50)
    """
    params = build_search_params(
        output_format=output_format,
        max_results=max_results,
    )

    prompt = get_prompt("company_hiring", company_name=company_name, department=department)
    schema = get_schema("company_hiring") if params.output_format == OutputFormat.STRUCTURED else None

    data = await _search(prompt, depth="standard", params=params, schema=schema)
    return _format_response(data, params.output_format)


@mcp.tool()
async def company_partnerships(
    company_name: str,
    output_format: str = "answer",
    max_results: int = 15,
) -> str:
    """Find partnerships, integrations, and strategic alliances for a company.

    Researches partner pages, integration marketplaces, press releases, and
    partner programs to map the company's ecosystem.

    Args:
        company_name: The name of the company to research
        output_format: "answer" for natural language with sources, "structured" for JSON
        max_results: Maximum sources to consider (1-50)
    """
    params = build_search_params(
        output_format=output_format,
        max_results=max_results,
    )

    prompt = get_prompt("company_partnerships", company_name=company_name)
    schema = get_schema("company_partnerships") if params.output_format == OutputFormat.STRUCTURED else None

    data = await _search(prompt, depth="deep", params=params, schema=schema)
    return _format_response(data, params.output_format)


@mcp.tool()
async def company_social_presence(
    company_name: str,
    output_format: str = "answer",
    include_images: bool = False,
    max_results: int = 15,
) -> str:
    """Analyze a company's social media presence and content strategy.

    Researches social profiles, content channels, community platforms, and
    executive thought leadership to understand their digital presence.

    Args:
        company_name: The name of the company to research
        output_format: "answer" for natural language with sources, "structured" for JSON
        include_images: Include social media profile images
        max_results: Maximum sources to consider (1-50)
    """
    params = build_search_params(
        output_format=output_format,
        include_images=include_images,
        max_results=max_results,
    )

    prompt = get_prompt("company_social_presence", company_name=company_name)
    schema = get_schema("company_social_presence") if params.output_format == OutputFormat.STRUCTURED else None

    data = await _search(prompt, depth="standard", params=params, schema=schema)
    return _format_response(data, params.output_format)


# =============================================================================
# MAIN
# =============================================================================


def main():
    """Run the MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
