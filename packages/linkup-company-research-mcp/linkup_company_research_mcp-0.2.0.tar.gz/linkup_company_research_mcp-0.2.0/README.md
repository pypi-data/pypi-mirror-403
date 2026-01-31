# Linkup Company Research MCP

An MCP server that provides comprehensive company research tools powered by [Linkup](https://linkup.so). Connect it to Claude, Cursor, or any MCP-compatible client to get instant company intelligence.

## Features

- **10 research tools** covering all aspects of company intelligence
- **Dual output formats**: Natural language answers with sources, or structured JSON for automation
- **Full parameter control**: Date filters, domain filters, image support, and result limits
- **Optimized prompts**: Following Linkup's best practices for accurate, comprehensive research

## Tools

| Tool | Description | Search Depth |
|------|-------------|--------------|
| `company_overview` | Company description, industry, size, business model, products | Deep |
| `company_news` | Latest news and developments (with date/topic filters) | Standard |
| `competitive_landscape` | Competitors, market position, differentiators | Deep |
| `company_financials` | Funding history, valuation, revenue, investors | Deep |
| `company_leadership` | Executives, founders, board members, advisors | Standard |
| `company_clients` | Customers, case studies, testimonials | Deep |
| `company_technology` | Tech stack, patents, engineering, open source | Deep |
| `company_hiring` | Job openings, growth signals, Glassdoor ratings | Standard |
| `company_partnerships` | Partners, integrations, ecosystem | Deep |
| `company_social_presence` | Social media, content strategy, community | Standard |

## Output Formats

All tools support two output formats via the `output_format` parameter:

### Natural Language (`output_format="answer"`)
Returns a comprehensive answer with up to 5 cited sources. Best for human consumption.

### Structured JSON (`output_format="structured"`)
Returns data in a defined JSON schema. Best for automation, CRM integration, and data pipelines.

## Parameters

### Common Parameters (all tools)
| Parameter | Type | Description |
|-----------|------|-------------|
| `company_name` | str | **Required.** The company to research |
| `output_format` | str | `"answer"` (default) or `"structured"` |
| `max_results` | int | Maximum sources to consider (1-50, default: 10-15) |

### Date Filters (news, financials)
| Parameter | Type | Description |
|-----------|------|-------------|
| `from_date` | str | Start date in YYYY-MM-DD format |
| `to_date` | str | End date in YYYY-MM-DD format |

### Domain Filters (news)
| Parameter | Type | Description |
|-----------|------|-------------|
| `include_domains` | str | Comma-separated domains to include (e.g., "techcrunch.com,reuters.com") |
| `exclude_domains` | str | Comma-separated domains to exclude |

### Other Parameters
| Parameter | Type | Tools | Description |
|-----------|------|-------|-------------|
| `include_images` | bool | overview, competitive, leadership, social | Include relevant images |
| `topic` | str | news | Filter by topic (e.g., "funding", "product launch") |
| `department` | str | hiring | Filter by department (e.g., "engineering", "sales") |

## Installation

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "linkup-company-research": {
      "command": "uvx",
      "args": ["linkup-company-research-mcp"],
      "env": {
        "LINKUP_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Claude Code

```bash
claude mcp add linkup-company-research -- uvx linkup-company-research-mcp
```

Then set your API key:
```bash
export LINKUP_API_KEY="your-api-key-here"
```

### Cursor

Add to `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "linkup-company-research": {
      "command": "uvx",
      "args": ["linkup-company-research-mcp"],
      "env": {
        "LINKUP_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Get Your API Key

1. Go to [linkup.so](https://linkup.so)
2. Sign up or log in
3. Navigate to API settings
4. Generate your API key

## Example Usage

Once connected, you can ask your AI assistant things like:

### Basic Research
- "Give me an overview of Stripe"
- "What's the latest news about OpenAI?"
- "Who are Figma's main competitors?"

### With Parameters
- "Get Anthropic's funding news from the last 6 months" (date filter)
- "Find Notion's customers and case studies" (new tool)
- "What tech stack does Vercel use?" (new tool)

### Structured Output for Automation
- "Get Stripe's company overview in structured format" (returns JSON)
- "Research HubSpot's leadership team as JSON" (for CRM integration)

## Tool Details

### company_overview
Researches the company's website, LinkedIn, and press coverage to provide detailed information about what they do, their industry, size, and business model.

### company_news
Searches news sources, press releases, and publications for recent coverage. Supports filtering by date range, topic, and source domains.

### competitive_landscape
Identifies competitors, market positioning, differentiators, and competitive advantages through research of industry reports, review sites, and company materials.

### company_financials
Researches funding history, valuation, revenue, investors, and financial health through Crunchbase, press releases, and financial news.

### company_leadership
Identifies executives, founders, board members, and advisors through company pages, LinkedIn, and press releases.

### company_clients
Researches customer pages, case studies, press releases, and review sites to identify verified customers and their use cases.

### company_technology
Analyzes engineering blogs, job postings, tech detection tools, patents, and open source contributions to understand technical capabilities.

### company_hiring
Researches careers pages, job boards, LinkedIn, and Glassdoor to understand hiring patterns and employee growth signals.

### company_partnerships
Researches partner pages, integration marketplaces, press releases, and partner programs to map the company's ecosystem.

### company_social_presence
Researches social profiles, content channels, community platforms, and executive thought leadership to understand their digital presence.

## Development

```bash
# Clone and install locally
git clone https://github.com/LinkupPlatform/linkup-company-research-mcp
cd linkup-company-research-mcp
pip install -e .

# Run the server directly
LINKUP_API_KEY="your-key" linkup-company-research
```

### Project Structure

```
src/linkup_company_research/
├── __init__.py
├── server.py      # Main MCP server with 10 tools
├── schemas.py     # JSON schemas for structuredOutput
├── prompts.py     # Optimized prompt templates
└── types.py       # Type definitions
```

## License

MIT
