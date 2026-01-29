#
# Copyright (c), 2025, Axius-SDC, Inc.
# All rights reserved.
# This file is distributed under the terms of the MIT License.
#
"""
Tests for Two-Tier Validation Strategy.

Tier 1 (Structural): Unknown elements, wrong nesting, cardinality -> REJECT
Tier 2 (Semantic): Type errors, pattern violations, range constraints -> QUARANTINE
"""

import unittest
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

from sdcvalidator.sdc4.validator import SDC4Validator
from sdcvalidator.sdc4.exceptions import SDC4StructuralValidationError
from sdcvalidator.sdc4.error_mapper import ErrorMapper
from sdcvalidator.core.exceptions import (
    XMLSchemaValidationError,
    XMLSchemaChildrenValidationError,
    XMLSchemaDecodeError
)


class TestTwoTierValidation(unittest.TestCase):
    """Tests for the Two-Tier Validation Strategy."""

    def setUp(self):
        """Set up test fixtures."""
        # Path to the SDC4 example schema
        self.schema_path = Path(__file__).parent.parent.parent / 'sdc4' / 'example' / 'dm-jsi5yxnvzsmsisgn2bvelkni.xsd'

        # Verify the schema exists
        if not self.schema_path.exists():
            self.skipTest(f"SDC4 example schema not found at {self.schema_path}")

    def test_tier1_unknown_element_rejection(self):
        """Test that unknown elements cause Tier 1 rejection."""
        # Create an instance with an unknown element (potential attack vector)
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<sdc4:dm-jsi5yxnvzsmsisgn2bvelkni
    xmlns:sdc4="https://semanticdatacharter.com/ns/sdc4/">
    <dm-label>StatePopulation</dm-label>
    <dm-language>en-US</dm-language>
    <dm-encoding>utf-8</dm-encoding>
    <MaliciousTag>attack_payload</MaliciousTag>
    <sdc4:ms-wnpz4qyrk369gnsivfsmysdf>
        <label>StatePopulation Data Cluster</label>
    </sdc4:ms-wnpz4qyrk369gnsivfsmysdf>
</sdc4:dm-jsi5yxnvzsmsisgn2bvelkni>
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            xml_path = Path(f.name)

        try:
            validator = SDC4Validator(self.schema_path)

            # Should raise SDC4StructuralValidationError
            with self.assertRaises(SDC4StructuralValidationError) as ctx:
                validator.validate_with_recovery(xml_path, save=False)

            # Verify error message contains the bad element name
            error_msg = str(ctx.exception)
            self.assertIn('Structural validation failed', error_msg)

        finally:
            xml_path.unlink()

    def test_tier1_misspelled_element_rejection(self):
        """Test that misspelled elements cause Tier 1 rejection."""
        # Create an instance with a misspelled element
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<sdc4:dm-jsi5yxnvzsmsisgn2bvelkni
    xmlns:sdc4="https://semanticdatacharter.com/ns/sdc4/">
    <dm-labl>StatePopulation</dm-labl>
    <dm-language>en-US</dm-language>
    <dm-encoding>utf-8</dm-encoding>
</sdc4:dm-jsi5yxnvzsmsisgn2bvelkni>
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            xml_path = Path(f.name)

        try:
            validator = SDC4Validator(self.schema_path)

            # Should raise SDC4StructuralValidationError
            with self.assertRaises(SDC4StructuralValidationError):
                validator.validate_with_recovery(xml_path, save=False)

        finally:
            xml_path.unlink()

    def test_tier2_semantic_error_quarantine(self):
        """Test that semantic errors (type violations) are quarantined with ExceptionalValue."""
        # Create an instance with a type error (string in integer field)
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<sdc4:dm-jsi5yxnvzsmsisgn2bvelkni
    xmlns:sdc4="https://semanticdatacharter.com/ns/sdc4/">
    <dm-label>StatePopulation</dm-label>
    <dm-language>en-US</dm-language>
    <dm-encoding>utf-8</dm-encoding>
    <sdc4:ms-wnpz4qyrk369gnsivfsmysdf>
        <label>StatePopulation Data Cluster</label>
        <sdc4:ms-iuikp1n1ydyfwncdqjd5wdoi>
            <sdc4:ms-cpq0lpgg887vpys05bucuep3>
                <label>State</label>
                <xdstring-value>California</xdstring-value>
            </sdc4:ms-cpq0lpgg887vpys05bucuep3>
        </sdc4:ms-iuikp1n1ydyfwncdqjd5wdoi>
        <sdc4:ms-ahfdavxt7dpx960rqi1qtb0l>
            <sdc4:ms-q1ey1sf5otsa97e76kb06hco>
                <label>Adult Population</label>
                <xdcount-value>not_a_number</xdcount-value>
                <xdcount-units>
                    <label>Count Units</label>
                    <xdstring-value>people</xdstring-value>
                </xdcount-units>
            </sdc4:ms-q1ey1sf5otsa97e76kb06hco>
        </sdc4:ms-ahfdavxt7dpx960rqi1qtb0l>
    </sdc4:ms-wnpz4qyrk369gnsivfsmysdf>
