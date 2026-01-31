"""Tests for generated telescope parameter validation.

This module tests the automatically generated Pydantic models to ensure
telescope parameter validation matches the schema specification.
"""

from math import isclose

import pytest
from pydantic import ValidationError

from qualpipe_webapp.backend.generated.qualpipe_criterion_model import (
    CriteriaReport,
    RangeCriterionConfig,
    TelescopeRangeCriterionConfig,
    TelescopeThresholdCriterionConfig,
    ThresholdCriterionConfig,
)


class TestParameterValidation:
    """Test parameter validation for generated models."""

    def test_range_criterion_validation(self):
        """Test range criterion validation."""
        config = RangeCriterionConfig.model_validate({"min_value": -3, "max_value": 3})
        assert config.min_value == -3
        assert config.max_value == 3

    def test_extra_field_not_allowed_in_range_criterion_validation(self):
        """Test extra field not allowed in range criterion validation."""
        with pytest.raises(ValidationError) as exc_info:
            RangeCriterionConfig.model_validate(
                {"min_value": 2, "max_value": 4, "extra_field": 123}
            )
        error_str = str(exc_info.value)
        print("\nerror_str:", error_str)
        assert "Extra inputs are not permitted" in error_str
        assert "extra_field" in error_str
        assert "min_value" not in error_str  # min_value itself is valid
        assert "max_value" not in error_str  # max_value itself is valid

    def test_threshold_criterion_validation(self):
        """Test threshold criterion validation."""
        # Valid case
        config = ThresholdCriterionConfig.model_validate(
            {"above": True, "threshold": 3}
        )
        assert config.above is True
        assert config.threshold == 3

    def test_extra_field_not_allowed_in_threshold_criterion_validation(self):
        """Test extra field not allowed in threshold criterion validation."""
        with pytest.raises(ValidationError) as exc_info:
            ThresholdCriterionConfig.model_validate(
                {"above": False, "threshold": -3, "extra_field": 123}
            )
        error_str = str(exc_info.value)
        print("\nerror_str:", error_str)
        assert "Extra inputs are not permitted" in error_str
        assert "extra_field" in error_str
        assert "above" not in error_str  # above itself is valid
        assert "threshold" not in error_str  # threshold itself is valid


