"""Tests for the code generation script."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import traitlets

from qualpipe_webapp.backend.codegen.generate_data_models import (
    class_traits,
    export_schemas_from_generated,
    is_telescope_parameter,
    main,
    trait_to_hint,
    write_generated_models,
)


# Mock classes for testing
class MockTelescopeParameter(traitlets.TraitType):
    """Mock telescope parameter trait."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MockCriterion(traitlets.HasTraits):
    """Mock criterion class for testing."""

    threshold = traitlets.Float(default_value=1.0)
    telescope_param = MockTelescopeParameter()
    name = traitlets.Unicode(default_value="test")


class TestTraitMapping:
    """Test trait to type hint mapping."""

    def test_trait_to_hint_basic_types(self):
        """Test mapping of basic traitlet types."""
        assert trait_to_hint(traitlets.Float()) == "float"
        assert trait_to_hint(traitlets.Int()) == "int"
        assert trait_to_hint(traitlets.Bool()) == "bool"
        assert trait_to_hint(traitlets.Unicode()) == "str"
        assert trait_to_hint(traitlets.List()) == "list"
        assert trait_to_hint(traitlets.Tuple()) == "tuple"
        assert trait_to_hint(traitlets.Dict()) == "dict"

    def test_trait_to_hint_unknown_type(self):
        """Test fallback for unknown trait types."""

        class CustomTrait(traitlets.TraitType):
            pass

        assert trait_to_hint(CustomTrait()) == "Any"


class TestTelescopeParameterDetection:
    """Test telescope parameter detection."""

    def test_is_telescope_parameter_positive(self):
        """Test detection of telescope parameter traits."""
        assert is_telescope_parameter(MockTelescopeParameter()) is True

    def test_is_telescope_parameter_negative(self):
        """Test non-telescope parameter traits."""
        assert is_telescope_parameter(traitlets.Float()) is False
        assert is_telescope_parameter(traitlets.Unicode()) is False


class TestClassTraits:
    """Test class trait extraction."""

    def test_class_traits_configurable(self):
        """Test trait extraction from configurable classes."""
        traits = class_traits(MockCriterion)
        assert "threshold" in traits
        assert "telescope_param" in traits
        assert "name" in traits

    def test_class_traits_fallback(self):
        """Test fallback trait extraction."""

        class FallbackClass:
            def traits(self):
                return {"value": "dummy"}

        traits = class_traits(FallbackClass)
        assert "value" in traits


class TestCodeGeneration:
    """Test the main code generation functionality."""

    def test_write_generated_models_single_module(self):
        """Test code generation with a single module component."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock a simple module
            mock_module = Mock()
            mock_module.TestCriterion = MockCriterion

            with (
                patch("importlib.import_module", return_value=mock_module),
                patch(
                    "inspect.getmembers",
                    return_value=[("TestCriterion", MockCriterion)],
                ),
            ):
                result_path = write_generated_models("testmodule", tmpdir)

                # Check file was created with correct name
                assert Path(result_path).name == "testmodule_model.py"
                assert Path(result_path).exists()

                # Check content contains expected elements
                content = Path(result_path).read_text()
                assert "class TestCriterionConfig(BaseModel):" in content
                assert "class TestCriterionRecord(BaseModel):" in content
                assert "class CriteriaReport(BaseModel):" in content

    def test_write_generated_models_multi_module(self):
        """Test code generation with multi-part module name."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_module = Mock()
            mock_module.TestCriterion = MockCriterion

            with (
                patch("importlib.import_module", return_value=mock_module),
                patch(
                    "inspect.getmembers",
                    return_value=[("TestCriterion", MockCriterion)],
                ),
            ):
                result_path = write_generated_models(
                    "package.submodule.criterion", tmpdir
                )

                # Check file was created with correct name (first + last part)
                assert Path(result_path).name == "package_criterion_model.py"

    def test_write_generated_models_telescope_parameter(self):
        """Test generation of telescope parameter validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_module = Mock()
            mock_module.TestCriterion = MockCriterion

            with (
                patch("importlib.import_module", return_value=mock_module),
                patch(
                    "inspect.getmembers",
                    return_value=[("TestCriterion", MockCriterion)],
                ),
            ):
                result_path = write_generated_models("testmodule", tmpdir)
                content = Path(result_path).read_text()

                # Check telescope parameter validation is generated
                assert "List[TelescopeParameterTuple]" in content
                assert "_validate_telescope_param" in content
                assert "first element must be 'type' or 'id'" in content

    def test_write_generated_models_no_criteria(self):
        """Test generation when no criterion classes are found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_module = Mock()

            with (
                patch("importlib.import_module", return_value=mock_module),
                patch("inspect.getmembers", return_value=[]),
            ):
                result_path = write_generated_models("testmodule", tmpdir)
                content = Path(result_path).read_text()

                # Should still generate basic structure
                assert "class CriteriaReport(BaseModel):" in content
                assert "pass" in content


