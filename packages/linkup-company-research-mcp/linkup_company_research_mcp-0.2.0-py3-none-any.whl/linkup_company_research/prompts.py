"""Optimized prompt templates for Linkup Company Research MCP.

These prompts follow Linkup's best practices:
- Sequential search patterns (search -> scrape)
- Explicit scraping instructions
- Multi-step research flows
- Specific data points to extract
"""


# =============================================================================
# EXISTING TOOLS - ENHANCED PROMPTS
# =============================================================================

COMPANY_OVERVIEW_PROMPT = """You are an expert business analyst researching {company_name}.

Execute the following research steps:

1. First, find {company_name}'s official website URL
2. Scrape their homepage to understand their core value proposition and what they do
3. Find and scrape their "About Us" or "About" page for company background, mission, and history
4. Find their LinkedIn company page and extract company details (employee count, headquarters, industry)
5. Search for recent press releases or news about {company_name} to find founding date and key milestones

Based on this comprehensive research, provide:
- Company name (official name)
- Website URL
- Core business description: What problem do they solve? What do they do?
- Value proposition: How do they differentiate themselves?
- Industry and sector classification
- Headquarters location (city, state/region, country)
- Other office locations (if found)
- Year founded
- Company size: Employee count with source (LinkedIn, website, etc.)
- Employee count range (e.g., "100-500")
- Business model: B2B, B2C, SaaS, marketplace, platform, services, etc.
- Key products or services with brief descriptions
- Target customer segments: Who are their ideal customers?
- LinkedIn URL
- Mission statement or company values (if publicly stated)

Do not stop until you have attempted to scrape the key pages. Return only factual data found - do not infer or estimate values."""


COMPANY_NEWS_PROMPT = """You are an expert business news analyst researching {company_name}.

{date_filter}
{topic_filter}

Execute the following research steps:

1. Search for recent news articles mentioning {company_name}
2. Look for official press releases from {company_name}'s newsroom or press page
3. Check major tech/business publications (TechCrunch, Reuters, Bloomberg, etc.)
4. Search for industry-specific news sources relevant to {company_name}'s sector
5. Run several searches with adjacent keywords to ensure comprehensive coverage

For each news item found, extract:
- Headline/title
- Publication date (as specific as possible)
- Source/publication name
- URL to the article
- Brief summary (2-3 sentences capturing the key points)
- Category: funding, product, partnership, executive, earnings, expansion, acquisition, legal, or other
- Sentiment: positive, negative, or neutral for the company

Focus on factual reporting. Distinguish between:
- Official announcements and press releases
- Third-party news reporting
- Analysis and opinion pieces

Order results by date, most recent first. Include the total count of news items found."""


COMPANY_NEWS_DATE_FILTER = """Search for news from {from_date} to {to_date}."""
COMPANY_NEWS_TOPIC_FILTER = """Focus specifically on news about: {topic}"""


COMPETITIVE_LANDSCAPE_PROMPT = """You are an expert competitive intelligence analyst researching {company_name}.

Execute the following research steps:

1. First, identify {company_name}'s primary industry and market category
2. Search for "{company_name} competitors" and "{company_name} alternatives"
3. Look for industry analyst reports, market research, or competitive analyses mentioning {company_name}
4. Check software review sites like G2, Capterra, TrustRadius for competitive comparisons
5. Scrape {company_name}'s website for their competitive positioning statements
6. Search for comparison articles: "{company_name} vs [competitor]"

Provide comprehensive competitive analysis:

Market Context:
- Market category: What market/industry does {company_name} compete in?
- Market size: Estimated TAM/SAM if available
- Market position: Is {company_name} a leader, challenger, follower, niche player, or emerging?

Competitors (for each major competitor):
- Company name and website
- Type: direct competitor (same solution) or indirect (different approach to same problem)
- Brief description of what they do
- Key strengths compared to {company_name}
- Key weaknesses compared to {company_name}

Competitive Position:
- Key differentiators: What makes {company_name} unique in the market?
- Competitive advantages: Technology, pricing, brand, distribution, network effects, etc.
- Competitive threats: What challenges or competitive pressures does {company_name} face?
- Market share estimate (if data is available)

Focus on factual competitive intelligence. Cite sources where possible."""


