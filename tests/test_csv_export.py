"""Unit tests for CSV export utility."""
from datetime import datetime

from app.utils.csv_export import export_to_csv, scan_events_to_csv_data


class TestExportToCsv:
    """Tests for export_to_csv."""

    def test_empty_data(self):
        result = export_to_csv([], ["a", "b"])
        assert "a,b" in result
        # Only header, no rows
        lines = result.strip().split("\n")
        assert len(lines) == 1

    def test_basic_export(self):
        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        result = export_to_csv(data, ["name", "age"])
        assert "Alice" in result
        assert "Bob" in result
        lines = result.strip().split("\n")
        assert len(lines) == 3  # header + 2 rows

    def test_datetime_converted_to_iso(self):
        dt = datetime(2026, 1, 15, 12, 30, 0)
        data = [{"ts": dt, "val": "x"}]
        result = export_to_csv(data, ["ts", "val"])
        assert "2026-01-15T12:30:00" in result

    def test_extra_columns_ignored(self):
        data = [{"a": 1, "b": 2, "c": 3}]
        result = export_to_csv(data, ["a", "b"])
        assert "c" not in result.split("\n")[0]  # c not in header


class TestScanEventsToCsvData:
    """Tests for scan_events_to_csv_data."""

    def test_empty_list(self):
        assert scan_events_to_csv_data([]) == []

    def test_converts_scan_event(self):
        class MockEvent:
            timestamp = datetime(2026, 2, 1, 10, 0, 0)
            user_agent = "Mozilla/5.0"
            ip_hash = "abc123"
            referrer = "https://google.com"

        result = scan_events_to_csv_data([MockEvent()])
        assert len(result) == 1
        assert result[0]["user_agent"] == "Mozilla/5.0"
        assert result[0]["ip_hash"] == "abc123"

    def test_null_referrer(self):
        class MockEvent:
            timestamp = datetime(2026, 2, 1)
            user_agent = "Bot"
            ip_hash = "xyz"
            referrer = None

        result = scan_events_to_csv_data([MockEvent()])
        assert result[0]["referrer"] == ""
