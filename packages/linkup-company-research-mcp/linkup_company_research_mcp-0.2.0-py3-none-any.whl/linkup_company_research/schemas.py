"""JSON schemas for structuredOutput mode in Linkup Company Research MCP."""

import json
from typing import Any


# =============================================================================
# EXISTING TOOLS - ENHANCED SCHEMAS
# =============================================================================

COMPANY_OVERVIEW_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "website": {"type": "string"},
        "description": {"type": "string"},
        "value_proposition": {"type": "string"},
        "industry": {"type": "string"},
        "sector": {"type": "string"},
        "headquarters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "state": {"type": "string"},
                "country": {"type": "string"}
            }
        },
        "other_locations": {"type": "array", "items": {"type": "string"}},
        "founded_year": {"type": "integer"},
        "employee_count": {"type": "string"},
        "employee_count_range": {"type": "string"},
        "business_model": {"type": "array", "items": {"type": "string"}},
        "products_services": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"}
                }
            }
        },
        "target_customers": {"type": "array", "items": {"type": "string"}},
        "linkedin_url": {"type": "string"},
        "mission_statement": {"type": "string"}
    },
    "required": ["company_name", "description"]
}

COMPANY_NEWS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "news_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "headline": {"type": "string"},
                    "date": {"type": "string"},
                    "source": {"type": "string"},
                    "url": {"type": "string"},
                    "summary": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": ["funding", "product", "partnership", "executive",
                                 "earnings", "expansion", "acquisition", "legal", "other"]
                    },
                    "sentiment": {
                        "type": "string",
                        "enum": ["positive", "negative", "neutral"]
                    }
                }
            }
        },
        "time_range": {
            "type": "object",
            "properties": {
                "from_date": {"type": "string"},
                "to_date": {"type": "string"}
            }
        },
        "total_news_count": {"type": "integer"}
    },
    "required": ["company_name", "news_items"]
}

COMPETITIVE_LANDSCAPE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "market_category": {"type": "string"},
        "market_position": {
            "type": "string",
            "enum": ["leader", "challenger", "follower", "niche", "emerging"]
        },
        "competitors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "website": {"type": "string"},
                    "type": {"type": "string", "enum": ["direct", "indirect"]},
                    "description": {"type": "string"},
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "weaknesses": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        "differentiators": {"type": "array", "items": {"type": "string"}},
        "competitive_advantages": {"type": "array", "items": {"type": "string"}},
        "competitive_threats": {"type": "array", "items": {"type": "string"}},
        "market_share_estimate": {"type": "string"},
        "market_size": {"type": "string"}
    },
    "required": ["company_name", "competitors"]
}

COMPANY_FINANCIALS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "total_funding": {"type": "string"},
        "funding_rounds": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "round": {"type": "string"},
                    "date": {"type": "string"},
                    "amount": {"type": "string"},
                    "lead_investors": {"type": "array", "items": {"type": "string"}},
                    "valuation": {"type": "string"}
                }
            }
        },
        "current_valuation": {
            "type": "object",
            "properties": {
                "amount": {"type": "string"},
                "date": {"type": "string"},
                "source": {"type": "string"}
            }
        },
        "investors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string", "enum": ["vc", "pe", "strategic", "angel", "corporate", "government"]}
                }
            }
        },
        "revenue": {
            "type": "object",
            "properties": {
                "amount": {"type": "string"},
                "type": {"type": "string", "enum": ["arr", "revenue", "gmv", "mrr"]},
                "growth_rate": {"type": "string"},
                "date": {"type": "string"}
            }
        },
        "profitability": {"type": "string"},
        "ipo_status": {
            "type": "string",
            "enum": ["public", "filed", "rumored", "planned", "private", "acquired"]
        },
        "stock_ticker": {"type": "string"},
        "recent_financial_news": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["company_name"]
}

