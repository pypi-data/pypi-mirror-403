"""Databricks SQL alert generation for MangleFrames."""

from typing import Optional, List, Dict, Any
import json
import requests
from dataclasses import dataclass, asdict


@dataclass
class AlertConfig:
    """Base configuration for all alert types."""
    name: str
    table: str
    severity: Optional[str] = "medium"


@dataclass(kw_only=True)
class ThresholdAlert(AlertConfig):
    """Alert when column values exceed thresholds."""
    column: str
    operator: str  # >, <, >=, <=, =, !=
    threshold: float

    def to_api_request(self) -> Dict[str, Any]:
        """Convert to API request format."""
        return {
            "name": self.name,
            "table": self.table,
            "column": self.column,
            "operator": self.operator,
            "threshold": self.threshold,
            "severity": self.severity
        }


@dataclass(kw_only=True)
class NullRateAlert(AlertConfig):
    """Alert when null percentage exceeds threshold."""
    column: str
    max_null_pct: float

    def to_api_request(self) -> Dict[str, Any]:
        """Convert to API request format."""
        return {
            "name": self.name,
            "table": self.table,
            "column": self.column,
            "max_null_pct": self.max_null_pct,
            "severity": self.severity
        }


@dataclass(kw_only=True)
class RowCountAlert(AlertConfig):
    """Alert when row count is outside expected range."""
    min_rows: Optional[int] = None
    max_rows: Optional[int] = None

    def to_api_request(self) -> Dict[str, Any]:
        """Convert to API request format."""
        req = {
            "name": self.name,
            "table": self.table,
            "severity": self.severity
        }
        if self.min_rows is not None:
            req["min_rows"] = self.min_rows
        if self.max_rows is not None:
            req["max_rows"] = self.max_rows
        return req


@dataclass(kw_only=True)
class DataFreshnessAlert(AlertConfig):
    """Alert when data is stale."""
    date_column: str
    max_age_hours: int

    def to_api_request(self) -> Dict[str, Any]:
        """Convert to API request format."""
        return {
            "name": self.name,
            "table": self.table,
            "date_column": self.date_column,
            "max_age_hours": self.max_age_hours,
            "severity": self.severity
        }


@dataclass(kw_only=True)
class DuplicateKeysAlert(AlertConfig):
    """Alert when duplicate keys are found."""
    keys: List[str]
    max_duplicates: Optional[int] = None

    def to_api_request(self) -> Dict[str, Any]:
        """Convert to API request format."""
        req = {
            "name": self.name,
            "table": self.table,
            "keys": self.keys,
            "severity": self.severity
        }
        if self.max_duplicates is not None:
            req["max_duplicates"] = self.max_duplicates
        return req


@dataclass
class ReconciliationAlert:
    """Alert when tables don't match sufficiently."""
    name: str
    source_table: str
    target_table: str
    join_keys: List[str]
    min_match_rate: float
    severity: Optional[str] = "high"

    def to_api_request(self) -> Dict[str, Any]:
        """Convert to API request format."""
        return {
            "name": self.name,
            "source_table": self.source_table,
            "target_table": self.target_table,
            "join_keys": self.join_keys,
            "min_match_rate": self.min_match_rate,
            "severity": self.severity
        }


