"""
SKU Value Object
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SKU:
    """Immutable SKU value object with format validation."""
    
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("SKU cannot be empty.")
        # SKU format: alphanumeric with hyphens, 3-50 chars
        if not re.match(r'^[A-Za-z0-9\-]{3,50}$', self.value):
            raise ValueError(
                f"Invalid SKU format: '{self.value}'. "
                "SKU must be 3-50 alphanumeric characters with hyphens."
            )

    def __str__(self):
        return self.value
