"""CSV export utilities."""
import csv
import io
from datetime import datetime
from typing import Any


def export_to_csv(data: list[dict[str, Any]], columns: list[str]) -> str:
    """Export data to CSV format.
    
    Args:
        data: List of dictionaries to export
        columns: List of column names to include
        
    Returns:
        CSV formatted string
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    
    writer.writeheader()
    for row in data:
        # Convert datetime objects to ISO format strings
        processed_row = {}
        for key, value in row.items():
            if isinstance(value, datetime):
                processed_row[key] = value.isoformat()
            else:
                processed_row[key] = value
        writer.writerow(processed_row)
    
    return output.getvalue()


def scan_events_to_csv_data(scan_events: list) -> list[dict[str, Any]]:
    """Convert scan events to CSV-ready data.
    
    Args:
        scan_events: List of ScanEvent objects
        
    Returns:
        List of dictionaries ready for CSV export
    """
    return [
        {
            "timestamp": event.timestamp,
            "user_agent": event.user_agent,
            "ip_hash": event.ip_hash,
            "referrer": event.referrer or "",
        }
        for event in scan_events
    ]