class AlertGenerator:
    """Generate Databricks SQL alerts from dataframes."""

    def __init__(self, viewer_url: str = "http://localhost:8765"):
        """Initialize alert generator.

        Args:
            viewer_url: URL of the MangleFrames viewer
        """
        self.viewer_url = viewer_url

    def generate_alert_sql(self, alert: AlertConfig) -> Dict[str, Any]:
        """Generate SQL for an alert definition.

        Args:
            alert: Alert configuration object

        Returns:
            Dictionary with SQL and Databricks query
        """
        # Determine endpoint based on alert type
        if isinstance(alert, ThresholdAlert):
            endpoint = "/api/alerts/threshold"
        elif isinstance(alert, NullRateAlert):
            endpoint = "/api/alerts/null_rate"
        elif isinstance(alert, RowCountAlert):
            endpoint = "/api/alerts/row_count"
        elif isinstance(alert, DataFreshnessAlert):
            endpoint = "/api/alerts/data_freshness"
        elif isinstance(alert, DuplicateKeysAlert):
            endpoint = "/api/alerts/duplicate_keys"
        elif isinstance(alert, ReconciliationAlert):
            endpoint = "/api/alerts/reconciliation"
        else:
            raise ValueError(f"Unknown alert type: {type(alert)}")

        # Make request to viewer API
        response = requests.post(
            f"{self.viewer_url}{endpoint}",
            json=alert.to_api_request()
        )
        response.raise_for_status()
        return response.json()

    def evaluate_alert(self, alert: AlertConfig) -> Dict[str, Any]:
        """Evaluate an alert against current data.

        Args:
            alert: Alert configuration object

        Returns:
            Dictionary with evaluation results
        """
        result = self.generate_alert_sql(alert)
        return result.get("evaluation", {})

    def get_templates(self) -> List[Dict[str, Any]]:
        """Get predefined alert templates.

        Returns:
            List of alert template configurations
        """
        response = requests.get(f"{self.viewer_url}/api/alerts/templates")
        response.raise_for_status()
        return response.json().get("templates", [])

    def create_databricks_alert(self, alert: AlertConfig, warehouse_id: str) -> Dict[str, Any]:
        """Generate Databricks API payload for alert creation.

        Args:
            alert: Alert configuration object
            warehouse_id: Databricks SQL warehouse ID

        Returns:
            Dictionary with Databricks API payload
        """
        # Generate SQL first
        alert_response = self.generate_alert_sql(alert)

        # Create Databricks config
        return {
            "name": alert.name,
            "query": {
                "query_text": alert_response["databricks_query"],
                "warehouse_id": warehouse_id
            },
            "condition": {
                "op": "GREATER_THAN",
                "operand": {
                    "column": {"name": "alert_value"}
                },
                "threshold": {
                    "value": {"double_value": 0}
                }
            },
            "custom_subject": f"Alert: {alert.name} - {{{{ALERT_STATUS}}}}",
            "custom_body": "The alert '{{ALERT_NAME}}' is {{ALERT_STATUS}}. Value: {{QUERY_RESULT_VALUE}}",
            "empty_result_state": "OK"
        }


# Convenience functions
def threshold_alert(name: str, table: str, column: str,
                   operator: str, threshold: float, **kwargs) -> ThresholdAlert:
    """Create a threshold alert."""
    return ThresholdAlert(
        name=name, table=table, column=column,
        operator=operator, threshold=threshold, **kwargs
    )


def null_rate_alert(name: str, table: str, column: str,
                   max_null_pct: float, **kwargs) -> NullRateAlert:
    """Create a null rate alert."""
    return NullRateAlert(
        name=name, table=table, column=column,
        max_null_pct=max_null_pct, **kwargs
    )


def row_count_alert(name: str, table: str, min_rows: Optional[int] = None,
                   max_rows: Optional[int] = None, **kwargs) -> RowCountAlert:
    """Create a row count alert."""
    return RowCountAlert(
        name=name, table=table, min_rows=min_rows,
        max_rows=max_rows, **kwargs
    )


def data_freshness_alert(name: str, table: str, date_column: str,
                        max_age_hours: int, **kwargs) -> DataFreshnessAlert:
    """Create a data freshness alert."""
    return DataFreshnessAlert(
        name=name, table=table, date_column=date_column,
        max_age_hours=max_age_hours, **kwargs
    )


def duplicate_keys_alert(name: str, table: str, keys: List[str],
                        max_duplicates: Optional[int] = None, **kwargs) -> DuplicateKeysAlert:
    """Create a duplicate keys alert."""
    return DuplicateKeysAlert(
        name=name, table=table, keys=keys,
        max_duplicates=max_duplicates, **kwargs
    )


def reconciliation_alert(name: str, source_table: str, target_table: str,
                        join_keys: List[str], min_match_rate: float, **kwargs) -> ReconciliationAlert:
    """Create a reconciliation alert."""
    return ReconciliationAlert(
        name=name, source_table=source_table, target_table=target_table,
        join_keys=join_keys, min_match_rate=min_match_rate, **kwargs
    )