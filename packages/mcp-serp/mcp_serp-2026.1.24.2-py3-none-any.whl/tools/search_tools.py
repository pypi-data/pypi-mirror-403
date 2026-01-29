"""Search tools for Google SERP API."""

from typing import Literal

from core.client import client
from core.exceptions import SerpAPIError, SerpAuthError
from core.server import mcp


@mcp.tool()
async def serp_google_search(
    query: str,
    search_type: Literal["search", "images", "news", "maps", "places", "videos"] = "search",
    country: str | None = None,
    language: str | None = None,
    time_range: str | None = None,
    number: int | None = None,
    page: int | None = None,
) -> str:
    """Search Google and get structured results using the SERP API.

    Performs a Google search and returns structured results including organic
    search results, knowledge graph, related questions, and more.

    Args:
        query: The search query string. Required.
        search_type: Type of search to perform. Options:
            - "search": Regular web search (default)
            - "images": Image search
            - "news": News articles
            - "maps": Map results
            - "places": Local business/place results
            - "videos": Video results
        country: Country code for localized results (e.g., "us", "cn", "uk").
            Default is "us".
        language: Language code for results (e.g., "en", "zh-cn", "fr").
            Default is "en".
        time_range: Time filter for results. Options:
            - "qdr:h": Past hour
            - "qdr:d": Past day
            - "qdr:w": Past week
            - "qdr:m": Past month
            - None: No time restriction (default)
        number: Number of results per page (default: 10).
            Note: More than 10 results may incur additional credits.
        page: Page number for pagination (default: 1).

    Returns:
        Formatted search results as a string, including:
        - Knowledge graph (if available)
        - Organic search results with title, link, and snippet
        - Related questions (People Also Ask)
        - Related searches

    Example:
        serp_google_search(query="artificial intelligence", search_type="news")
    """
    try:
        # Build payload
        payload: dict = {"query": query, "type": search_type}

        if country:
            payload["country"] = country
        if language:
            payload["language"] = language
        if time_range:
            payload["range"] = time_range
        if number:
            payload["number"] = number
        if page:
            payload["page"] = page

        result = await client.search(**payload)

        # Format response
        output_parts = []

        # Knowledge Graph
        if "knowledge_graph" in result and result["knowledge_graph"]:
            kg = result["knowledge_graph"]
            output_parts.append("## Knowledge Graph")
            if kg.get("title"):
                output_parts.append(f"**{kg['title']}**")
            if kg.get("type"):
                output_parts.append(f"Type: {kg['type']}")
            if kg.get("description"):
                output_parts.append(f"\n{kg['description']}")
            if kg.get("website"):
                output_parts.append(f"Website: {kg['website']}")
            if kg.get("attributes"):
                output_parts.append("\nAttributes:")
                for key, value in kg["attributes"].items():
                    output_parts.append(f"  - {key}: {value}")
            output_parts.append("")

        # Answer Box
        if "answer_box" in result and result["answer_box"]:
            ab = result["answer_box"]
            output_parts.append("## Answer Box")
            if ab.get("answer"):
                output_parts.append(f"**{ab['answer']}**")
            if ab.get("title"):
                output_parts.append(f"{ab['title']}")
            output_parts.append("")

        # Organic Results
        if "organic" in result and result["organic"]:
            output_parts.append("## Search Results")
            for i, item in enumerate(result["organic"], 1):
                output_parts.append(f"\n### {i}. {item.get('title', 'No Title')}")
                output_parts.append(f"URL: {item.get('link', 'N/A')}")
                if item.get("snippet"):
                    output_parts.append(f"{item['snippet']}")
                if item.get("date"):
                    output_parts.append(f"Date: {item['date']}")

        # Images
        if "images" in result and result["images"]:
            output_parts.append("\n## Images")
            for i, item in enumerate(result["images"][:10], 1):
                output_parts.append(f"\n### Image {i}")
                output_parts.append(f"Title: {item.get('title', 'No Title')}")
                output_parts.append(f"URL: {item.get('link', 'N/A')}")
                if item.get("image_url"):
                    output_parts.append(f"Image: {item['image_url']}")

        # News
        if "news" in result and result["news"]:
            output_parts.append("\n## News")
            for i, item in enumerate(result["news"], 1):
                output_parts.append(f"\n### {i}. {item.get('title', 'No Title')}")
                output_parts.append(f"Source: {item.get('source', 'N/A')}")
                output_parts.append(f"URL: {item.get('link', 'N/A')}")
                if item.get("snippet"):
                    output_parts.append(f"{item['snippet']}")
                if item.get("date"):
                    output_parts.append(f"Date: {item['date']}")

        # Videos
        if "videos" in result and result["videos"]:
            output_parts.append("\n## Videos")
            for i, item in enumerate(result["videos"], 1):
                output_parts.append(f"\n### {i}. {item.get('title', 'No Title')}")
                output_parts.append(f"URL: {item.get('link', 'N/A')}")
                if item.get("source"):
                    output_parts.append(f"Source: {item['source']}")
                if item.get("duration"):
                    output_parts.append(f"Duration: {item['duration']}")
                if item.get("date"):
                    output_parts.append(f"Date: {item['date']}")

        # Places
        if "places" in result and result["places"]:
            output_parts.append("\n## Places")
            for i, item in enumerate(result["places"], 1):
                output_parts.append(f"\n### {i}. {item.get('title', 'No Title')}")
                if item.get("address"):
                    output_parts.append(f"Address: {item['address']}")
                if item.get("rating"):
                    output_parts.append(f"Rating: {item['rating']}")

        # Maps
        if "maps" in result and result["maps"]:
            output_parts.append("\n## Maps")
            for i, item in enumerate(result["maps"], 1):
                output_parts.append(f"\n### {i}. {item.get('title', 'No Title')}")
                if item.get("address"):
                    output_parts.append(f"Address: {item['address']}")

        # People Also Ask
        if "people_also_ask" in result and result["people_also_ask"]:
            output_parts.append("\n## People Also Ask")
            for item in result["people_also_ask"]:
                output_parts.append(f"\n**Q: {item.get('question', 'N/A')}**")
                if item.get("snippet"):
                    output_parts.append(f"A: {item['snippet']}")
                if item.get("link"):
                    output_parts.append(f"Source: {item['link']}")

        # Related Searches
        if "related_searches" in result and result["related_searches"]:
            output_parts.append("\n## Related Searches")
            queries = [
                item.get("query", "") for item in result["related_searches"] if item.get("query")
            ]
            output_parts.append(", ".join(queries))

        if not output_parts:
            return "No results found for your query."

        return "\n".join(output_parts)

    except SerpAuthError as e:
        return f"Authentication Error: {e.message}. Please check your API token."
    except SerpAPIError as e:
        return f"API Error: {e.message}"
    except Exception as e:
        return f"Error performing search: {str(e)}"


