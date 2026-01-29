# Research Tools

CLI toolkit + MCP server for dev.to, Google/Serper, Reddit, YouTube, Trends, News, Hacker News and SearchAPI.io research. Global alias `rt`.

## Quick Start

```bash
# Help
rt --help

# Dev.to research
rt devto trending -t typescript
rt devto tags -t typescript,javascript
rt devto authors -t typescript --limit 10

# Google/Serper research
rt google keywords -q "typescript tips"
rt google paa -q "how to learn typescript"
rt google serp -q "claude code tutorial"
rt google related -q "ai development"
rt google keywords -q "test" --no-cache

# Google Trends research
rt trends interest -q "typescript" --geo us --time "today 12-m"
rt trends related -q "typescript"
rt trends topics -q "typescript"
rt trends geo -q "typescript"
rt t interest -q "python,javascript" --geo us  # compare

# Google News research
rt news search -q "typescript" --period week
rt news search -q "site:techcrunch.com AI" --period month --sort most_recent
rt n search -q "claude anthropic" --gl us

# Reddit research
rt reddit -s typescript
rt reddit -s typescript,webdev --sort top --period month

# Hacker News research
rt hn top
rt hn new --limit 50
rt hn best
rt hn ask
rt hn show
rt hn search -q "typescript"
rt hn search -q "claude api" --limit 20 --json

# YouTube research
rt youtube search -q "typescript tutorial"
rt yt channel -c "Fireship" --limit 10
rt yt trending --category music --region us

# Competitor research (SearchAPI.io)
rt competitor serp -q "project management software"
rt competitor ads -q "crm software"
rt c serp -q "keyword" --no-cache

# Ads Transparency (all ads for an advertiser)
rt transparency ads -d tesla.com
rt transparency ads -d openai.com --region us --platform youtube
rt at ads -d anthropic.com --format video --period last_90_days

# Google AI Mode (AI-generated responses)
rt ai search -q "best typescript error handling practices"
rt ai search -q "how to optimize react performance" --location "San Francisco"

# Rank Tracking (SEO position monitoring)
rt rank track -q "typescript tutorial"
rt rank track -q "react hooks" --device mobile --location "New York" -n 50
rt r track -q "claude code" --gl us

# LLM Citation Tracking (Perplexity, Google AI Mode)
rt llm track -q "best typescript framework"
rt llm track -q "typescript orm" --engines perplexity,google_ai
rt l track -q "test" --no-cache

# Brand visibility in LLM responses
rt llm brand -d prisma.io --keywords "typescript orm,node database"
rt l brand -d anthropic.com -k "ai api,llm sdk"

# Compare domain vs competitor in LLM citations
rt llm compare -d prisma.io -c typeorm.io --keywords "typescript orm,node database"
rt l compare -d vercel.com -c netlify.com -k "deploy react,hosting"

# Cache management
rt cache stats
rt cache clear
rt cache cleanup
```

## MCP Server

```bash
# Run MCP server
rt-mcp

# Or via uvx (install from PyPI)
uvx mcp-cli-research-tools
```

### MCP Tools
- `devto_trending` - Trending posts from dev.to
- `devto_tags` - Tag engagement analysis
- `devto_authors` - Top authors by engagement
- `google_keywords` - Autocomplete suggestions
- `google_serp` - SERP analysis
- `google_paa` - People Also Ask
- `google_related` - Related searches
- `google_trends` - Google Trends (interest, related, topics, geo)
- `google_news` - Google News search
- `google_ads_transparency` - All ads for an advertiser
- `google_ai_mode` - AI-generated responses with references
- `google_rank_tracking` - SEO position monitoring (up to 100 results)
- `reddit_posts` - Subreddit monitoring
- `hn_top_stories` - Top stories from Hacker News
- `hn_new_stories` - Newest stories
- `hn_best_stories` - Best stories
- `hn_ask_stories` - Ask HN posts
- `hn_show_stories` - Show HN posts
- `hn_search` - Search HN via Algolia
- `youtube_search` - Video search
- `youtube_channel` - Channel videos
- `youtube_trending` - Trending videos
- `searchapi_serp` - SERP with AI Overview and ads
- `searchapi_ads` - Competitor ads analysis
- `llm_track` - Track citations across LLM engines
- `llm_brand` - Brand visibility in LLM responses
- `llm_compare` - Compare domain vs competitor in LLM citations

## Setup

```bash
cd C:\ai-projects\research-tools && uv sync
```

## Credentials (.env)

```
DEVTO_API_KEY=xxx       # https://dev.to/settings/extensions
SERPER_API_KEY=xxx      # https://serper.dev/api-key
SEARCH_API_IO_KEY=xxx   # https://www.searchapi.io/api-key
PERPLEXITY_API_KEY=xxx  # https://www.perplexity.ai/settings/api
OPENAI_API_KEY=xxx      # Optional - for ChatGPT (expensive)
```

## Cache

SQLite database (`~/.research-tools/data.db`). TTL: Serper 48h, Reddit 12h, YouTube 24h, Trends 24h, News 12h, HN 12h, SearchAPI 48h, Ads Transparency 24h, AI Mode 12h, Rank Tracking 24h, LLM Tracking 12h.

## Structure

```
src/research_tools/
├── cli/           # Cyclopts CLI
├── clients/       # API clients (Serper, SearchAPI, Perplexity, OpenAI, HN)
├── db/            # SQLite + CacheRepository
├── mcp/           # FastMCP server
├── models/        # Pydantic models
├── services/      # Service layer (business logic)
└── output.py      # Rich rendering
```