</sdc4:dm-jsi5yxnvzsmsisgn2bvelkni>
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            xml_path = Path(f.name)

        try:
            validator = SDC4Validator(self.schema_path)

            # Should NOT raise - semantic errors are quarantined
            recovered_tree = validator.validate_with_recovery(xml_path, save=False)

            # Verify we got a tree back (not an exception)
            self.assertIsNotNone(recovered_tree)
            self.assertIsInstance(recovered_tree, ET.ElementTree)

        finally:
            xml_path.unlink()

    def test_validate_structure_method(self):
        """Test the validate_structure() method returns structural errors."""
        # Create an instance with a structural error
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<sdc4:dm-jsi5yxnvzsmsisgn2bvelkni
    xmlns:sdc4="https://semanticdatacharter.com/ns/sdc4/">
    <dm-label>StatePopulation</dm-label>
    <UnknownElement>bad</UnknownElement>
    <dm-language>en-US</dm-language>
    <dm-encoding>utf-8</dm-encoding>
</sdc4:dm-jsi5yxnvzsmsisgn2bvelkni>
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            xml_path = Path(f.name)

        try:
            validator = SDC4Validator(self.schema_path)

            # Use validate_structure to check without raising
            structural_errors = validator.validate_structure(xml_path)

            # Should have at least one structural error
            self.assertGreater(len(structural_errors), 0)

        finally:
            xml_path.unlink()

    def test_validate_structure_clean_document(self):
        """Test validate_structure() returns empty list for valid structure."""
        # Create a structurally valid instance (may have semantic errors)
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<sdc4:dm-jsi5yxnvzsmsisgn2bvelkni
    xmlns:sdc4="https://semanticdatacharter.com/ns/sdc4/">
    <dm-label>StatePopulation</dm-label>
    <dm-language>en-US</dm-language>
    <dm-encoding>utf-8</dm-encoding>
    <sdc4:ms-wnpz4qyrk369gnsivfsmysdf>
        <label>StatePopulation Data Cluster</label>
    </sdc4:ms-wnpz4qyrk369gnsivfsmysdf>
</sdc4:dm-jsi5yxnvzsmsisgn2bvelkni>
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            xml_path = Path(f.name)

        try:
            validator = SDC4Validator(self.schema_path)

            # Use validate_structure to check
            structural_errors = validator.validate_structure(xml_path)

            # Should have no structural errors (semantic errors are OK)
            self.assertEqual(len(structural_errors), 0)

        finally:
            xml_path.unlink()

    def test_structural_error_before_semantic(self):
        """Test that documents with both error types fail on structural first."""
        # Create an instance with BOTH structural AND semantic errors
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<sdc4:dm-jsi5yxnvzsmsisgn2bvelkni
    xmlns:sdc4="https://semanticdatacharter.com/ns/sdc4/">
    <dm-label>StatePopulation</dm-label>
    <dm-language>en-US</dm-language>
    <dm-encoding>utf-8</dm-encoding>
    <BadStructure>oops</BadStructure>
    <sdc4:ms-wnpz4qyrk369gnsivfsmysdf>
        <label>StatePopulation Data Cluster</label>
        <sdc4:ms-ahfdavxt7dpx960rqi1qtb0l>
            <sdc4:ms-q1ey1sf5otsa97e76kb06hco>
                <label>Adult Population</label>
                <xdcount-value>not_a_number</xdcount-value>
                <xdcount-units>
                    <label>Count Units</label>
                    <xdstring-value>people</xdstring-value>
                </xdcount-units>
            </sdc4:ms-q1ey1sf5otsa97e76kb06hco>
        </sdc4:ms-ahfdavxt7dpx960rqi1qtb0l>
    </sdc4:ms-wnpz4qyrk369gnsivfsmysdf>
