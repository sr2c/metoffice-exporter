import datetime
import sys
import time
from typing import Dict, Tuple, Iterable, Any, Optional

import feedparser
from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server, Metric
from prometheus_client.registry import Collector


class MetOfficeAlerts:
    region: str

    _feed: Any
    _last_update: Optional[datetime.datetime]

    def __init__(self, region: str):
        self.region = region
        self._feed = None
        self._last_update = None

    def update(self) -> None:
        self._feed = feedparser.parse(
            f"http://www.metoffice.gov.uk/public/data/PWSCache/WarningsRSS/Region/{self.region}")
        self._last_update = datetime.datetime.now()

    def get_alert_count(self) -> Tuple[Dict[str, int], int]:
        counts = {
            "red": 0,
            "amber": 0,
            "yellow": 0,
        }
        total = 0
        if self._feed is None:
            self.update()
        if not self._last_update or self._last_update < (datetime.datetime.now() - datetime.timedelta(minutes=15)):
            self.update()
        for entry in self._feed.entries:  # type: ignore[union-attr]
            total += 1
            for level in counts:
                if entry.summary.lower().startswith(level):
                    counts[level] += 1
        return counts, total


class MetOfficeAlertsExporter(Collector):
    def __init__(self, region: str) -> None:
        self._alerts = MetOfficeAlerts(region)

    def collect(self) -> Iterable[Metric]:
        alerts, total = self._alerts.get_alert_count()
        for level in alerts.keys():
            gauge = GaugeMetricFamily(f"{level}_alert", f"Number of upcoming {level} alerts", labels=["region"])
            gauge.add_metric([self._alerts.region], alerts[level])
            yield gauge
        gauge = GaugeMetricFamily("unknown_alert", "Number of upcoming unknown alerts", labels=["region"])
        gauge.add_metric([self._alerts.region], total - sum(alerts.values()))
        yield gauge


if __name__ == "__main__":
    region = sys.argv[1] if len(sys.argv) > 1 else "gr"
    REGISTRY.register(MetOfficeAlertsExporter(region))
    start_http_server(9000)
    while True:
        time.sleep(1)
