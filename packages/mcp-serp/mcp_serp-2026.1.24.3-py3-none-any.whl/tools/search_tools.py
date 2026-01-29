"""Search tools for Google SERP API."""

import json
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

    Performs a Google search and returns the complete JSON response from the API,
    preserving all available fields and data.

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
        Complete JSON response from the SERP API containing all available data.

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

        if not result:
            return json.dumps({"error": "No results found for your query."})

        return json.dumps(result, ensure_ascii=False, indent=2)

    except SerpAuthError as e:
        return json.dumps({"error": "Authentication Error", "message": e.message})
    except SerpAPIError as e:
        return json.dumps({"error": "API Error", "message": e.message})
    except Exception as e:
        return json.dumps({"error": "Error performing search", "message": str(e)})


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
