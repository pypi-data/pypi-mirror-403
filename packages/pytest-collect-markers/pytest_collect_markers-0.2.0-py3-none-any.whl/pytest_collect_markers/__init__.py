"""pytest plugin to collect and output test markers to JSON."""

import json
from pathlib import Path

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register command line options."""
    group = parser.getgroup("marker-collection")
    group.addoption(
        "--collect-markers",
        action="store_true",
        default=False,
        help="Collect markers from tests and output to JSON file",
    )
    group.addoption(
        "--markers-output",
        action="store",
        default="markers.json",
        help="Output file path for collected markers (default: markers.json)",
    )


def pytest_configure(config: pytest.Config) -> None:
    """Register the plugin if --collect-markers is enabled."""
    if config.getoption("collect_markers"):
        config.pluginmanager.register(MarkerCollectorPlugin(config), "marker_collector")


class MarkerCollectorPlugin:
    """Plugin that collects markers from test items and writes to JSON."""

    def __init__(self, config: pytest.Config) -> None:
        self.config = config
        self.markers: dict[str, list[str]] = {}

    def pytest_collection_modifyitems(
        self, items: list[pytest.Item]
    ) -> None:
        """Extract markers from collected test items."""
        for item in items:
            marker_names = [marker.name for marker in item.iter_markers()]
            self.markers[item.nodeid] = marker_names

    def pytest_sessionfinish(self, session: pytest.Session) -> None:
        """Write collected markers to JSON file."""
        output_path = Path(self.config.getoption("markers_output"))
        with output_path.open("w") as f:
            json.dump(self.markers, f, indent=2)