class TestTelescopeParameterValidation:
    """Test telescope parameter validation for generated models."""

    @pytest.mark.parametrize(
        ("selector_type", "selector_value", "numeric_value"),
        [
            # Valid "type" patterns - any string is acceptable now
            ("type", "*", 0.0),
            ("type", "LST_001", 1.0),
            ("type", "MST_FlashCam_001", 2.0),
            ("type", "SST_ASTRI_001", 3.0),
            ("type", "custom_telescope", 4.0),  # Any custom string
            ("type", "INVALID_PATTERN", 5.0),  # Previously invalid patterns now valid
            ("type", "lst_001", 6.0),  # lowercase is valid
            ("type", "XST_001", 7.0),  # Any prefix is valid
            ("type", "LST", 8.0),  # Short names are valid
            ("type", "", 9.0),  # Even empty string is valid
            # Valid "ID" patterns
            ("id", 1, 4.0),
            ("id", 42, 5.0),
            ("id", 999, 6.0),
            # Different numeric types
            ("type", "*", 1),  # int as numeric value
            ("id", 1, 0.5),  # float as numeric value
        ],
    )
    def test_valid_telescope_parameters(
        self, selector_type, selector_value, numeric_value
    ):
        """Test that valid telescope parameters pass validation."""
        config = TelescopeRangeCriterionConfig.model_validate(
            {
                "min_value": [(selector_type, selector_value, numeric_value)],
                "max_value": [("type", "*", 10.0)],
            }
        )
        assert config.min_value[0] == (selector_type, selector_value, numeric_value)

    @pytest.mark.parametrize(
        ("selector_type", "expected_error"),
        [
            ("invalid", "first element must be 'type' or 'id'"),
            ("TYPE", "first element must be 'type' or 'id'"),
            ("Id", "first element must be 'type' or 'id'"),
            ("", "first element must be 'type' or 'id'"),
            (None, "first element must be 'type' or 'id'"),
        ],
    )
    def test_invalid_selector_type_enum(self, selector_type, expected_error):
        """Test that invalid selector types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TelescopeRangeCriterionConfig.model_validate(
                {
                    "min_value": [(selector_type, "test", 0.0)],
                    "max_value": [("type", "*", 10.0)],
                }
            )
        # Either our custom message or Pydantic's built-in validation error
        error_str = str(exc_info.value)
        assert (
            expected_error in error_str
            or "Input should be a valid string" in error_str
            or "Input should be 'type' or 'id'" in error_str
        )

    @pytest.mark.parametrize(
        ("selector_value", "expected_error"),
        [
            # Invalid type patterns - only non-string values should fail
            (
                42,
                "selector value must be string when selector_type='type'",
            ),  # wrong type
            (None, "selector value must be string when selector_type='type'"),  # None
            ([], "selector value must be string when selector_type='type'"),  # list
        ],
    )
    def test_invalid_type_selector_values(self, selector_value, expected_error):
        """Test that invalid type selector values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TelescopeRangeCriterionConfig.model_validate(
                {
                    "min_value": [("type", selector_value, 0.0)],
                    "max_value": [("type", "*", 10.0)],
                }
            )
        # Either our custom message or Pydantic's built-in validation error
        error_str = str(exc_info.value)
        assert (
            expected_error in error_str
            or "Input should be a valid string" in error_str
            or "Input should be a valid integer" in error_str
        )

    @pytest.mark.parametrize(
        ("selector_value", "expected_error"),
        [
            # Invalid ID values
            (0, "selector value must be positive integer when selector_type='id'"),
            (-1, "selector value must be positive integer when selector_type='id'"),
            (-42, "selector value must be positive integer when selector_type='id'"),
            (
                "string",
                "selector value must be positive integer when selector_type='id'",
            ),
            (1.5, "selector value must be positive integer when selector_type='id'"),
            (None, "selector value must be positive integer when selector_type='id'"),
        ],
    )
    def test_invalid_id_selector_values(self, selector_value, expected_error):
        """Test that invalid ID selector values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TelescopeRangeCriterionConfig.model_validate(
                {
                    "min_value": [("id", selector_value, 0.0)],
                    "max_value": [("type", "*", 10.0)],
                }
            )
        # Either our custom message or Pydantic's built-in validation error
        error_str = str(exc_info.value)
        assert (
            expected_error in error_str
            or "Input should be a valid string" in error_str
            or "Input should be a valid integer" in error_str in error_str
        )

    @pytest.mark.parametrize(
        ("numeric_value", "expected_error"),
        [
            ("string", "third element must be numeric"),
            (None, "third element must be numeric"),
            (complex(1, 2), "third element must be numeric"),
        ],
    )
    def test_invalid_numeric_values(self, numeric_value, expected_error):
        """Test that invalid numeric values are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TelescopeRangeCriterionConfig.model_validate(
                {
                    "min_value": [("type", "*", numeric_value)],
                    "max_value": [("type", "*", 10.0)],
                }
            )
        # Either our custom message or Pydantic's built-in validation error
        error_str = str(exc_info.value)
        assert (
            expected_error in error_str or "Input should be a valid number" in error_str
        )

    def test_string_numeric_valid(self):
        """Test that string numerics are accepted by Pydantic."""
        # Pydantic accepts string representations of numbers
        config = TelescopeRangeCriterionConfig.model_validate(
            {"min_value": [("type", "*", "1.5")], "max_value": [("type", "*", 10.0)]}
        )
        assert isclose(config.min_value[0][2], 1.5, abs_tol=1e-9)  # Converted to float

    @pytest.mark.parametrize(
        "invalid_list",
        [
            12,
            "not_a_list",
            None,
        ],
    )
    def test_telescope_parameter_must_be_a_list(self, invalid_list):
        """Test that telescope parameter must be a list."""
        with pytest.raises(ValidationError) as exc_info:
            TelescopeRangeCriterionConfig.model_validate(
                {"min_value": invalid_list, "max_value": [("type", "*", 10.0)]}
            )
        # Either our custom message or Pydantic's built-in validation error
        error_str = str(exc_info.value)
        print("\nerror_str:", error_str)

        assert (
            "telescope parameter items must be length-3" in error_str
            or "Input should be a valid list" in error_str
        )

    @pytest.mark.parametrize(
        "invalid_tuple",
        [
            ("type", "*"),  # Too short
            ("type", "*", 1.0, "extra"),  # Too long
            ("type",),  # Way too short
            (),  # Empty
        ],
    )
    def test_invalid_tuple_length(self, invalid_tuple):
        """Test that tuples with wrong length are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            TelescopeRangeCriterionConfig.model_validate(
                {"min_value": [invalid_tuple], "max_value": [("type", "*", 10.0)]}
            )
        # Either our custom message or Pydantic's built-in validation error
        error_str = str(exc_info.value)
        assert (
            "telescope parameter items must be length-3" in error_str
            or "Field required" in error_str
            or "Tuple should have at most 3 items" in error_str
        )

    def test_multiple_valid_telescope_parameters(self):
        """Test validation with multiple telescope parameters in one list."""
        config = TelescopeRangeCriterionConfig.model_validate(
            {
                "min_value": [
                    ("type", "*", 0.0),
                    ("type", "LST_001", 1.0),
                    ("id", 42, 2.0),
                ],
                "max_value": [
                    ("type", "MST_FlashCam_001", 10.0),
                    ("id", 100, 20.0),
                ],
            }
        )
        assert len(config.min_value) == 3
        assert len(config.max_value) == 2

    def test_mixed_valid_invalid_parameters(self):
        """Test that one invalid parameter in a list fails the whole validation."""
        with pytest.raises(ValidationError):
            TelescopeRangeCriterionConfig.model_validate(
                {
                    "min_value": [
                        ("type", "*", 0.0),  # Valid
                        ("invalid", "test", 1.0),  # Invalid
                    ],
                    "max_value": [("type", "*", 10.0)],
                }
            )

    def test_telescope_threshold_criterion_validation(self):
        """Test that telescope threshold criterion has same validation."""
        # Valid case
        config = TelescopeThresholdCriterionConfig.model_validate(
            {"above": True, "threshold": [("type", "LST_001", 5.0)]}
        )
        assert config.above is True
        assert config.threshold[0] == ("type", "LST_001", 5.0)

        # Invalid case
        with pytest.raises(ValidationError) as exc_info:
            TelescopeThresholdCriterionConfig.model_validate(
                {"above": False, "threshold": [("invalid", "test", 0.0)]}
            )
        # Either our custom message or Pydantic's built-in validation error
        error_str = str(exc_info.value)

        assert (
            "first element must be 'type' or 'id'" in error_str
            or "Input should be 'type' or 'id'" in error_str
        )


class TestCriteriaReportValidation:
    """Test the overall criteria report validation."""

    def test_single_criterion_validation(self):
        """Test that exactly one criterion is required."""
        # Valid: exactly one criterion
        report = CriteriaReport.model_validate(
            {
                "TelescopeRangeCriterion": {
                    "result": True,
                    "config": {
                        "min_value": [("type", "*", 0.0)],
                        "max_value": [("type", "*", 10.0)],
                    },
                }
            }
        )
        assert report.TelescopeRangeCriterion is not None
        assert report.TelescopeThresholdCriterion is None

    def test_multiple_criteria_rejected(self):
        """Test that multiple criteria in one report are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CriteriaReport.model_validate(
                {
                    "TelescopeRangeCriterion": {
                        "result": True,
                        "config": {
                            "min_value": [("type", "*", 0.0)],
                            "max_value": [("type", "*", 10.0)],
                        },
                    },
                    "TelescopeThresholdCriterion": {
                        "result": False,
                        "config": {"above": True, "threshold": [("id", 1, 5.0)]},
                    },
                }
            )
        assert "exactly one criterion entry" in str(exc_info.value)

    def test_no_criteria_rejected(self):
        """Test that empty criteria report is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            CriteriaReport.model_validate({})
        assert "exactly one criterion entry" in str(exc_info.value)


class TestSchemaCompatibility:
    """Test compatibility with the original schema specification."""

    def test_telescope_range_criterion_structure(self):
        """Test that the generated model matches expected structure."""
        config = TelescopeRangeCriterionConfig.model_validate(
            {"min_value": [("type", "*", 0.0)], "max_value": [("id", 42, 10.0)]}
        )

        # Verify structure matches schema expectations
        assert hasattr(config, "min_value")
        assert hasattr(config, "max_value")
        assert isinstance(config.min_value, list)
        assert isinstance(config.max_value, list)

        # Verify tuple structure
        min_tuple = config.min_value[0]
        max_tuple = config.max_value[0]
        assert len(min_tuple) == 3
        assert len(max_tuple) == 3
        assert min_tuple[0] in ("type", "id")
        assert max_tuple[0] in ("type", "id")

    def test_edge_case_telescope_patterns(self):
        """Test edge cases for telescope type patterns."""
        # Any string is now valid for type selectors
        valid_patterns = [
            "LST_",  # Minimum valid LST pattern
            "MST_",  # Minimum valid MST pattern
            "SST_",  # Minimum valid SST pattern
            "LST_NectarCam_001",  # Longer realistic pattern
            "custom_type",  # Any custom string
            "123",  # Numeric string
            "telescope-1",  # With dashes
            "tel.scope_001",  # With dots and underscores
            "",  # Even empty string
        ]

        for pattern in valid_patterns:
            config = TelescopeRangeCriterionConfig.model_validate(
                {
                    "min_value": [("type", pattern, 1.0)],
                    "max_value": [("type", "*", 10.0)],
                }
            )
            assert config.min_value[0][1] == pattern