@mcp.tool()
async def serp_google_images(
    query: str,
    country: str | None = None,
    language: str | None = None,
    number: int | None = None,
    page: int | None = None,
) -> str:
    """Search Google Images and get image results.

    Performs a Google Image search and returns structured image results.

    Args:
        query: The search query string. Required.
        country: Country code for localized results (e.g., "us", "cn").
        language: Language code for results (e.g., "en", "zh-cn").
        number: Number of results per page (default: 10).
        page: Page number for pagination (default: 1).

    Returns:
        Formatted image search results.
    """
    result: str = await serp_google_search(
        query=query,
        search_type="images",
        country=country,
        language=language,
        number=number,
        page=page,
    )
    return result


@mcp.tool()
async def serp_google_news(
    query: str,
    country: str | None = None,
    language: str | None = None,
    time_range: str | None = None,
    number: int | None = None,
    page: int | None = None,
) -> str:
    """Search Google News and get news article results.

    Performs a Google News search and returns structured news results.

    Args:
        query: The search query string. Required.
        country: Country code for localized results (e.g., "us", "cn").
        language: Language code for results (e.g., "en", "zh-cn").
        time_range: Time filter. Options: "qdr:h" (hour), "qdr:d" (day),
            "qdr:w" (week), "qdr:m" (month).
        number: Number of results per page (default: 10).
        page: Page number for pagination (default: 1).

    Returns:
        Formatted news search results.
    """
    result: str = await serp_google_search(
        query=query,
        search_type="news",
        country=country,
        language=language,
        time_range=time_range,
        number=number,
        page=page,
    )
    return result


@mcp.tool()
async def serp_google_videos(
    query: str,
    country: str | None = None,
    language: str | None = None,
    number: int | None = None,
    page: int | None = None,
) -> str:
    """Search Google Videos and get video results.

    Performs a Google Video search and returns structured video results.

    Args:
        query: The search query string. Required.
        country: Country code for localized results (e.g., "us", "cn").
        language: Language code for results (e.g., "en", "zh-cn").
        number: Number of results per page (default: 10).
        page: Page number for pagination (default: 1).

    Returns:
        Formatted video search results.
    """
    result: str = await serp_google_search(
        query=query,
        search_type="videos",
        country=country,
        language=language,
        number=number,
        page=page,
    )
    return result


@mcp.tool()
async def serp_google_places(
    query: str,
    country: str | None = None,
    language: str | None = None,
    number: int | None = None,
    page: int | None = None,
) -> str:
    """Search Google for local places and businesses.

    Performs a Google Places search and returns structured place results.

    Args:
        query: The search query string. Required.
        country: Country code for localized results (e.g., "us", "cn").
        language: Language code for results (e.g., "en", "zh-cn").
        number: Number of results per page (default: 10).
        page: Page number for pagination (default: 1).

    Returns:
        Formatted place search results.
    """
    result: str = await serp_google_search(
        query=query,
        search_type="places",
        country=country,
        language=language,
        number=number,
        page=page,
    )
    return result


@mcp.tool()
async def serp_google_maps(
    query: str,
    country: str | None = None,
    language: str | None = None,
    number: int | None = None,
    page: int | None = None,
) -> str:
    """Search Google Maps for locations.

    Performs a Google Maps search and returns structured map results.

    Args:
        query: The search query string. Required.
        country: Country code for localized results (e.g., "us", "cn").
        language: Language code for results (e.g., "en", "zh-cn").
        number: Number of results per page (default: 10).
        page: Page number for pagination (default: 1).

    Returns:
        Formatted map search results.
    """
    result: str = await serp_google_search(
        query=query,
        search_type="maps",
        country=country,
        language=language,
        number=number,
        page=page,
    )
    return result