COMPANY_LEADERSHIP_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "founders": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "title": {"type": "string"},
                    "is_active": {"type": "boolean"},
                    "background": {"type": "string"},
                    "linkedin_url": {"type": "string"}
                }
            }
        },
        "executives": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "title": {"type": "string"},
                    "joined_date": {"type": "string"},
                    "background": {"type": "string"},
                    "previous_companies": {"type": "array", "items": {"type": "string"}},
                    "linkedin_url": {"type": "string"}
                }
            }
        },
        "board_members": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "affiliation": {"type": "string"},
                    "role": {"type": "string"}
                }
            }
        },
        "advisors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "expertise": {"type": "string"}
                }
            }
        },
        "recent_changes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["hire", "departure", "promotion"]},
                    "person": {"type": "string"},
                    "role": {"type": "string"},
                    "date": {"type": "string"}
                }
            }
        }
    },
    "required": ["company_name"]
}


# =============================================================================
# NEW TOOLS - SCHEMAS
# =============================================================================

COMPANY_CLIENTS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "customer_count": {"type": "string"},
        "customer_segments": {"type": "array", "items": {"type": "string"}},
        "named_customers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "industry": {"type": "string"},
                    "verification": {
                        "type": "string",
                        "enum": ["case_study", "press_release", "logo", "review", "testimonial"]
                    },
                    "use_case": {"type": "string"},
                    "outcomes": {"type": "string"}
                }
            }
        },
        "industry_verticals": {"type": "array", "items": {"type": "string"}},
        "case_studies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "customer": {"type": "string"},
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "metrics": {"type": "string"},
                    "url": {"type": "string"}
                }
            }
        },
        "testimonials": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quote": {"type": "string"},
                    "author": {"type": "string"},
                    "company": {"type": "string"},
                    "title": {"type": "string"}
                }
            }
        }
    },
    "required": ["company_name"]
}

COMPANY_TECHNOLOGY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "core_technology": {"type": "string"},
        "tech_stack": {
            "type": "object",
            "properties": {
                "languages": {"type": "array", "items": {"type": "string"}},
                "frameworks": {"type": "array", "items": {"type": "string"}},
                "databases": {"type": "array", "items": {"type": "string"}},
                "infrastructure": {"type": "array", "items": {"type": "string"}},
                "cloud_providers": {"type": "array", "items": {"type": "string"}},
                "devops_tools": {"type": "array", "items": {"type": "string"}}
            }
        },
        "ai_ml_capabilities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "capability": {"type": "string"},
                    "description": {"type": "string"}
                }
            }
        },
        "patents": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "number": {"type": "string"},
                    "status": {"type": "string", "enum": ["granted", "pending", "filed"]},
                    "date": {"type": "string"}
                }
            }
        },
        "open_source": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "url": {"type": "string"},
                    "description": {"type": "string"},
                    "stars": {"type": "integer"}
                }
            }
        },
        "certifications": {"type": "array", "items": {"type": "string"}},
        "security_compliance": {"type": "array", "items": {"type": "string"}},
        "engineering_blog_url": {"type": "string"},
        "engineering_team_size": {"type": "string"},
        "technical_differentiators": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["company_name"]
}

COMPANY_HIRING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "total_open_positions": {"type": "integer"},
        "careers_page_url": {"type": "string"},
        "positions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "department": {"type": "string"},
                    "location": {"type": "string"},
                    "seniority": {"type": "string", "enum": ["entry", "mid", "senior", "lead", "executive"]},
                    "remote": {"type": "boolean"},
                    "url": {"type": "string"}
                }
            }
        },
        "departments_hiring": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "department": {"type": "string"},
                    "open_roles": {"type": "integer"}
                }
            }
        },
        "locations_hiring": {"type": "array", "items": {"type": "string"}},
        "remote_policy": {"type": "string"},
        "employee_growth": {
            "type": "object",
            "properties": {
                "current_count": {"type": "string"},
                "previous_count": {"type": "string"},
                "growth_rate": {"type": "string"},
                "trend": {"type": "string", "enum": ["growing", "stable", "declining"]}
            }
        },
        "glassdoor": {
            "type": "object",
            "properties": {
                "rating": {"type": "number"},
                "review_count": {"type": "integer"},
                "recommend_to_friend": {"type": "string"},
                "ceo_approval": {"type": "string"}
            }
        },
        "hiring_signals": {"type": "array", "items": {"type": "string"}},
        "notable_recent_hires": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "role": {"type": "string"},
                    "previous_company": {"type": "string"}
                }
            }
        }
    },
    "required": ["company_name"]
}

