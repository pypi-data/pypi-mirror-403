"""
Analytics Aggregator Module

Simple aggregation engine for pipeline dashboard cards.
Aggregates data from case_data fields based on card configuration.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from topaz_agent_kit.utils.logger import Logger


class AnalyticsAggregator:
    """
    Simple aggregation engine for dashboard cards.
    
    Aggregates data from case_data fields based on card configuration.
    """
    
    def __init__(self, logger: Optional[Logger] = None):
        """
        Initialize AnalyticsAggregator.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or Logger("AnalyticsAggregator")
    
    def aggregate(self, cases: List[Dict[str, Any]], card_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate data for a single card configuration.
        
        Args:
            cases: Filtered cases (already filtered by pipeline/time/status/search)
            card_config: Card configuration from YAML
            
        Returns:
            Aggregated data for the card
        """
        card_type = card_config.get("type")
        
        if not card_type:
            self.logger.error("Card config missing 'type' field")
            return {"error": "Card config missing 'type' field"}
        
        try:
            if card_type == "metric":
                return self._aggregate_metric(cases, card_config)
            elif card_type == "percentage":
                return self._aggregate_percentage(cases, card_config)
            elif card_type == "donut":
                return self._aggregate_donut(cases, card_config)
            elif card_type == "bar":
                return self._aggregate_bar(cases, card_config)
            elif card_type == "timeline":
                return self._aggregate_timeline(cases, card_config)
            else:
                self.logger.error("Unknown card type: {}", card_type)
                return {"error": f"Unknown card type: {card_type}"}
        except Exception as e:
            self.logger.error("Error aggregating card {}: {}", card_config.get("title", "unknown"), e)
            return {"error": str(e)}
    
    def _aggregate_metric(self, cases: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate metric card (count, sum, avg, min, max)"""
        field = config.get("field")
        if not field:
            return {"error": "Metric card missing 'field' configuration"}
        
        agg_type = config.get("aggregation", "count")
        
        values = []
        cases_with_field = 0
        for case in cases:
            value = self._extract_field(case, field)
            if value is not None:
                cases_with_field += 1
                # Try to convert to number if possible
                try:
                    if isinstance(value, (int, float)):
                        values.append(value)
                    elif isinstance(value, str):
                        # Try to parse as number
                        try:
                            values.append(float(value))
                        except ValueError:
                            # Not a number, skip
                            pass
                    else:
                        # Boolean or other type - count as 1 if truthy
                        if value:
                            values.append(1)
                except (ValueError, TypeError):
                    # Skip non-numeric values
                    pass
        
        # Log debug info if no values found
        if not values and cases_with_field == 0 and len(cases) > 0:
            # Sample a case to see what's available
            sample_case = cases[0]
            case_data = sample_case.get("case_data", {})
            
            # Try to extract the field to see what happens
            sample_value = self._extract_field(sample_case, field)
            
            # Check if the field path starts with a known agent output (like argus_anomaly_detector)
            field_parts = field.split(".")
            first_part = field_parts[0] if field_parts else None
            agent_data = case_data.get(first_part) if first_part and isinstance(case_data, dict) else None
            
            self.logger.warning(
                "No cases found with field '{}' for metric card '{}' (total cases: {}).\n"
                "  Sample case_id: {}\n"
                "  Sample extracted value: {}\n"
                "  Sample case_data top-level keys: {}\n"
                "  Sample _list_view.pipeline_fields keys: {}\n"
                "  {} structure: {}",
                field,
                config.get("title", "unknown"),
                len(cases),
                sample_case.get("case_id", "unknown"),
                sample_value,
                list(case_data.keys())[:10] if isinstance(case_data, dict) else "not a dict",
                list(case_data.get("_list_view", {}).get("pipeline_fields", {}).keys()) if isinstance(case_data.get("_list_view", {}).get("pipeline_fields"), dict) else [],
                first_part or "N/A",
                agent_data if isinstance(agent_data, dict) else (type(agent_data).__name__ if agent_data is not None else "not found")
            )
        
        if not values:
            format_type = config.get("format", "number")
            decimals = config.get("decimals", 0)
            return {
                "value": 0,
                "formatted": self._format_value(0, format_type, decimals, config)
            }
        
        if agg_type == "count":
            result = len(values)
        elif agg_type == "sum":
            result = sum(values)
        elif agg_type == "avg":
            result = sum(values) / len(values)
        elif agg_type == "min":
            result = min(values)
        elif agg_type == "max":
            result = max(values)
        else:
            result = len(values)
        
        format_type = config.get("format", "number")
        decimals = config.get("decimals", 0)
        
        return {
            "value": result,
            "formatted": self._format_value(result, format_type, decimals, config)
        }
    
    def _aggregate_percentage(self, cases: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate percentage card"""
        numerator_config = config.get("numerator")
        denominator_config = config.get("denominator")
        
        if not numerator_config or not denominator_config:
            return {"error": "Percentage card missing 'numerator' or 'denominator' configuration"}
        
        # Calculate numerator
        numerator = self._count_with_filter(cases, numerator_config)
        
        # Calculate denominator
        if denominator_config.get("field") == "total":
            denominator = len(cases)
        else:
            denominator = self._count_with_filter(cases, denominator_config)
        
        if denominator == 0:
            return {
                "value": 0,
                "numerator": 0,
                "denominator": 0,
                "formatted": "0%"
            }
        
        percentage = (numerator / denominator) * 100
        
        return {
            "value": percentage / 100,  # Decimal form (0.25 for 25%)
            "numerator": numerator,
            "denominator": denominator,
            "formatted": f"{percentage:.1f}%"
        }
    
    def _aggregate_donut(self, cases: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate donut chart (group by field)"""
        field = config.get("field")
        if not field:
            return {"error": "Donut card missing 'field' configuration"}
        
        groups = {}
        for case in cases:
            value = self._extract_field(case, field)
            if value is not None:
                value_str = str(value)
                groups[value_str] = groups.get(value_str, 0) + 1
        
        total = sum(groups.values())
        
        # Calculate percentages
        result = {}
        for key, count in groups.items():
            percentage = (count / total * 100) if total > 0 else 0
            result[key] = {
                "count": count,
                "percentage": percentage
            }
        
        return result
    
    def _aggregate_bar(self, cases: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate bar chart (same as donut, different visualization)"""
        return self._aggregate_donut(cases, config)
    
    def _aggregate_timeline(self, cases: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate timeline card"""
        field = config.get("field", "created_at")
        group_by = config.get("group_by", "day")
        
        # Group cases by time
        timeline_data = {}
        for case in cases:
            date_str = self._extract_field(case, field)
            if not date_str:
                continue
            
            # Parse and group by time period
            date_key = self._group_by_time(date_str, group_by)
            if date_key:
                if date_key not in timeline_data:
                    timeline_data[date_key] = []
                timeline_data[date_key].append(case)
        
        # Format for frontend
        result = {}
        for date_key, date_cases in timeline_data.items():
            result[date_key] = {
                "total": len(date_cases),
                "by_status": self._group_by_status(date_cases)
            }
        
        return result
    
    def _extract_field(self, case: Dict[str, Any], field_path: str) -> Any:
        """
        Extract field value from case_data using dot notation.
        
        Checks multiple locations:
        1. Direct in case_data (for raw agent outputs)
        2. In case_data._list_view (for list view fields)
        3. In case_data._detail_view (for detail view fields)
        
        Args:
            case: Case dictionary
            field_path: Dot-notation path (e.g., "agent_id.field" or "status")
            
        Returns:
            Field value or None
        """
        # Handle special fields
        if field_path == "status":
            return case.get("status")
        elif field_path == "created_at":
            return case.get("created_at")
        elif field_path == "total":
            return 1  # For counting
        
        # Navigate through case_data using dot notation
        case_data = case.get("case_data", {})
        if not case_data:
            self.logger.info("Case {} has no case_data", case.get("case_id", "unknown"))
            return None
        
        # Try multiple locations: direct, _list_view.pipeline_fields, _list_view, _detail_view
        # First, try direct access in case_data (for raw agent outputs like argus_anomaly_detector)
        parts = field_path.split(".")
        value = case_data
        
        for i, part in enumerate(parts):
            if isinstance(value, dict):
                value = value.get(part)
                if value is not None:
                    # Continue to next part
                    continue
                else:
                    # Part not found at this level
                    # Special handling: check if the previous value (before trying to get 'part') 
                    # has 'result' or 'parsed' keys (common pattern for agent outputs)
                    # We need to reconstruct the previous value
                    prev_value = case_data
                    for j in range(i):
                        if isinstance(prev_value, dict):
                            prev_value = prev_value.get(parts[j])
                        else:
                            prev_value = None
                            break
                    
                    if isinstance(prev_value, dict) and ('result' in prev_value or 'parsed' in prev_value):
                        # Try 'result' first, then 'parsed'
                        for wrapper_key in ['result', 'parsed']:
                            if wrapper_key in prev_value:
                                wrapper_value = prev_value[wrapper_key]
                                if isinstance(wrapper_value, dict):
                                    # Try to find the remaining path inside the wrapper
                                    remaining_parts = parts[i:]
                                    nested_value = wrapper_value
                                    found = True
                                    for nested_part in remaining_parts:
                                        if isinstance(nested_value, dict):
                                            nested_value = nested_value.get(nested_part)
                                            if nested_value is None:
                                                found = False
                                                break
                                        else:
                                            found = False
                                            break
                                    if found and nested_value is not None:
                                        return nested_value
                    # Try next location
                    break
            else:
                # Value is not a dict, can't continue
                if i == 0:
                    # Log when we can't even access the first part
                    self.logger.warning(
                        "Field path '{}' - '{}' not found or not a dict in case_data.\n"
                        "  Available top-level keys: {}\n"
                        "  Case ID: {}",
                        field_path, parts[0],
                        list(case_data.keys())[:20] if isinstance(case_data, dict) else "not a dict",
                        case.get("case_id", "unknown")
                    )
                break
        else:
            # Successfully found the value directly (all parts matched)
            if value is not None:
                return value
        
        # Try _list_view.pipeline_fields (fields are stored by their key, not full path)
        list_view = case_data.get("_list_view", {})
        if isinstance(list_view, dict):
            pipeline_fields = list_view.get("pipeline_fields", {})
            if isinstance(pipeline_fields, dict):
                # Check if there's a pipeline field with this key
                # For paths like "argus_anomaly_detector.anomaly_type", try "anomaly_type"
                # For paths like "current_journal.amount", try "amount"
                last_part = parts[-1] if parts else None
                if last_part and last_part in pipeline_fields:
                    field_data = pipeline_fields[last_part]
                    # pipeline_fields stores {value, label, type}, extract the value
                    if isinstance(field_data, dict) and "value" in field_data:
                        return field_data["value"]
                    elif not isinstance(field_data, dict):
                        # Sometimes it's stored directly as the value
                        return field_data
        
        # Try _list_view directly (for backwards compatibility)
        if isinstance(list_view, dict):
            value = list_view
            for i, part in enumerate(parts):
                if isinstance(value, dict):
                    value = value.get(part)
                    if value is not None:
                        continue
                    else:
                        break
                else:
                    break
            else:
                if value is not None:
                    return value
        
        # Try _detail_view
        detail_view = case_data.get("_detail_view", {})
        if isinstance(detail_view, dict):
            value = detail_view
            for i, part in enumerate(parts):
                if isinstance(value, dict):
                    value = value.get(part)
                    if value is not None:
                        continue
                    else:
                        break
                else:
                    break
            else:
                if value is not None:
                    return value
        
        # Not found in any location - log for debugging
        available_keys = list(case_data.keys()) if isinstance(case_data, dict) else "not a dict"
        list_view_keys = list(case_data.get("_list_view", {}).keys()) if isinstance(case_data.get("_list_view"), dict) else []
        detail_view_keys = list(case_data.get("_detail_view", {}).keys()) if isinstance(case_data.get("_detail_view"), dict) else []
        
        self.logger.debug(
            "Field path '{}' not found in case {}.\n"
            "  Available top-level keys: {}\n"
            "  _list_view keys: {}\n"
            "  _detail_view keys: {}",
            field_path,
            case.get("case_id", "unknown"),
            available_keys,
            list_view_keys,
            detail_view_keys
        )
        return None
    
    def _count_with_filter(self, cases: List[Dict[str, Any]], config: Dict[str, Any]) -> int:
        """
        Count cases matching filter criteria.
        
        Args:
            cases: List of cases
            config: Filter configuration with 'field' and optional 'filter' value
            
        Returns:
            Count of matching cases
        """
        field = config.get("field")
        if not field:
            return 0
        
        filter_value = config.get("filter")
        
        count = 0
        for case in cases:
            value = self._extract_field(case, field)
            
            if filter_value is not None:
                # Compare value with filter
                # Handle boolean filter: filter: true means count truthy values
                if filter_value is True:
                    # Count truthy values (True, 1, non-empty strings, etc.)
                    if value:
                        count += 1
                elif filter_value is False:
                    # Count falsy values (False, 0, empty strings, None, etc.)
                    if not value:
                        count += 1
                elif isinstance(value, bool) and isinstance(filter_value, bool):
                    if value == filter_value:
                        count += 1
                elif isinstance(value, (int, float)) and isinstance(filter_value, (int, float)):
                    if value == filter_value:
                        count += 1
                elif str(value) == str(filter_value):
                    count += 1
            else:
                # Count all non-null values
                if value is not None:
                    count += 1
        
        return count
    
    def _format_value(self, value: float, format_type: str, decimals: int, config: Dict[str, Any]) -> str:
        """
        Format value based on type.
        
        Args:
            value: Numeric value to format
            format_type: Format type (number, percentage, currency)
            decimals: Number of decimal places
            config: Card configuration (for currency symbol, etc.)
            
        Returns:
            Formatted string
        """
        if format_type == "percentage":
            return f"{value * 100:.{decimals}f}%"
        elif format_type == "currency":
            currency = config.get("currency", "USD")
            symbol = "$" if currency == "USD" else currency
            return f"{symbol}{value:,.{decimals}f}"
        else:
            return f"{value:.{decimals}f}"
    
    def _group_by_time(self, date_str: str, group_by: str) -> Optional[str]:
        """
        Group date string by time period.
        
        Args:
            date_str: Date string (ISO format or SQLite format)
            group_by: Grouping type (hour, day, week, month)
            
        Returns:
            Group key string or None
        """
        try:
            # Parse date string
            if "T" in date_str:
                # ISO format
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            elif " " in date_str:
                # SQLite format (YYYY-MM-DD HH:MM:SS)
                dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            else:
                # Date only
                dt = datetime.strptime(date_str, "%Y-%m-%d")
            
            if group_by == "hour":
                return dt.strftime("%Y-%m-%d %H:00")
            elif group_by == "day":
                return dt.strftime("%Y-%m-%d")
            elif group_by == "week":
                # Get week number
                week = dt.isocalendar()[1]
                year = dt.year
                return f"{year}-W{week:02d}"
            elif group_by == "month":
                return dt.strftime("%Y-%m")
            else:
                # Default to day
                return dt.strftime("%Y-%m-%d")
        except Exception as e:
            self.logger.warning("Failed to parse date '{}': {}", date_str, e)
            return None
    
    def _group_by_status(self, cases: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Group cases by status.
        
        Args:
            cases: List of cases
            
        Returns:
            Dictionary mapping status to count
        """
        statuses = {}
        for case in cases:
            status = case.get("status", "unknown")
            statuses[status] = statuses.get(status, 0) + 1
        return statuses
