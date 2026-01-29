"""Google Trends data models."""

from dataclasses import dataclass, field


@dataclass
class TrendsTimelinePoint:
    """Single data point in trends timeline."""

    date: str
    values: list[dict]  # [{query: str, value: int}]


@dataclass
class TrendsInterestResult:
    """Interest over time result."""

    query: str
    averages: list[dict] = field(default_factory=list)  # [{query, value}]
    timeline: list[TrendsTimelinePoint] = field(default_factory=list)
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        # Flatten timeline values for easier rendering
        timeline_flat = []
        for t in self.timeline:
            value = t.values[0].get("extracted_value", 0) if t.values else 0
            timeline_flat.append({"date": t.date, "value": value, "values": t.values})

        return {
            "query": self.query,
            "cached": self.from_cache,
            "averages": self.averages,
            "timeline": timeline_flat,
        }


@dataclass
class TrendsRelatedItem:
    """Single related query or topic."""

    query: str
    value: int
    link: str = ""


@dataclass
class TrendsRelatedResult:
    """Related queries or topics result."""

    query: str
    top: list[TrendsRelatedItem] = field(default_factory=list)
    rising: list[TrendsRelatedItem] = field(default_factory=list)
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "cached": self.from_cache,
            "top": [
                {"query": t.query, "value": t.value, "link": t.link}
                for t in self.top
            ],
            "rising": [
                {"query": r.query, "value": r.value, "link": r.link}
                for r in self.rising
            ],
        }


@dataclass
class TrendsGeoItem:
    """Interest by region item."""

    location: str
    location_code: str
    value: int


@dataclass
class TrendsGeoResult:
    """Interest by region result."""

    query: str
    regions: list[TrendsGeoItem] = field(default_factory=list)
    from_cache: bool = False

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dict."""
        return {
            "query": self.query,
            "cached": self.from_cache,
            "regions": [
                {
                    "location": r.location,
                    "location_code": r.location_code,
                    "value": r.value,
                }
                for r in self.regions
            ],
        }
