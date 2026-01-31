"""
Neural LAB - AI Solutions Platform
Base classes and mixins for SDK.

Author: Anderson Henrique da Silva
Location: Minas Gerais, Brasil
Created: 2026-01-25
"""

from dataclasses import asdict, fields
from typing import Any


class DataclassMixin:
    """
    Mixin that adds to_dict() method to dataclasses.

    Usage:
        @dataclass
        class MyClass(DataclassMixin):
            name: str
            value: int

        obj = MyClass(name="test", value=42)
        data = obj.to_dict()  # {"name": "test", "value": 42}
    """

    def to_dict(self) -> dict[str, Any]:
        """
        Convert dataclass to dictionary.

        Returns:
            Dictionary with all field values
        """
        return asdict(self)

    def to_dict_non_null(self) -> dict[str, Any]:
        """
        Convert dataclass to dictionary, excluding None values.

        Returns:
            Dictionary with non-None field values only
        """
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def field_names(cls) -> list:
        """
        Get list of field names for this dataclass.

        Returns:
            List of field names
        """
        return [f.name for f in fields(cls)]
