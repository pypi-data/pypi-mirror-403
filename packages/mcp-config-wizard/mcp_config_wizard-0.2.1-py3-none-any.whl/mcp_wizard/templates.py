"""Pre-defined MCP server templates for common servers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ServerTemplate:
    """Template for a pre-configured MCP server."""

    name: str
    display_name: str
    description: str
    transport: str  # "stdio" or "http"
    config: dict[str, Any] = field(default_factory=dict)
    env_vars: list[str] = field(default_factory=list)  # Required env vars to prompt for
    optional_env_vars: list[str] = field(default_factory=list)  # Optional env vars
    headers: list[str] = field(default_factory=list)  # Required headers to prompt for
    category: str = "general"  # Category for grouping


# Popular MCP server templates
TEMPLATES: list[ServerTemplate] = [
    # === DEVELOPMENT TOOLS ===
    ServerTemplate(
        name="filesystem",
        display_name="Filesystem",
        description="Read and write files on your local filesystem",
        transport="stdio",
        category="development",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "{path}"],
        },
    ),
    ServerTemplate(
        name="github",
        display_name="GitHub",
        description="Access GitHub repositories, issues, and pull requests",
        transport="stdio",
        category="development",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
        },
        env_vars=["GITHUB_TOKEN"],
    ),
    ServerTemplate(
        name="gitlab",
        display_name="GitLab",
        description="Access GitLab repositories, issues, and merge requests",
        transport="stdio",
        category="development",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-gitlab"],
        },
        env_vars=["GITLAB_TOKEN"],
        optional_env_vars=["GITLAB_URL"],
    ),
    ServerTemplate(
        name="git",
        display_name="Git",
        description="Git operations on local repositories",
        transport="stdio",
        category="development",
        config={
            "command": "uvx",
            "args": ["mcp-server-git", "--repository", "{repository_path}"],
        },
    ),
    ServerTemplate(
        name="linear",
        display_name="Linear",
        description="Manage Linear issues and projects",
        transport="stdio",
        category="development",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-linear"],
        },
        env_vars=["LINEAR_API_KEY"],
    ),
    
    # === DATABASES ===
    ServerTemplate(
        name="postgres",
        display_name="PostgreSQL",
        description="Query PostgreSQL databases",
        transport="stdio",
        category="database",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-postgres"],
        },
        env_vars=["DATABASE_URL"],
    ),
    ServerTemplate(
        name="sqlite",
        display_name="SQLite",
        description="Query SQLite databases",
        transport="stdio",
        category="database",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sqlite", "{database_path}"],
        },
    ),
    ServerTemplate(
        name="mysql",
        display_name="MySQL",
        description="Query MySQL databases",
        transport="stdio",
        category="database",
        config={
            "command": "npx",
            "args": ["-y", "mcp-server-mysql"],
        },
        env_vars=["MYSQL_URL"],
    ),
    ServerTemplate(
        name="redis",
        display_name="Redis",
        description="Interact with Redis databases",
        transport="stdio",
        category="database",
        config={
            "command": "npx",
            "args": ["-y", "mcp-server-redis"],
        },
        env_vars=["REDIS_URL"],
    ),
    ServerTemplate(
        name="mongodb",
        display_name="MongoDB",
        description="Query MongoDB databases",
        transport="stdio",
        category="database",
        config={
            "command": "npx",
            "args": ["-y", "mcp-server-mongodb"],
        },
        env_vars=["MONGODB_URI"],
    ),
    ServerTemplate(
        name="supabase",
        display_name="Supabase",
        description="Access Supabase projects and databases",
        transport="stdio",
        category="database",
        config={
            "command": "npx",
            "args": ["-y", "@supabase/mcp-server-supabase@latest", "--access-token", "{access_token}"],
        },
    ),
    ServerTemplate(
        name="neon",
        display_name="Neon",
        description="Manage Neon serverless Postgres",
        transport="stdio",
        category="database",
        config={
            "command": "npx",
            "args": ["-y", "@neondatabase/mcp-server-neon"],
        },
        env_vars=["NEON_API_KEY"],
    ),
    
    # === MEMORY & KNOWLEDGE ===
    ServerTemplate(
        name="memory",
        display_name="Memory",
        description="Persistent memory storage for AI conversations",
        transport="stdio",
        category="memory",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"],
        },
    ),
    ServerTemplate(
        name="knowledge-graph",
        display_name="Knowledge Graph Memory",
        description="Graph-based memory with relationships between concepts",
        transport="stdio",
        category="memory",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"],
        },
    ),
    
    # === SEARCH & WEB ===
    ServerTemplate(
        name="brave-search",
        display_name="Brave Search",
        description="Web search using Brave Search API",
        transport="stdio",
        category="search",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
        },
        env_vars=["BRAVE_API_KEY"],
    ),
    ServerTemplate(
        name="tavily",
        display_name="Tavily",
        description="AI-powered search engine for research",
        transport="stdio",
        category="search",
        config={
            "command": "npx",
            "args": ["-y", "tavily-mcp"],
        },
        env_vars=["TAVILY_API_KEY"],
    ),
    ServerTemplate(
        name="exa",
        display_name="Exa",
        description="Neural search engine for finding content",
        transport="stdio",
        category="search",
        config={
            "command": "npx",
            "args": ["-y", "exa-mcp-server"],
        },
        env_vars=["EXA_API_KEY"],
    ),
    ServerTemplate(
        name="fetch",
        display_name="Fetch",
        description="Fetch and parse web content",
        transport="stdio",
        category="search",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-fetch"],
        },
    ),
    ServerTemplate(
        name="firecrawl",
        display_name="Firecrawl",
        description="Web scraping and crawling",
        transport="stdio",
        category="search",
        config={
            "command": "npx",
            "args": ["-y", "firecrawl-mcp"],
        },
        env_vars=["FIRECRAWL_API_KEY"],
    ),
    
    # === BROWSER AUTOMATION ===
    ServerTemplate(
        name="puppeteer",
        display_name="Puppeteer",
        description="Browser automation and web scraping",
        transport="stdio",
        category="browser",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        },
    ),
    ServerTemplate(
        name="playwright",
        display_name="Playwright",
        description="Cross-browser automation and testing",
        transport="stdio",
        category="browser",
        config={
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest"],
        },
    ),
    ServerTemplate(
        name="browserbase",
        display_name="Browserbase",
        description="Cloud browser automation",
        transport="stdio",
        category="browser",
        config={
            "command": "npx",
            "args": ["-y", "@browserbasehq/mcp-server-browserbase"],
        },
        env_vars=["BROWSERBASE_API_KEY", "BROWSERBASE_PROJECT_ID"],
    ),
    
    # === CLOUD & INFRASTRUCTURE ===
    ServerTemplate(
        name="aws",
        display_name="AWS",
        description="AWS services and resource management",
        transport="stdio",
        category="cloud",
        config={
            "command": "npx",
            "args": ["-y", "aws-mcp"],
        },
        env_vars=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        optional_env_vars=["AWS_REGION"],
    ),
    ServerTemplate(
        name="cloudflare",
        display_name="Cloudflare",
        description="Manage Cloudflare services",
        transport="stdio",
        category="cloud",
        config={
            "command": "npx",
            "args": ["-y", "@cloudflare/mcp-server-cloudflare"],
        },
        env_vars=["CLOUDFLARE_API_TOKEN"],
    ),
    ServerTemplate(
        name="vercel",
        display_name="Vercel",
        description="Manage Vercel deployments and projects",
        transport="stdio",
        category="cloud",
        config={
            "command": "npx",
            "args": ["-y", "vercel-mcp"],
        },
        env_vars=["VERCEL_TOKEN"],
    ),
    ServerTemplate(
        name="netlify",
        display_name="Netlify",
        description="Manage Netlify sites and deployments",
        transport="stdio",
        category="cloud",
        config={
            "command": "npx",
            "args": ["-y", "netlify-mcp"],
        },
        env_vars=["NETLIFY_TOKEN"],
    ),
    
    # === COMMUNICATION ===
    ServerTemplate(
        name="slack",
        display_name="Slack",
        description="Access Slack workspaces and channels",
        transport="stdio",
        category="communication",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-slack"],
        },
        env_vars=["SLACK_BOT_TOKEN"],
        optional_env_vars=["SLACK_TEAM_ID"],
    ),
    ServerTemplate(
        name="discord",
        display_name="Discord",
        description="Interact with Discord servers",
        transport="stdio",
        category="communication",
        config={
            "command": "npx",
            "args": ["-y", "discord-mcp"],
        },
        env_vars=["DISCORD_TOKEN"],
    ),
    ServerTemplate(
        name="email",
        display_name="Email (Gmail/SMTP)",
        description="Send and read emails",
        transport="stdio",
        category="communication",
        config={
            "command": "npx",
            "args": ["-y", "email-mcp"],
        },
        env_vars=["EMAIL_ADDRESS", "EMAIL_PASSWORD"],
    ),
    
    # === PRODUCTIVITY ===
    ServerTemplate(
        name="google-drive",
        display_name="Google Drive",
        description="Access and manage Google Drive files",
        transport="stdio",
        category="productivity",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-gdrive"],
        },
        env_vars=["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
    ),
    ServerTemplate(
        name="notion",
        display_name="Notion",
        description="Access Notion workspaces and pages",
        transport="stdio",
        category="productivity",
        config={
            "command": "npx",
            "args": ["-y", "notion-mcp"],
        },
        env_vars=["NOTION_API_KEY"],
    ),
    ServerTemplate(
        name="obsidian",
        display_name="Obsidian",
        description="Access Obsidian vault and notes",
        transport="stdio",
        category="productivity",
        config={
            "command": "npx",
            "args": ["-y", "obsidian-mcp", "--vault", "{vault_path}"],
        },
    ),
    ServerTemplate(
        name="todoist",
        display_name="Todoist",
        description="Manage Todoist tasks and projects",
        transport="stdio",
        category="productivity",
        config={
            "command": "npx",
            "args": ["-y", "todoist-mcp"],
        },
        env_vars=["TODOIST_API_TOKEN"],
    ),
    
    # === MAPS & LOCATION ===
    ServerTemplate(
        name="google-maps",
        display_name="Google Maps",
        description="Access Google Maps for location and directions",
        transport="stdio",
        category="maps",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-google-maps"],
        },
        env_vars=["GOOGLE_MAPS_API_KEY"],
    ),
    
    # === AI & DOCUMENTATION ===
    ServerTemplate(
        name="context7",
        display_name="Context7",
        description="Access Context7 documentation and library information",
        transport="http",
        category="ai",
        config={
            "url": "https://mcp.context7.com/mcp",
        },
        headers=["CONTEXT7_API_KEY"],
    ),
    ServerTemplate(
        name="openai",
        display_name="OpenAI",
        description="Access OpenAI models and APIs",
        transport="stdio",
        category="ai",
        config={
            "command": "npx",
            "args": ["-y", "openai-mcp"],
        },
        env_vars=["OPENAI_API_KEY"],
    ),
    ServerTemplate(
        name="anthropic",
        display_name="Anthropic",
        description="Access Anthropic Claude models",
        transport="stdio",
        category="ai",
        config={
            "command": "npx",
            "args": ["-y", "anthropic-mcp"],
        },
        env_vars=["ANTHROPIC_API_KEY"],
    ),
    
    # === UTILITIES ===
    ServerTemplate(
        name="time",
        display_name="Time",
        description="Get current time and timezone information",
        transport="stdio",
        category="utility",
        config={
            "command": "uvx",
            "args": ["mcp-server-time"],
        },
    ),
    ServerTemplate(
        name="sequential-thinking",
        display_name="Sequential Thinking",
        description="Dynamic problem-solving through structured thoughts",
        transport="stdio",
        category="utility",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"],
        },
    ),
    ServerTemplate(
        name="everything",
        display_name="Everything",
        description="Reference/test server with examples of all MCP features",
        transport="stdio",
        category="utility",
        config={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-everything"],
        },
    ),
    
    # === DATA & ANALYTICS ===
    ServerTemplate(
        name="bigquery",
        display_name="BigQuery",
        description="Query Google BigQuery datasets",
        transport="stdio",
        category="data",
        config={
            "command": "npx",
            "args": ["-y", "bigquery-mcp"],
        },
        env_vars=["GOOGLE_APPLICATION_CREDENTIALS"],
    ),
    ServerTemplate(
        name="snowflake",
        display_name="Snowflake",
        description="Query Snowflake data warehouse",
        transport="stdio",
        category="data",
        config={
            "command": "npx",
            "args": ["-y", "snowflake-mcp"],
        },
        env_vars=["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"],
    ),
    
    # === SECURITY ===
    ServerTemplate(
        name="sentry",
        display_name="Sentry",
        description="Access Sentry error tracking",
        transport="stdio",
        category="security",
        config={
            "command": "npx",
            "args": ["-y", "@sentry/mcp-server-sentry"],
        },
        env_vars=["SENTRY_AUTH_TOKEN"],
    ),
    ServerTemplate(
        name="1password",
        display_name="1Password",
        description="Access 1Password vaults securely",
        transport="stdio",
        category="security",
        config={
            "command": "npx",
            "args": ["-y", "1password-mcp"],
        },
        env_vars=["OP_SERVICE_ACCOUNT_TOKEN"],
    ),
]


def get_template(name: str) -> ServerTemplate | None:
    """Get a server template by name."""
    for template in TEMPLATES:
        if template.name == name:
            return template
    return None


def get_templates_by_transport(transport: str) -> list[ServerTemplate]:
    """Get all templates for a specific transport type."""
    return [t for t in TEMPLATES if t.transport == transport]


def get_templates_by_category(category: str) -> list[ServerTemplate]:
    """Get all templates for a specific category."""
    return [t for t in TEMPLATES if t.category == category]


def get_all_templates() -> list[ServerTemplate]:
    """Get all available server templates."""
    return TEMPLATES.copy()


def get_categories() -> list[str]:
    """Get all unique categories."""
    return sorted(set(t.category for t in TEMPLATES))