</sdc4:dm-jsi5yxnvzsmsisgn2bvelkni>
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            xml_path = Path(f.name)

        try:
            validator = SDC4Validator(self.schema_path)

            # Should raise SDC4StructuralValidationError (not quarantine)
            with self.assertRaises(SDC4StructuralValidationError):
                validator.validate_with_recovery(xml_path, save=False)

        finally:
            xml_path.unlink()


class TestErrorMapperClassification(unittest.TestCase):
    """Unit tests for ErrorMapper.is_structural_error() classification."""

    def setUp(self):
        """Set up test fixtures."""
        self.mapper = ErrorMapper()

    def test_unknown_element_is_structural(self):
        """Test that XMLSchemaChildrenValidationError with invalid_tag is structural."""
        # Create a mock error with invalid_tag set using a simple class
        class MockChildrenError(XMLSchemaChildrenValidationError):
            def __init__(self):
                self.invalid_tag = '{http://example.com}UnknownTag'
                self._reason = "Unexpected child with tag 'UnknownTag'"
                self._path = '/root/UnknownTag'

            @property
            def reason(self):
                return self._reason

            @property
            def path(self):
                return self._path

        error = MockChildrenError()
        self.assertTrue(self.mapper.is_structural_error(error))

    def test_type_violation_is_semantic(self):
        """Test that type violations are semantic (not structural)."""
        # Create a mock decode error (type violation)
        error = XMLSchemaDecodeError(
            validator=None,
            obj="not_a_number",
            decoder=None,
            reason="'not_a_number' is not a valid value for type xs:integer",
        )

        self.assertFalse(self.mapper.is_structural_error(error))

    def test_pattern_violation_is_semantic(self):
        """Test that pattern violations are semantic (not structural)."""
        error = XMLSchemaValidationError(
            validator=None,
            obj="bad-value",
            reason="pattern '[A-Z]{3}' not matched",
        )

        self.assertFalse(self.mapper.is_structural_error(error))

    def test_enumeration_violation_is_semantic(self):
        """Test that enumeration violations are semantic (not structural)."""
        error = XMLSchemaValidationError(
            validator=None,
            obj="invalid_choice",
            reason="value not in enumeration ['A', 'B', 'C']",
        )

        self.assertFalse(self.mapper.is_structural_error(error))

    def test_cardinality_violation_is_structural(self):
        """Test that cardinality (minOccurs/maxOccurs) violations are structural."""
        # Create a mock error for cardinality violation
        class MockCardinalityError(XMLSchemaChildrenValidationError):
            def __init__(self):
                self.invalid_tag = None  # Not an unknown element
                self._reason = "The particle 'element' occurs 0 times but the minimum is 1"
                self._path = '/root/element'

            @property
            def reason(self):
                return self._reason

            @property
            def path(self):
                return self._path

        error = MockCardinalityError()
        self.assertTrue(self.mapper.is_structural_error(error))


class TestSDC4StructuralValidationError(unittest.TestCase):
    """Unit tests for SDC4StructuralValidationError exception."""

    def test_error_message_format(self):
        """Test that error message is properly formatted."""
        # Create mock errors
        error1 = XMLSchemaValidationError(
            validator=None,
            obj="test",
            reason="Unexpected element 'BadTag'",
        )
        error1._path = "/root/BadTag"

        error2 = XMLSchemaValidationError(
            validator=None,
            obj="test",
            reason="Element 'AnotherBad' not allowed",
        )
        error2._path = "/root/AnotherBad"

        exc = SDC4StructuralValidationError([error1, error2])

        msg = str(exc)
        self.assertIn("Structural validation failed", msg)
        self.assertIn("Tier 1 rejection", msg)
        self.assertIn("1.", msg)
        self.assertIn("2.", msg)

    def test_error_count_property(self):
        """Test the error_count property."""
        error = XMLSchemaValidationError(
            validator=None,
            obj="test",
            reason="Test error",
        )

        exc = SDC4StructuralValidationError([error, error, error])
        self.assertEqual(exc.error_count, 3)


if __name__ == '__main__':
    unittest.main()
