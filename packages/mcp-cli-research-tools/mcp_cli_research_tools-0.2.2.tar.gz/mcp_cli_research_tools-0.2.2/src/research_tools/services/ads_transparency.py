"""Google Ads Transparency Center service - SSOT for advertiser ad research."""

from ..clients import SearchAPIClient
from ..models.ads_transparency import AdCreative, AdsTransparencyResult
from .base import BaseService
from .cache import CacheService


class AdsTransparencyService(BaseService):
    """Service for Google Ads Transparency Center via SearchAPI.io."""

    cache_prefix = "ads_transparency"
    default_ttl = 24

    def __init__(self, api_key: str, cache: CacheService) -> None:
        super().__init__(cache)
        self._api_key = api_key

    async def get_ads(
        self,
        domain: str,
        region: str = "anywhere",
        platform: str = "",
        ad_format: str = "",
        time_period: str = "last_30_days",
        num: int = 40,
        skip_cache: bool = False,
    ) -> AdsTransparencyResult:
        """
        Get all ads for a specific advertiser from Ads Transparency Center.

        Args:
            domain: Advertiser domain (e.g. "tesla.com")
            region: Geographic region (default: "anywhere")
            platform: Ad platform filter (search, youtube, maps, shopping, google_play)
            ad_format: Format filter (text, image, video)
            time_period: Time range (last_30_days, last_90_days, anytime, or YYYY-MM-DD..YYYY-MM-DD)
            num: Number of results (max 100, default 40)
            skip_cache: Force fresh fetch

        Returns:
            AdsTransparencyResult with list of ad creatives
        """
        cache_key = self._cache_key(
            "ads", domain, region, platform, ad_format, time_period, str(num)
        )

        cached_data, from_cache = await self._cache.get_or_fetch_async(
            cache_key,
            lambda: self._fetch_ads(domain, region, platform, ad_format, time_period, num),
            self.default_ttl,
            skip_cache,
        )

        return self._parse_result(cached_data, from_cache)

    async def _fetch_ads(
        self,
        domain: str,
        region: str,
        platform: str,
        ad_format: str,
        time_period: str,
        num: int,
    ) -> dict:
        """Fetch ads data from SearchAPI.io."""
        async with SearchAPIClient(self._api_key) as client:
            params = {
                "domain": domain,
                "region": region,
                "num": min(num, 100),
            }

            if platform:
                params["platform"] = platform
            if ad_format:
                params["ad_format"] = ad_format
            if time_period:
                params["time_period"] = time_period

            data = await client.raw_search("google_ads_transparency_center", **params)

            return {
                "domain": domain,
                "region": region,
                "platform": platform or "all",
                "time_period": time_period,
                "raw": data,
            }

    def _parse_result(self, data: dict, from_cache: bool) -> AdsTransparencyResult:
        """Parse cached data into AdsTransparencyResult."""
        raw = data.get("raw", {})

        ads = []
        # API returns "ad_creatives" not "ads"
        for i, ad in enumerate(raw.get("ad_creatives", []), 1):
            advertiser = ad.get("advertiser", {})

            ads.append(
                AdCreative(
                    position=i,
                    ad_id=ad.get("id", ""),
                    advertiser_name=advertiser.get("name", ""),
                    advertiser_id=advertiser.get("id", ""),
                    target_domain=ad.get("target_domain", ""),
                    format=ad.get("format", ""),
                    first_shown=ad.get("first_shown_datetime", ""),
                    last_shown=ad.get("last_shown_datetime", ""),
                    days_displayed=ad.get("total_days_shown", 0),
                    ad_link=ad.get("details_link", ""),
                )
            )

        return AdsTransparencyResult(
            domain=data.get("domain", ""),
            region=data.get("region", "anywhere"),
            platform=data.get("platform", "all"),
            time_period=data.get("time_period", "last_30_days"),
            ads=ads,
            from_cache=from_cache,
        )
