"""YouTube service - SSOT for YouTube research."""

from ..clients import SerperClient
from ..models import VideoResult, YouTubeResult
from .base import BaseService
from .cache import CacheService


class YouTubeService(BaseService):
    """Service for YouTube video research via Serper API."""

    cache_prefix = "youtube"
    default_ttl = 24

    def __init__(self, api_key: str, cache: CacheService) -> None:
        super().__init__(cache)
        self._api_key = api_key

    async def search(
        self,
        query: str,
        limit: int = 20,
        region: str = "us",
        skip_cache: bool = False,
    ) -> YouTubeResult:
        """
        Search for videos.

        Args:
            query: Search query
            limit: Max number of results
            region: Country code
            skip_cache: Force fresh fetch

        Returns:
            YouTubeResult with videos
        """
        cache_key = self._cache_key("search", query, str(limit), region)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_search(query, limit, region),
            self.default_ttl,
            skip_cache,
        )

        return YouTubeResult(
            query=cached_data["query"],
            videos=[VideoResult(**v) for v in cached_data["videos"]],
            from_cache=from_cache,
        )

    async def _fetch_search(self, query: str, limit: int, region: str) -> dict:
        """Fetch video search from API."""
        async with SerperClient(self._api_key) as client:
            videos = await client.videos(query, num=limit, gl=region)
            return {
                "query": query,
                "videos": [self._video_to_dict(v) for v in videos],
            }

    async def channel_videos(
        self,
        channel: str,
        limit: int = 20,
        region: str = "us",
        skip_cache: bool = False,
    ) -> YouTubeResult:
        """
        Get videos from a specific channel.

        Args:
            channel: Channel name
            limit: Max number of results
            region: Country code
            skip_cache: Force fresh fetch

        Returns:
            YouTubeResult with videos from channel
        """
        cache_key = self._cache_key("channel", channel, str(limit), region)

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_channel(channel, limit, region),
            self.default_ttl,
            skip_cache,
        )

        return YouTubeResult(
            query=cached_data["query"],
            videos=[VideoResult(**v) for v in cached_data["videos"]],
            from_cache=from_cache,
        )

    async def _fetch_channel(self, channel: str, limit: int, region: str) -> dict:
        """Fetch channel videos from API."""
        query = f'"{channel}" site:youtube.com'
        async with SerperClient(self._api_key) as client:
            videos = await client.videos(query, num=limit, gl=region)
            # Filter to only include videos from matching channel
            filtered = [v for v in videos if channel.lower() in v.channel.lower()]
            result_videos = filtered if filtered else videos
            return {
                "query": channel,
                "videos": [self._video_to_dict(v) for v in result_videos],
            }

    async def trending(
        self,
        category: str | None = None,
        region: str = "us",
        limit: int = 20,
        skip_cache: bool = False,
    ) -> YouTubeResult:
        """
        Get trending videos.

        Args:
            category: Optional category (music, gaming, tech, etc.)
            region: Country code
            limit: Max number of results
            skip_cache: Force fresh fetch

        Returns:
            YouTubeResult with trending videos
        """
        cache_key = self._cache_key("trending", category or "all", region, str(limit))

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_trending(category, region, limit),
            self.default_ttl,
            skip_cache,
        )

        return YouTubeResult(
            query=cached_data["query"],
            videos=[VideoResult(**v) for v in cached_data["videos"]],
            from_cache=from_cache,
        )

    async def _fetch_trending(
        self, category: str | None, region: str, limit: int
    ) -> dict:
        """Fetch trending videos from API."""
        if category:
            query = f"trending {category} videos {region}"
        else:
            query = f"trending videos {region}"

        async with SerperClient(self._api_key) as client:
            videos = await client.videos(query, num=limit, gl=region)
            return {
                "query": query,
                "videos": [self._video_to_dict(v) for v in videos],
            }

    def _video_to_dict(self, video: VideoResult) -> dict:
        """Convert VideoResult to dict for caching."""
        return {
            "position": video.position,
            "title": video.title,
            "link": video.link,
            "snippet": video.snippet,
            "channel": video.channel,
            "duration": video.duration,
            "views": video.views,
            "date": video.date,
            "thumbnail": video.thumbnail,
        }