COMPANY_FINANCIALS_PROMPT = """You are an expert financial analyst researching {company_name}'s financial information.

{date_filter}

Execute the following research steps:

1. Search Crunchbase, PitchBook, or similar databases for {company_name}'s funding history
2. Look for funding announcements and press releases about investment rounds
3. Search for investor profiles and identify lead investors for each round
4. Find valuation mentions in news articles or analyst reports
5. For public companies, search for revenue figures, earnings reports, and financial filings
6. Check for IPO status, SPAC deals, or acquisition rumors
7. Search for financial news and developments in the specified time period

Provide detailed financial information:

Funding:
- Total funding raised to date (with source)
- Funding rounds: For each round, include:
  - Round type (Seed, Series A, B, C, etc.)
  - Date of announcement
  - Amount raised
  - Lead investors
  - Valuation at that round (if disclosed)

Current Valuation:
- Most recent valuation amount
- Date of valuation
- Source of valuation data

Investors:
- List of all known investors
- Investor type: VC, PE, strategic, angel, corporate, government

Revenue & Financials (if available):
- Revenue or ARR figures
- Revenue type (ARR, GMV, MRR, etc.)
- Growth rate
- Date of the revenue data

Financial Health:
- Profitability status: profitable, path to profitability, burn rate
- Recent financial milestones

IPO & Public Status:
- IPO status: public, filed, rumored, planned, private, or acquired
- Stock ticker (if public)
- Recent financial news

Note the date and source for each financial data point. Do not estimate values."""


COMPANY_LEADERSHIP_PROMPT = """You are an expert executive researcher investigating {company_name}'s leadership team.

Execute the following research steps:

1. Find and scrape {company_name}'s "Team", "About Us", "Leadership", or "Company" page for executive information
2. Search LinkedIn for {company_name} executives with C-level and VP titles
3. Look for recent executive announcements, leadership changes, or new hire press releases
4. Find board member information from press releases, SEC filings, or company pages
5. Search for advisory board or notable advisors

For each leader identified, provide:
- Full name
- Current title
- Brief professional background (previous companies, education highlights)
- When they joined {company_name} (if known)
- LinkedIn URL (if found)

Organize leadership information as:

Founders:
- Names, current titles, whether still active at the company
- Brief founder background

C-Suite Executives:
- CEO and their background
- CTO, CFO, COO, CMO, CPO, CRO, etc.
- Previous companies they worked at

Board Members:
- Name, affiliation (e.g., "Partner at Sequoia")
- Their role on the board

Advisors (if any):
- Name and area of expertise

Recent Leadership Changes (last 12 months):
- Type: hire, departure, or promotion
- Person's name and role
- Date of change

Focus on verified information from official sources."""


# =============================================================================
# NEW TOOLS - PROMPTS
# =============================================================================

COMPANY_CLIENTS_PROMPT = """You are an expert B2B researcher investigating {company_name}'s customers and clients.

Execute the following research steps:

1. Find and scrape {company_name}'s "Customers", "Case Studies", "Success Stories", or "Clients" page
2. Look for customer logos displayed on their homepage
3. Search for "{company_name} customer" and "{company_name} case study"
4. Find press releases announcing customer wins or partnerships
5. Check review sites like G2, Capterra, TrustRadius for listed customers
6. Search for customer testimonials and quotes

Provide detailed customer information:

Customer Overview:
- Estimated customer count (if disclosed)
- Customer segments: enterprise, mid-market, SMB, consumer, government, etc.
- Key industry verticals where they have traction

Named Customers (for each verified customer):
- Customer name
- Customer's industry
- Verification source: case_study, press_release, logo, review, or testimonial
- Use case: How they use {company_name}'s product/service
- Outcomes/results: Metrics or benefits achieved (if available)

Case Studies (for detailed case studies found):
- Customer name
- Case study title
- Summary of the case study
- Key metrics or results highlighted
- URL to the case study

Testimonials (notable quotes found):
- Quote text
- Author name and title
- Company name

Distinguish between:
- Confirmed customers (from case studies, press releases with explicit confirmation)
- Logo customers (shown on website but without detailed information)
- Inferred customers (mentioned in reviews or third-party sources)"""


