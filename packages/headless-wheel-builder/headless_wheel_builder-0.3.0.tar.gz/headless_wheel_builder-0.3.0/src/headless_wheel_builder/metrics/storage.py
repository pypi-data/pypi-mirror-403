"""Storage backend for metrics data."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from headless_wheel_builder.metrics.models import BuildMetrics, TimeRange


@dataclass
class MetricsStorage:
    """Storage backend for metrics data.

    Stores metrics in a JSON file with optional rotation.

    Attributes:
        path: Path to metrics file
        max_entries: Maximum entries to keep (0 = unlimited)
    """

    path: Path = field(default_factory=lambda: Path.home() / ".hwb" / "metrics.json")
    max_entries: int = 10000

    def __post_init__(self) -> None:
        """Ensure storage directory exists."""
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> list[dict[str, Any]]:
        """Load metrics from file."""
        if not self.path.exists():
            return []

        try:
            content = self.path.read_text(encoding="utf-8")
            data = json.loads(content)
            return data.get("metrics", [])
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, metrics: list[dict[str, Any]]) -> None:
        """Save metrics to file."""
        # Rotate if needed
        if self.max_entries > 0 and len(metrics) > self.max_entries:
            metrics = metrics[-self.max_entries :]

        data = {
            "version": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
        }

        content = json.dumps(data, indent=2)
        self.path.write_text(content, encoding="utf-8")

    def add(self, metrics: BuildMetrics) -> None:
        """Add a build metrics entry.

        Args:
            metrics: Build metrics to add
        """
        entries = self._load()
        entries.append(metrics.to_dict())
        self._save(entries)

    def add_many(self, metrics_list: list[BuildMetrics]) -> None:
        """Add multiple metrics entries.

        Args:
            metrics_list: List of build metrics to add
        """
        entries = self._load()
        for metrics in metrics_list:
            entries.append(metrics.to_dict())
        self._save(entries)

    def get_all(self) -> list[BuildMetrics]:
        """Get all stored metrics.

        Returns:
            List of all build metrics
        """
        entries = self._load()
        return [BuildMetrics.from_dict(e) for e in entries]

    def get_by_package(self, package: str) -> list[BuildMetrics]:
        """Get metrics for a specific package.

        Args:
            package: Package name

        Returns:
            List of build metrics for the package
        """
        all_metrics = self.get_all()
        return [m for m in all_metrics if m.package == package]

    def get_by_time_range(self, time_range: TimeRange) -> list[BuildMetrics]:
        """Get metrics within a time range.

        Args:
            time_range: Time range to filter by

        Returns:
            List of build metrics within the range
        """
        if time_range == TimeRange.ALL:
            return self.get_all()

        cutoff_seconds = time_range.to_seconds()
        now = datetime.now(timezone.utc)
        all_metrics = self.get_all()

        result: list[BuildMetrics] = []
        for m in all_metrics:
            if m.timestamp:
                try:
                    ts = datetime.fromisoformat(m.timestamp.replace("Z", "+00:00"))
                    delta = (now - ts).total_seconds()
                    if delta <= cutoff_seconds:
                        result.append(m)
                except ValueError:
                    pass

        return result

    def get_recent(self, count: int = 10) -> list[BuildMetrics]:
        """Get most recent metrics.

        Args:
            count: Number of entries to return

        Returns:
            List of recent build metrics
        """
        all_metrics = self.get_all()
        return all_metrics[-count:] if len(all_metrics) > count else all_metrics

    def get_failures(self, count: int = 10) -> list[BuildMetrics]:
        """Get recent failures.

        Args:
            count: Maximum number of failures to return

        Returns:
            List of failed build metrics
        """
        all_metrics = self.get_all()
        failures = [m for m in all_metrics if not m.success]
        return failures[-count:] if len(failures) > count else failures

    def clear(self) -> None:
        """Clear all stored metrics."""
        self._save([])

    def export(self, path: Path, format: str = "json") -> None:
        """Export metrics to file.

        Args:
            path: Export file path
            format: Export format (json or csv)
        """
        metrics = self.get_all()

        if format == "csv":
            self._export_csv(path, metrics)
        else:
            self._export_json(path, metrics)

    def _export_json(self, path: Path, metrics: list[BuildMetrics]) -> None:
        """Export as JSON."""
        data = [m.to_dict() for m in metrics]
        content = json.dumps(data, indent=2)
        path.write_text(content, encoding="utf-8")

    def _export_csv(self, path: Path, metrics: list[BuildMetrics]) -> None:
        """Export as CSV."""
        if not metrics:
            path.write_text("", encoding="utf-8")
            return

        # CSV header
        headers = [
            "timestamp",
            "package",
            "version",
            "success",
            "duration_seconds",
            "wheel_size_bytes",
            "python_version",
            "platform",
            "isolation",
            "error",
        ]

        lines = [",".join(headers)]

        for m in metrics:
            values = [
                m.timestamp or "",
                m.package,
                m.version,
                str(m.success),
                str(m.duration_seconds),
                str(m.wheel_size_bytes or ""),
                m.python_version,
                m.platform,
                m.isolation,
                (m.error or "").replace(",", ";").replace("\n", " ")[:100],
            ]
            lines.append(",".join(values))

        path.write_text("\n".join(lines), encoding="utf-8")
