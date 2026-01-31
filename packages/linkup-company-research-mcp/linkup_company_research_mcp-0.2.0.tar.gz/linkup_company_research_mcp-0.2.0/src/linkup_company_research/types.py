"""Type definitions for Linkup Company Research MCP."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class OutputFormat(str, Enum):
    """Output format options for Linkup API responses."""
    ANSWER = "answer"           # Returns sourcedAnswer (natural language with sources)
    STRUCTURED = "structured"   # Returns structuredOutput (JSON following schema)


@dataclass
class SearchParams:
    """Parameters for Linkup API search requests."""

    # Date filters (YYYY-MM-DD format)
    from_date: Optional[str] = None
    to_date: Optional[str] = None

    # Domain filters (up to 50 each)
    include_domains: Optional[list[str]] = field(default_factory=list)
    exclude_domains: Optional[list[str]] = field(default_factory=list)

    # Result options
    include_images: bool = False
    max_results: Optional[int] = None

    # Output format
    output_format: OutputFormat = OutputFormat.ANSWER


def parse_domain_list(domains: str) -> list[str]:
    """Parse comma-separated domain string to list (max 50 domains)."""
    if not domains:
        return []
    return [d.strip() for d in domains.split(",") if d.strip()][:50]


def build_search_params(
    output_format: str = "answer",
    from_date: str = "",
    to_date: str = "",
    include_domains: str = "",
    exclude_domains: str = "",
    include_images: bool = False,
    max_results: int = 10
) -> SearchParams:
    """Build SearchParams from tool string arguments."""
    return SearchParams(
        output_format=OutputFormat(output_format),
        from_date=from_date if from_date else None,
        to_date=to_date if to_date else None,
        include_domains=parse_domain_list(include_domains),
        exclude_domains=parse_domain_list(exclude_domains),
        include_images=include_images,
        max_results=max_results if max_results else None
    )
