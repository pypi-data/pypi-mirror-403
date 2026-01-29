#
# Copyright (c), 2025, Axius-SDC, Inc.
# All rights reserved.
# This file is distributed under the terms of the MIT License.
#
"""
SDC4-specific exceptions for validation.
"""

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from sdcvalidator.core.exceptions import XMLSchemaValidationError


class SDC4StructuralValidationError(Exception):
    """
    Raised when structural validation fails (Tier 1 rejection).

    This error indicates the XML document has structural violations
    (unknown elements, wrong nesting, cardinality violations) that
    cannot be recovered via ExceptionalValue quarantine.

    Structural errors include:
    - Unknown/unexpected elements not defined in the XSD
    - Missing required child elements (incomplete content)
    - Cardinality violations (minOccurs/maxOccurs)
    - Incorrect element nesting

    These errors represent potential security risks (e.g., mass assignment
    attacks) and must be rejected outright rather than quarantined.
    """

    def __init__(self, errors: List['XMLSchemaValidationError'], message: str = None):
        """
        Initialize the structural validation error.

        :param errors: List of structural validation errors that caused the rejection.
        :param message: Optional custom message. If None, a message is built from errors.
        """
        self.errors = errors
        if message is None:
            message = self._build_message()
        super().__init__(message)

    def _build_message(self) -> str:
        """Build a detailed error message from the list of structural errors."""
        lines = ["Structural validation failed (Tier 1 rejection):"]
        for i, error in enumerate(self.errors, 1):
            reason = error.reason or str(error)
            lines.append(f"  {i}. {reason}")
            if error.path:
                lines.append(f"     at: {error.path}")
        return "\n".join(lines)

    @property
    def error_count(self) -> int:
        """Return the number of structural errors."""
        return len(self.errors)
