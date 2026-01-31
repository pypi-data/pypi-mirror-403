"""
Web Search Skill - Web and news search capability.

This skill provides the ability to search the web and news using DuckDuckGo.
It wraps the WebSearchTool and WebNewsSearchTool with detailed instructions.
"""

from ..base import Skill, SkillMetadata, SkillCategory
from ...tools import WebSearchTool, WebNewsSearchTool


WEB_SEARCH_INSTRUCTIONS = """
## Web Search Instructions

You can search the web and news using DuckDuckGo. No API key is required.

### Available Tools

1. **web_search** - Search the web for general information
2. **news_search** - Search for recent news articles

### Web Search Tool

Use `web_search` to find current information from the internet.

**Parameters:**
- `query` (required): The search query to look up
- `max_results` (optional): Maximum number of results (default: 5, max: 10)

**Returns:**
- Formatted search results with titles, snippets, and URLs

**Example Usage:**
```
web_search("Python async programming best practices")
web_search("latest AI developments 2024", max_results=10)
```

### News Search Tool

Use `news_search` to find recent news articles on a topic.

**Parameters:**
- `query` (required): The news topic to search for
- `max_results` (optional): Maximum number of results (default: 5, max: 10)

**Returns:**
- Formatted news results with titles, dates, sources, and URLs

**Example Usage:**
```
news_search("artificial intelligence regulations")
news_search("tech industry layoffs", max_results=8)
```

### Best Practices

1. **Be specific**: Use specific search terms for better results
2. **Use quotes**: For exact phrases, include them in your query
3. **Combine terms**: Use multiple relevant keywords
4. **Check dates**: News results include publication dates - verify recency
5. **Verify sources**: Cross-reference important information from multiple sources

### When to Use Each Tool

- **web_search**: General information, tutorials, documentation, how-to guides
- **news_search**: Current events, recent announcements, breaking news, industry updates

### Limitations

- Results are limited to 10 per search
- Some websites may block scraping
- News results depend on DuckDuckGo's news index
- Results may vary based on region and time
"""


def create_web_search_skill() -> Skill:
    """
    Create the web search skill.

    Returns:
        Skill instance for web and news search
    """
    skill = Skill(
        metadata=SkillMetadata(
            name="web_search",
            description="Search the web and news using DuckDuckGo (no API key required)",
            trigger_patterns=[
                "search",
                "web search",
                "news",
                "lookup",
                "find online",
                "search the web",
                "google",
                "look up",
                "current events",
                "recent news",
            ],
            category=SkillCategory.WEB,
            version="1.0.0",
        ),
        instructions=WEB_SEARCH_INSTRUCTIONS,
        tools=[WebSearchTool(), WebNewsSearchTool()],
        dependencies=[],
        config={},
    )
    skill._display_name = "Recherche sur Internet"
    skill._display_icon = "🔍"
    return skill


__all__ = ["create_web_search_skill", "WEB_SEARCH_INSTRUCTIONS"]