COMPANY_PARTNERSHIPS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "partnerships": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "partner_name": {"type": "string"},
                    "partner_website": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["strategic", "technology", "channel", "platform", "integration", "reseller", "consulting"]
                    },
                    "description": {"type": "string"},
                    "date_announced": {"type": "string"}
                }
            }
        },
        "integrations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "type": {"type": "string", "enum": ["native", "api", "third_party", "marketplace"]},
                    "description": {"type": "string"}
                }
            }
        },
        "partner_program": {
            "type": "object",
            "properties": {
                "exists": {"type": "boolean"},
                "name": {"type": "string"},
                "tiers": {"type": "array", "items": {"type": "string"}},
                "benefits": {"type": "array", "items": {"type": "string"}},
                "url": {"type": "string"}
            }
        },
        "marketplace": {
            "type": "object",
            "properties": {
                "exists": {"type": "boolean"},
                "name": {"type": "string"},
                "app_count": {"type": "string"},
                "url": {"type": "string"}
            }
        },
        "ecosystem_strategy": {"type": "string"}
    },
    "required": ["company_name"]
}

COMPANY_SOCIAL_PRESENCE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "social_profiles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "platform": {"type": "string"},
                    "handle": {"type": "string"},
                    "url": {"type": "string"},
                    "followers": {"type": "string"},
                    "posting_frequency": {"type": "string"}
                }
            }
        },
        "content_channels": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "enum": ["blog", "podcast", "youtube", "newsletter", "webinar", "events"]},
                    "name": {"type": "string"},
                    "url": {"type": "string"},
                    "frequency": {"type": "string"},
                    "subscriber_count": {"type": "string"}
                }
            }
        },
        "content_themes": {"type": "array", "items": {"type": "string"}},
        "community": {
            "type": "object",
            "properties": {
                "platforms": {"type": "array", "items": {"type": "string"}},
                "size": {"type": "string"},
                "urls": {"type": "array", "items": {"type": "string"}}
            }
        },
        "brand_voice": {"type": "string"},
        "executive_presence": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "title": {"type": "string"},
                    "platform": {"type": "string"},
                    "handle": {"type": "string"},
                    "followers": {"type": "string"},
                    "url": {"type": "string"}
                }
            }
        },
        "notable_content": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "type": {"type": "string"},
                    "url": {"type": "string"},
                    "engagement": {"type": "string"}
                }
            }
        }
    },
    "required": ["company_name"]
}


# =============================================================================
# SCHEMA REGISTRY
# =============================================================================

SCHEMAS: dict[str, dict[str, Any]] = {
    "company_overview": COMPANY_OVERVIEW_SCHEMA,
    "company_news": COMPANY_NEWS_SCHEMA,
    "competitive_landscape": COMPETITIVE_LANDSCAPE_SCHEMA,
    "company_financials": COMPANY_FINANCIALS_SCHEMA,
    "company_leadership": COMPANY_LEADERSHIP_SCHEMA,
    "company_clients": COMPANY_CLIENTS_SCHEMA,
    "company_technology": COMPANY_TECHNOLOGY_SCHEMA,
    "company_hiring": COMPANY_HIRING_SCHEMA,
    "company_partnerships": COMPANY_PARTNERSHIPS_SCHEMA,
    "company_social_presence": COMPANY_SOCIAL_PRESENCE_SCHEMA,
}


def get_schema(tool_name: str) -> dict[str, Any]:
    """Get JSON schema for a tool by name."""
    schema = SCHEMAS.get(tool_name)
    if not schema:
        raise ValueError(f"No schema found for tool: {tool_name}")
    return schema


def get_schema_json(tool_name: str) -> str:
    """Get JSON schema as a JSON string for API requests."""
    return json.dumps(get_schema(tool_name))