COMPANY_TECHNOLOGY_PROMPT = """You are an expert technology analyst researching {company_name}'s technical capabilities.

Execute the following research steps:

1. Search for {company_name}'s engineering blog or technical blog posts
2. Look at their job postings to understand their tech stack
3. Check BuiltWith, StackShare, Wappalyzer, or similar for technology detection
4. Search for patents filed by {company_name}
5. Find technical talks, conference presentations, or engineering podcasts featuring {company_name}
6. Look for open source contributions on GitHub
7. Find their technical documentation or developer resources
8. Search for security certifications and compliance information

Provide comprehensive technical information:

Core Technology:
- What technical approach or innovation powers their product?
- Key technical differentiators

Tech Stack:
- Programming languages used
- Frameworks (frontend, backend)
- Databases and data stores
- Infrastructure components
- Cloud providers (AWS, GCP, Azure, etc.)
- DevOps and CI/CD tools

AI/ML Capabilities (if applicable):
- Machine learning or AI capabilities
- Description of how AI/ML is used

Patents:
- Patent titles
- Patent numbers
- Status: granted, pending, or filed
- Filing/grant dates

Open Source:
- Public repositories
- GitHub URLs
- Description and star counts

Security & Compliance:
- Certifications: SOC 2, ISO 27001, etc.
- Compliance: GDPR, HIPAA, PCI-DSS, etc.

Engineering Organization:
- Engineering blog URL
- Estimated engineering team size
- Notable engineers or technical leaders

Technical Differentiators:
- What makes their technology unique or better?"""


COMPANY_HIRING_PROMPT = """You are an expert talent intelligence analyst researching {company_name}'s hiring activity.

{department_filter}

Execute the following research steps:

1. Find and scrape {company_name}'s careers page to get current job openings
2. Search LinkedIn Jobs for open positions at {company_name}
3. Check job boards like Glassdoor, Indeed, Lever, Greenhouse for additional listings
4. Look for hiring announcements or expansion news
5. Search for employee growth data and headcount changes over time
6. Find Glassdoor company ratings and employee reviews

Provide detailed hiring intelligence:

Job Openings:
- Total number of open positions
- Careers page URL
- List of positions with:
  - Job title
  - Department (Engineering, Sales, Marketing, etc.)
  - Location
  - Seniority level: entry, mid, senior, lead, or executive
  - Remote option: yes/no
  - Job posting URL (if available)

Hiring by Department:
- Department name and number of open roles
- Which teams are growing most?

Locations:
- Cities/regions where they're hiring
- Remote work policy

Employee Growth:
- Current employee count
- Previous employee count (and when)
- Growth rate percentage
- Trend: growing, stable, or declining

Glassdoor Data (if available):
- Overall rating (out of 5)
- Number of reviews
- Recommend to friend percentage
- CEO approval rating

Hiring Signals:
- What do their hiring patterns indicate about company strategy?
- Recent funding? New product launch? Market expansion?

Notable Recent Hires:
- Names, roles, and previous companies of significant hires"""


COMPANY_HIRING_DEPARTMENT_FILTER = """Focus specifically on {department} roles and hiring activity."""


COMPANY_PARTNERSHIPS_PROMPT = """You are an expert business development analyst researching {company_name}'s partnerships and ecosystem.

Execute the following research steps:

1. Find and scrape {company_name}'s "Partners", "Integrations", "Ecosystem", or "Marketplace" page
2. Search for "{company_name} partnership" and "{company_name} integration"
3. Look for partnership announcements in press releases
4. Check if they have a partner program and scrape its details
5. Find technical integrations (API partners, app marketplace listings)
6. Search for channel partner or reseller relationships

Provide comprehensive partnership information:

Strategic Partnerships (for each major partnership):
- Partner company name and website
- Partnership type: strategic, technology, channel, platform, integration, reseller, or consulting
- Description of the partnership
- Date announced (if known)

Integrations (products that integrate with {company_name}):
- Integration name
- Category (CRM, Analytics, Communication, etc.)
- Type: native (built by {company_name}), api, third_party, or marketplace
- Brief description

Partner Program:
- Does a partner program exist?
- Program name
- Partner tiers (e.g., Silver, Gold, Platinum)
- Key benefits for partners
- Partner program URL

Marketplace/App Store:
- Does {company_name} have a marketplace?
- Marketplace name
- Approximate number of apps/integrations
- Marketplace URL

Ecosystem Strategy:
- How do partnerships fit into {company_name}'s growth strategy?
- Open vs. closed ecosystem approach?"""


