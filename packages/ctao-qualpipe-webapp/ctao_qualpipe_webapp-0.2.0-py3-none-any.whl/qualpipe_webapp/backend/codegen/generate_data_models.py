"""Generate Pydantic models and JSON Schemas for criteria discovered in an external package.

Generate Pydantic models for criteria discovered in an external package
and write JSON/YAML schemas suitable for the frontend static folder.

Usage (from repo root, in env where qualpipe is importable):
python -m qualpipe_webapp.backend.codegen.generate_data_models \
    --module qualpipe.core.criterion \
    --out-generated src/qualpipe_webapp/backend/generated \
    --out-schemas src/qualpipe_webapp/frontend/static
"""

from __future__ import annotations

import importlib
import inspect
import json
import os
import textwrap

import traitlets
import yaml

# Basic traitlets -> python type strings
TRAITLET_MAP = {
    "Float": "float",
    "Int": "int",
    "Bool": "bool",
    "Unicode": "str",
    "List": "list",
    "Tuple": "tuple",
    "Dict": "dict",
    "Instance": "Any",
}


def trait_to_hint(tr: traitlets.TraitType) -> str:
    """Map traitlets TraitType instance to a python type hint string."""
    clsname = tr.__class__.__name__
    return TRAITLET_MAP.get(clsname, "Any")


def class_traits(cls: type) -> dict[str, traitlets.TraitType]:
    """Return traitlets declared on cls (supports Configurable/HasTraits)."""
    if hasattr(cls, "class_traits"):
        return cls.class_traits()
    # fallback to creating an instance
    try:
        inst = cls()
        return inst.traits()
    except Exception:
        return {}


def is_telescope_parameter(tr: traitlets.TraitType) -> bool:
    """Detect a TelescopeParameter-like trait by class name fallback."""
    return "telescope" in tr.__class__.__name__.lower()


def write_generated_models(module_name: str, out_dir: str) -> str:
    """Inspect module for criteria classes and write a generated pydantic module.

    Returns path to written file.
    """
    mod = importlib.import_module(module_name)
    os.makedirs(out_dir, exist_ok=True)

    # Generate filename from module name: "qualpipe.core.criterion" -> "qualpipe_criterion_model.py"
    module_parts = module_name.split(".")
    # Use relevant parts: first part + last part (e.g., "qualpipe" + "criterion")
    if len(module_parts) >= 2:
        filename = f"{module_parts[0]}_{module_parts[-1]}_model.py"
    else:
        filename = f"{module_parts[0]}_model.py"
    out_path = os.path.join(out_dir, filename)

    header = textwrap.dedent(
        """\
        # Auto-generated from traitlets-based criteria. Do not edit.
        from pydantic import BaseModel, field_validator, model_validator, Field, ConfigDict
        from typing import Literal, Union, Annotated, List, Tuple

        # Type alias for telescope parameter tuples
        TelescopeParameterTuple = Tuple[Literal['type', 'id'], Union[str, int], float]
        """
    )

    models: list[str] = []
    found_names: list[str] = []

    # Discover classes that look like Criteria (heuristic: contain "Criterion" in name)
    for name, obj in inspect.getmembers(mod, inspect.isclass):
        if "Criterion" not in name:
            continue
        # skip abstract bases
        if getattr(obj, "__abstractmethods__", False):
            continue
        traits = class_traits(obj)
        # Build config model for this criterion
        cfg_fields: list[str] = []
        validators: list[str] = []
        for tname, tr in traits.items():
            if tname.startswith("_"):
                continue
            # Skip internal traitlets configuration traits
            if tname in ("config", "parent", "log"):
                continue
            if is_telescope_parameter(tr):
                # represent telescope parameter using a type alias with enum constraint
                # First field: enum("type", "id")
                # Second field: depends on first (str for "type", int for "id")
                # Third field: float value
                hint = "List[TelescopeParameterTuple]"
                cfg_fields.append(
                    f"    {tname}: {hint} = Field(..., description='List of telescope parameters with format [selector_type, selector_value, numeric_value]')"
                )
                # add validator to ensure tuple shape and enum constraints
                v = textwrap.dedent(
                    f"""
                    @field_validator('{tname}')
                    @classmethod
                    def _validate_{tname}(cls, v):
                        if not isinstance(v, list):
                            raise ValueError("telescope parameter must be a list")

                        for item in v:
                            if not (isinstance(item, (list, tuple)) and len(item) == 3):
                                raise ValueError("telescope parameter items must be length-3 [selector_type, selector, value]")

                            selector_type, selector_value, numeric_value = item

                            # First field must be enum: "type" or "id"
                            if selector_type not in ('type', 'id'):
                                raise ValueError("first element must be 'type' or 'id'")

                            # Second field validation depends on first field
                            if selector_type == 'type':
                                # For type: any string value
                                if not isinstance(selector_value, str):
                                    raise ValueError("selector value must be string when selector_type='type'")
                            elif selector_type == 'id':
                                # For id: positive integer
                                if not isinstance(selector_value, int) or selector_value < 1:
                                    raise ValueError("selector value must be positive integer when selector_type='id'")

                            # Third field must be numeric
                            if not isinstance(numeric_value, (int, float)):
                                raise ValueError("third element must be numeric")

                        return v
                    """
                )
                validators.append(v.rstrip())
            else:
                hint = trait_to_hint(tr)
                # detect required/default - skip traits with Undefined defaults
                default = getattr(tr, "default_value", None)
                if default is None or str(default) == "traitlets.Undefined":
                    cfg_fields.append(f"    {tname}: {hint}")
                else:
                    cfg_fields.append(f"    {tname}: {hint} = {repr(default)}")
        cfg_name = f"{name}Config"
        found_names.append((name, cfg_name))
        model_src = f"class {cfg_name}(BaseModel):\n"
        if cfg_fields:
            model_src += "\n".join(cfg_fields) + "\n"
        else:
            model_src += "    pass\n"
        model_src += "\n    model_config = ConfigDict(extra='forbid')\n"
        if validators:
            # Add validators inside the class with proper indentation
            model_src += (
                "\n"
                + "\n".join(
                    [
                        "\n".join(
                            f"    {line}" if line.strip() else ""
                            for line in validator.split("\n")
                        )
                        for validator in validators
                    ]
                )
                + "\n"
            )
        models.append(model_src)

        # wrapper that contains result + config
        wrapper_src = textwrap.dedent(
            f"""
            class {name}Record(BaseModel):
                result: bool
                config: {cfg_name}
            """
        )
        models.append(wrapper_src.strip())

    # Compose CriteriaReport model: allow exactly one criterion property (enforce in root_validator)
    if found_names:
        criteria_props = "\n".join(
            [f"    {cname}: {cname}Record | None = None" for (cname, _) in found_names]
        )
        criteria_model = f"""class CriteriaReport(BaseModel):
{criteria_props}

    @model_validator(mode='before')
    @classmethod
    def _exactly_one(cls, values):
        present = [k for k,v in values.items() if v is not None]
        if len(present) != 1:
            raise ValueError("criteria report must contain exactly one criterion entry")
        return values"""
    else:
        criteria_model = """class CriteriaReport(BaseModel):
    pass"""
    # Metadata wrapper (only include criteriaReport here; plotMeta handled elsewhere)
    metadata_model = textwrap.dedent(
        """
        class FetchedMetadata(BaseModel):
            criteriaReport: CriteriaReport

        class MetadataPayload(BaseModel):
            fetchedMetadata: FetchedMetadata
        """
    )

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(header + "\n\n")
        for m in models:
            fh.write(m.rstrip() + "\n\n\n")
        fh.write(criteria_model.rstrip() + "\n\n\n")
        fh.write(metadata_model)
    return out_path


