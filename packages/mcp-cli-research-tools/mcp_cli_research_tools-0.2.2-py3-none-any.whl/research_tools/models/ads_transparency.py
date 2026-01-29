"""Google Ads Transparency Center data models."""

from dataclasses import dataclass, field


@dataclass
class AdCreative:
    """Single ad creative from Ads Transparency Center."""

    position: int
    ad_id: str
    advertiser_name: str
    advertiser_id: str
    target_domain: str
    format: str  # text, image, video
    first_shown: str
    last_shown: str
    days_displayed: int
    ad_link: str


@dataclass
class AdsTransparencyResult:
    """Result from Ads Transparency Center lookup."""

    domain: str
    region: str
    platform: str
    time_period: str
    ads: list[AdCreative] = field(default_factory=list)
    from_cache: bool = False

    @property
    def total_ads(self) -> int:
        """Total number of ads."""
        return len(self.ads)

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "domain": self.domain,
            "region": self.region,
            "platform": self.platform,
            "time_period": self.time_period,
            "cached": self.from_cache,
            "total_ads": self.total_ads,
            "ads": [
                {
                    "position": ad.position,
                    "ad_id": ad.ad_id,
                    "advertiser_name": ad.advertiser_name,
                    "advertiser_id": ad.advertiser_id,
                    "target_domain": ad.target_domain,
                    "format": ad.format,
                    "first_shown": ad.first_shown,
                    "last_shown": ad.last_shown,
                    "days_displayed": ad.days_displayed,
                    "ad_link": ad.ad_link,
                }
                for ad in self.ads
            ],
        }