COMPANY_SOCIAL_PRESENCE_PROMPT = """You are an expert digital marketing analyst researching {company_name}'s social media and content presence.

Execute the following research steps:

1. Find {company_name}'s official social media profiles (LinkedIn, Twitter/X, YouTube, Facebook, Instagram, TikTok)
2. Check follower counts and recent posting activity
3. Find their blog, podcast, newsletter, or other content channels
4. Search for thought leadership content from company executives
5. Look for community forums, Slack groups, Discord servers, or user groups
6. Analyze their content themes and brand voice

Provide comprehensive social presence analysis:

Social Media Profiles (for each platform):
- Platform name
- Handle/username
- Profile URL
- Follower/subscriber count
- Posting frequency (daily, weekly, monthly, etc.)

Content Channels:
- Type: blog, podcast, youtube, newsletter, webinar, events
- Channel name
- URL
- Posting frequency
- Subscriber/reader count (if available)

Content Strategy:
- Content themes: What topics do they focus on?
- Brand voice: Professional, casual, educational, entertaining, etc.

Community:
- Platforms: Slack, Discord, forum, etc.
- Community size (members)
- Community URLs

Executive Social Presence (for key executives with strong presence):
- Name and title
- Platform
- Handle
- Follower count
- Profile URL

Notable Content:
- Viral posts, popular articles, or high-engagement content
- Title, type, URL, and engagement metrics"""


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_prompt(tool_name: str, **kwargs) -> str:
    """Get formatted prompt for a tool with variable substitution."""
    prompts = {
        "company_overview": COMPANY_OVERVIEW_PROMPT,
        "company_news": COMPANY_NEWS_PROMPT,
        "competitive_landscape": COMPETITIVE_LANDSCAPE_PROMPT,
        "company_financials": COMPANY_FINANCIALS_PROMPT,
        "company_leadership": COMPANY_LEADERSHIP_PROMPT,
        "company_clients": COMPANY_CLIENTS_PROMPT,
        "company_technology": COMPANY_TECHNOLOGY_PROMPT,
        "company_hiring": COMPANY_HIRING_PROMPT,
        "company_partnerships": COMPANY_PARTNERSHIPS_PROMPT,
        "company_social_presence": COMPANY_SOCIAL_PRESENCE_PROMPT,
    }

    prompt_template = prompts.get(tool_name)
    if not prompt_template:
        raise ValueError(f"No prompt found for tool: {tool_name}")

    # Handle special filters for news
    if tool_name == "company_news":
        date_filter = ""
        if kwargs.get("from_date") or kwargs.get("to_date"):
            from_date = kwargs.get("from_date", "the beginning")
            to_date = kwargs.get("to_date", "now")
            date_filter = COMPANY_NEWS_DATE_FILTER.format(from_date=from_date, to_date=to_date)

        topic_filter = ""
        if kwargs.get("topic"):
            topic_filter = COMPANY_NEWS_TOPIC_FILTER.format(topic=kwargs["topic"])

        kwargs["date_filter"] = date_filter
        kwargs["topic_filter"] = topic_filter

    # Handle date filter for financials
    if tool_name == "company_financials":
        date_filter = ""
        if kwargs.get("from_date") or kwargs.get("to_date"):
            from_date = kwargs.get("from_date", "the beginning")
            to_date = kwargs.get("to_date", "now")
            date_filter = f"Focus on financial news and developments from {from_date} to {to_date}."
        kwargs["date_filter"] = date_filter

    # Handle department filter for hiring
    if tool_name == "company_hiring":
        department_filter = ""
        if kwargs.get("department"):
            department_filter = COMPANY_HIRING_DEPARTMENT_FILTER.format(department=kwargs["department"])
        kwargs["department_filter"] = department_filter

    return prompt_template.format(**kwargs)