def export_schemas_from_generated(generated_module_path: str, out_dir: str) -> None:
    """Import generated module and write JSON/YAML schemas for MetadataPayload and CriteriaReport."""
    # make module importable
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "qualpipe_generated_metadata", generated_module_path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore

    os.makedirs(out_dir, exist_ok=True)

    # Rebuild all models in dependency order to resolve forward references
    try:
        # Rebuild in order: CriteriaReport -> FetchedMetadata -> MetadataPayload
        criteria_report = getattr(mod, "CriteriaReport")
        fetched_metadata = getattr(mod, "FetchedMetadata")
        metadata_payload = getattr(mod, "MetadataPayload")

        criteria_report.model_rebuild()
        fetched_metadata.model_rebuild()
        metadata_payload.model_rebuild()
    except Exception as e:
        print(f"Warning: Could not rebuild models: {e}")

    # pick models to export - just export the CriteriaReport for now
    to_export = {
        "criteria_schema": getattr(mod, "CriteriaReport"),
    }

    for name, model in to_export.items():
        # pydantic v2/v1 compatibility
        schema_obj = None
        if hasattr(model, "model_json_schema"):
            schema_obj = model.model_json_schema()
        elif hasattr(model, "schema"):
            schema_obj = model.schema()
        else:
            raise RuntimeError("Unsupported pydantic version")
        # write JSON
        json_path = os.path.join(out_dir, f"{name}.json")
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(schema_obj, fh, indent=2)
        # write YAML
        yaml_path = os.path.join(out_dir, f"{name}.yaml")
        with open(yaml_path, "w", encoding="utf-8") as fh:
            yaml.safe_dump(schema_obj, fh, sort_keys=False)


def main():
    """Generate Pydantic models and JSON Schemas for criteria discovered in an external package."""
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument(
        "--module", required=True, help="module to scan for Criterion classes"
    )
    p.add_argument("--out-generated", default="src/qualpipe_webapp/backend/generated")
    p.add_argument("--out-schemas", default="src/qualpipe_webapp/frontend/static")
    args = p.parse_args()

    gen_path = write_generated_models(args.module, args.out_generated)
    print("Wrote generated models to", gen_path)
    export_schemas_from_generated(gen_path, args.out_schemas)
    print("Wrote JSON/YAML schemas to", args.out_schemas)


if __name__ == "__main__":
    main()
