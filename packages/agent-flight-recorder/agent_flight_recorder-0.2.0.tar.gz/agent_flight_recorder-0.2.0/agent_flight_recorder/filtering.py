"""
Request/response filtering and transformation for Agent Flight Recorder.

Provides utilities for redacting sensitive data, filtering fields,
and transforming requests/responses before caching.
"""

import re
import logging
from typing import Any, Dict, Callable, Optional, Pattern, List

logger = logging.getLogger(__name__)


class DataFilter:
    """Filter and transform request/response data for privacy and storage."""
    
    def __init__(self) -> None:
        """Initialize the data filter."""
        self.redaction_rules: List[Dict[str, Any]] = [
            {
                "pattern": r"api[-_]?key",
                "replacement": "[REDACTED_API_KEY]",
                "flags": re.IGNORECASE
            },
            {
                "pattern": r"authorization",
                "replacement": "[REDACTED_AUTH]",
                "flags": re.IGNORECASE
            },
            {
                "pattern": r"token",
                "replacement": "[REDACTED_TOKEN]",
                "flags": re.IGNORECASE
            },
            {
                "pattern": r"password",
                "replacement": "[REDACTED_PASSWORD]",
                "flags": re.IGNORECASE
            },
        ]
        self.custom_filters: List[Callable[[Any], Any]] = []
    
    def add_custom_filter(self, filter_fn: Callable[[Any], Any]) -> None:
        """
        Add a custom filter function.
        
        Args:
            filter_fn: Function that takes data and returns filtered data
        """
        self.custom_filters.append(filter_fn)
    
    def add_redaction_rule(
        self, 
        pattern: str, 
        replacement: str, 
        case_sensitive: bool = False
    ) -> None:
        """
        Add a custom redaction rule.
        
        Args:
            pattern: Regex pattern to match
            replacement: Replacement string
            case_sensitive: Whether pattern matching is case sensitive
        """
        flags = 0 if case_sensitive else re.IGNORECASE
        self.redaction_rules.append({
            "pattern": pattern,
            "replacement": replacement,
            "flags": flags
        })
    
    def filter_data(self, data: Any) -> Any:
        """
        Apply all filters to data.
        
        Args:
            data: Data to filter
            
        Returns:
            Filtered data
        """
        # Apply redaction rules
        filtered = self._redact_sensitive_data(data)
        
        # Apply custom filters
        for filter_fn in self.custom_filters:
            try:
                filtered = filter_fn(filtered)
            except Exception as e:
                logger.warning(f"Error applying custom filter: {e}")
        
        return filtered
    
    def _redact_sensitive_data(self, data: Any) -> Any:
        """
        Redact sensitive fields like API keys and tokens.
        
        Args:
            data: Data to redact
            
        Returns:
            Data with sensitive fields redacted
        """
        if isinstance(data, dict):
            redacted = {}
            for key, value in data.items():
                redacted[key] = self._redact_field(key, value)
            return redacted
        elif isinstance(data, list):
            return [self._redact_sensitive_data(item) for item in data]
        elif isinstance(data, str):
            return self._redact_string(data)
        else:
            return data
    
    def _redact_field(self, field_name: str, value: Any) -> Any:
        """
        Redact a single field if it matches sensitive patterns.
        
        Args:
            field_name: Name of the field
            value: Field value
            
        Returns:
            Redacted value if sensitive, original otherwise
        """
        # Check if field name matches any redaction rules
        for rule in self.redaction_rules:
            if re.search(rule["pattern"], field_name, rule["flags"]):
                if isinstance(value, str):
                    return rule["replacement"]
                elif isinstance(value, dict):
                    return {"__redacted__": rule["replacement"]}
                else:
                    return rule["replacement"]
        
        # Recursively process nested data
        return self._redact_sensitive_data(value)
    
    def _redact_string(self, text: str) -> str:
        """
        Redact sensitive patterns in a string.
        
        Args:
            text: String to redact
            
        Returns:
            Redacted string
        """
        for rule in self.redaction_rules:
            text = re.sub(
                rule["pattern"],
                rule["replacement"],
                text,
                flags=rule["flags"]
            )
        return text
    
    def filter_fields(
        self, 
        data: Any, 
        allowed_fields: Optional[List[str]] = None,
        excluded_fields: Optional[List[str]] = None
    ) -> Any:
        """
        Filter to only include/exclude specific fields.
        
        Args:
            data: Data to filter
            allowed_fields: Only include these fields (None = all)
            excluded_fields: Exclude these fields (None = none)
            
        Returns:
            Filtered data
        """
        if not isinstance(data, dict):
            return data
        
        filtered = {}
        
        for key, value in data.items():
            # Check if field should be included
            if allowed_fields and key not in allowed_fields:
                continue
            
            if excluded_fields and key in excluded_fields:
                continue
            
            # Recursively filter nested data
            if isinstance(value, dict):
                filtered[key] = self.filter_fields(
                    value, 
                    allowed_fields, 
                    excluded_fields
                )
            elif isinstance(value, list):
                filtered[key] = [
                    self.filter_fields(
                        item, 
                        allowed_fields, 
                        excluded_fields
                    ) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                filtered[key] = value
        
        return filtered
    
    def filter_large_responses(
        self, 
        data: Any, 
        max_size_bytes: int = 1024 * 100  # 100 KB default
    ) -> Any:
        """
        Truncate responses larger than max size.
        
        Args:
            data: Data to potentially truncate
            max_size_bytes: Maximum size in bytes
            
        Returns:
            Truncated data
        """
        import json
        
        try:
            data_str = json.dumps(data)
            size = len(data_str.encode('utf-8'))
            
            if size > max_size_bytes:
                logger.warning(
                    f"Response size {size} bytes exceeds "
                    f"limit {max_size_bytes} bytes, truncating"
                )
                # Simple truncation
                return {
                    "__truncated__": True,
                    "original_size": size,
                    "max_size": max_size_bytes,
                    "preview": data_str[:200] + "..."
                }
        except:
            pass
        
        return data