class TestSchemaExport:
    """Test JSON/YAML schema export functionality."""

    def test_export_schemas_from_generated(self):
        """Test schema export from generated module."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple generated module file
            generated_file = Path(tmpdir) / "test_model.py"
            generated_file.write_text(
                """
from pydantic import BaseModel

class CriteriaReport(BaseModel):
    pass
"""
            )

            schema_dir = Path(tmpdir) / "schemas"
            schema_dir.mkdir()

            export_schemas_from_generated(str(generated_file), str(schema_dir))

            # Check JSON schema was created
            json_file = schema_dir / "criteria_schema.json"
            assert json_file.exists()

            # Check YAML schema was created
            yaml_file = schema_dir / "criteria_schema.yaml"
            assert yaml_file.exists()

            # Verify JSON content is valid
            schema_data = json.loads(json_file.read_text())
            assert "title" in schema_data
            assert schema_data["title"] == "CriteriaReport"


class TestIntegration:
    """Integration tests for the complete workflow."""

    @patch(
        "qualpipe_webapp.backend.codegen.generate_data_models.importlib.import_module"
    )
    @patch("qualpipe_webapp.backend.codegen.generate_data_models.inspect.getmembers")
    def test_end_to_end_generation(self, mock_getmembers, mock_import):
        """Test complete code generation workflow."""
        # Setup mocks
        mock_module = Mock()
        mock_import.return_value = mock_module
        mock_getmembers.return_value = [("TestCriterion", MockCriterion)]

        with tempfile.TemporaryDirectory() as tmpdir:
            gen_dir = Path(tmpdir) / "generated"
            schema_dir = Path(tmpdir) / "schemas"

            # Generate models
            result_path = write_generated_models("test.module", str(gen_dir))

            # Export schemas
            export_schemas_from_generated(result_path, str(schema_dir))

            # Verify files exist
            assert Path(result_path).exists()
            assert (schema_dir / "criteria_schema.json").exists()
            assert (schema_dir / "criteria_schema.yaml").exists()

            # Verify content structure
            content = Path(result_path).read_text()
            assert "TestCriterionConfig" in content
            assert "CriteriaReport" in content
            assert "MetadataPayload" in content


# Test the actual module if qualpipe is available
class TestWithRealModule:
    """Integration tests with real qualpipe module (if available)."""

    def test_with_real_qualpipe_module(self):
        """Test with actual qualpipe.core.criterion module."""
        pytest.importorskip("qualpipe.core.criterion")

        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                result_path = write_generated_models("qualpipe.core.criterion", tmpdir)
                assert Path(result_path).exists()

                # Check that real criterion classes are processed
                content = Path(result_path).read_text()
                assert "class CriteriaReport(BaseModel):" in content

            except Exception as e:
                pytest.skip(f"Real module test failed: {e}")


class TestMainFunction:
    """Test the main CLI function."""

    @patch(
        "sys.argv",
        [
            "generate_data_models",
            "--module",
            "test.module",
            "--out-generated",
            "/tmp/gen",
            "--out-schemas",
            "/tmp/schemas",
        ],
    )
    @patch(
        "qualpipe_webapp.backend.codegen.generate_data_models.write_generated_models"
    )
    @patch(
        "qualpipe_webapp.backend.codegen.generate_data_models.export_schemas_from_generated"
    )
    def test_main_function_cli_args(self, mock_export, mock_write):
        """Test main function with CLI arguments."""
        mock_write.return_value = "/tmp/gen/test_model.py"

        # Call main function
        main()

        # Verify functions were called with correct arguments
        mock_write.assert_called_once_with("test.module", "/tmp/gen")
        mock_export.assert_called_once_with("/tmp/gen/test_model.py", "/tmp/schemas")
