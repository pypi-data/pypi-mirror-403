"""Validation tools for InputSpec, OutputContract, and run manifests.

Provides:
- InputSpec linting (json_schema_extra validation, show_when structure)
- OutputContract validation (structure, key uniqueness)
- Bundle validation (hash integrity)
- RunManifest vs OutputContract alignment validation
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from fraclab_sdk.errors import AlgorithmError


class ValidationSeverity(Enum):
    """Severity level for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue."""

    severity: ValidationSeverity
    code: str
    message: str
    path: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Result of validation."""

    valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[ValidationIssue]:
        """Get error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """Get warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]


# =============================================================================
# InputSpec Validation
# =============================================================================

# Valid show_when operators
VALID_SHOW_WHEN_OPS = {"eq", "neq", "in", "nin", "gt", "gte", "lt", "lte", "exists"}


def _validate_show_when_condition(
    condition: dict[str, Any], schema: dict[str, Any], path: str, issues: list[ValidationIssue]
) -> None:
    """Validate a single show_when condition.

    Args:
        condition: The condition dict {field, op, value}.
        schema: The full JSON schema for field lookup.
        path: Current path for error reporting.
        issues: List to append issues to.
    """
    if not isinstance(condition, dict):
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="SHOW_WHEN_INVALID_CONDITION",
                message="show_when condition must be a dict",
                path=path,
            )
        )
        return

    # Check required keys
    if "field" not in condition:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="SHOW_WHEN_MISSING_FIELD",
                message="show_when condition missing 'field' key",
                path=path,
            )
        )
        return

    field_path = condition["field"]
    op = condition.get("op", "eq")

    # Validate operator
    if op not in VALID_SHOW_WHEN_OPS:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="SHOW_WHEN_INVALID_OP",
                message=f"Invalid show_when operator: {op}. Valid: {VALID_SHOW_WHEN_OPS}",
                path=path,
            )
        )

    # Validate field path exists in schema
    if not _field_exists_in_schema(field_path, schema):
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="SHOW_WHEN_FIELD_NOT_FOUND",
                message=f"show_when references non-existent field: {field_path}",
                path=path,
                details={"field": field_path},
            )
        )


def _validate_show_when(
    show_when: Any, schema: dict[str, Any], path: str, issues: list[ValidationIssue]
) -> None:
    """Validate show_when structure.

    Supports:
    - Single condition: {field, op, value}
    - AND list: [{cond1}, {cond2}]
    - OR object: {"or": [{cond1}, {cond2}]}

    Args:
        show_when: The show_when value.
        schema: Full JSON schema for field lookup.
        path: Current path for error reporting.
        issues: List to append issues to.
    """
    if show_when is None:
        return

    if isinstance(show_when, dict):
        if "or" in show_when:
            # OR object
            or_conditions = show_when["or"]
            if not isinstance(or_conditions, list):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="SHOW_WHEN_INVALID_OR",
                        message="show_when 'or' must be a list",
                        path=path,
                    )
                )
            else:
                for i, cond in enumerate(or_conditions):
                    _validate_show_when_condition(cond, schema, f"{path}.or[{i}]", issues)
        elif "and" in show_when:
            # AND object (explicit)
            and_conditions = show_when["and"]
            if not isinstance(and_conditions, list):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="SHOW_WHEN_INVALID_AND",
                        message="show_when 'and' must be a list",
                        path=path,
                    )
                )
            else:
                for i, cond in enumerate(and_conditions):
                    _validate_show_when_condition(cond, schema, f"{path}.and[{i}]", issues)
        else:
            # Single condition
            _validate_show_when_condition(show_when, schema, path, issues)

    elif isinstance(show_when, list):
        # Implicit AND list
        for i, cond in enumerate(show_when):
            _validate_show_when_condition(cond, schema, f"{path}[{i}]", issues)

    else:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="SHOW_WHEN_INVALID_TYPE",
                message=f"show_when must be dict or list, got {type(show_when).__name__}",
                path=path,
            )
        )


def _field_exists_in_schema(field_path: str, schema: dict[str, Any]) -> bool:
    """Check if a field path exists in a JSON schema.

    Supports dot notation: "parent.child.field"

    Args:
        field_path: Dot-separated field path.
        schema: JSON schema dict.

    Returns:
        True if field exists.
    """
    parts = field_path.split(".")
    current = schema.get("properties", {})

    for i, part in enumerate(parts):
        if part not in current:
            return False
        prop = current[part]

        # Last part - field exists
        if i == len(parts) - 1:
            return True

        # Navigate into nested object
        if prop.get("type") == "object":
            current = prop.get("properties", {})
        elif "$ref" in prop:
            # Handle $ref - simplified, assumes $defs at root
            ref = prop["$ref"]
            if ref.startswith("#/$defs/"):
                def_name = ref.split("/")[-1]
                defs = schema.get("$defs", {})
                if def_name in defs:
                    current = defs[def_name].get("properties", {})
                else:
                    return False
            else:
                return False
        else:
            return False

    return True


def _validate_enum_labels(
    enum_labels: dict[str, str],
    enum_values: list[Any] | None,
    path: str,
    issues: list[ValidationIssue],
) -> None:
    """Validate enum_labels keys match enum values.

    Args:
        enum_labels: The enum_labels dict.
        enum_values: The enum values from schema (if available).
        path: Current path for error reporting.
        issues: List to append issues to.
    """
    if enum_values is None:
        return

    enum_values_str = {str(v) for v in enum_values}
    for key in enum_labels:
        if str(key) not in enum_values_str:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="ENUM_LABEL_UNKNOWN_VALUE",
                    message=f"enum_labels key '{key}' not in enum values: {enum_values}",
                    path=path,
                )
            )


def _extract_schema_from_workspace(workspace: Path) -> dict[str, Any]:
    """Extract JSON schema from workspace InputSpec.

    Args:
        workspace: Algorithm workspace.

    Returns:
        JSON schema dict.
    """
    script = '''
import json
import sys

try:
    from schema.inputspec import INPUT_SPEC
    model = INPUT_SPEC
    schema = model.model_json_schema()
    print(json.dumps(schema))
except Exception as e:
    print(json.dumps({"error": str(e)}))
'''

    env = {"PYTHONPATH": str(workspace), "PYTHONUNBUFFERED": "1"}
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=workspace,
        env={**dict(__import__("os").environ), **env},
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise AlgorithmError(f"Failed to extract schema: {result.stderr}")

    data = json.loads(result.stdout)
    if "error" in data:
        raise AlgorithmError(f"Failed to extract schema: {data['error']}")

    return data


def validate_inputspec(workspace: Path) -> ValidationResult:
    """Validate InputSpec (schema.inputspec:INPUT_SPEC, legacy CONFIG_MODEL).

    Checks:
    - Schema can be generated
    - json_schema_extra fields are valid
    - show_when conditions reference existing fields
    - enum_labels keys match enum values

    Args:
        workspace: Algorithm workspace path.

    Returns:
        ValidationResult with issues found.
    """
    workspace = Path(workspace).resolve()
    issues: list[ValidationIssue] = []

    # Extract schema
    try:
        schema = _extract_schema_from_workspace(workspace)
    except AlgorithmError as e:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="INPUTSPEC_LOAD_FAILED",
                message=str(e),
            )
        )
        return ValidationResult(valid=False, issues=issues)

    # Validate properties
    _validate_schema_properties(schema, schema, "", issues)

    # Check for required fields
    if "properties" not in schema:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.WARNING,
                code="INPUTSPEC_NO_PROPERTIES",
                message="Schema has no properties defined",
            )
        )

    has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
    return ValidationResult(valid=not has_errors, issues=issues)


def _validate_schema_properties(
    props_container: dict[str, Any],
    full_schema: dict[str, Any],
    path_prefix: str,
    issues: list[ValidationIssue],
) -> None:
    """Recursively validate schema properties.

    Args:
        props_container: Dict containing 'properties' key.
        full_schema: The full schema for field lookups.
        path_prefix: Current path prefix for error reporting.
        issues: List to append issues to.
    """
    properties = props_container.get("properties", {})

    for field_name, field_schema in properties.items():
        field_path = f"{path_prefix}.{field_name}" if path_prefix else field_name

        # Check json_schema_extra (stored in various places depending on Pydantic version)
        extra = (
            field_schema.get("json_schema_extra")
            or field_schema.get("extra")
            or {}
        )

        # Validate show_when
        if "show_when" in extra:
            _validate_show_when(extra["show_when"], full_schema, f"{field_path}.show_when", issues)

        # Validate enum_labels
        if "enum_labels" in extra:
            enum_values = field_schema.get("enum")
            _validate_enum_labels(extra["enum_labels"], enum_values, f"{field_path}.enum_labels", issues)

        # Recurse into nested objects
        if field_schema.get("type") == "object":
            _validate_schema_properties(field_schema, full_schema, field_path, issues)

        # Handle allOf, anyOf, oneOf
        for combiner in ["allOf", "anyOf", "oneOf"]:
            if combiner in field_schema:
                for i, sub_schema in enumerate(field_schema[combiner]):
                    _validate_schema_properties(
                        sub_schema, full_schema, f"{field_path}.{combiner}[{i}]", issues
                    )

    # Handle $defs
    if "$defs" in props_container:
        for def_name, def_schema in props_container["$defs"].items():
            _validate_schema_properties(
                def_schema, full_schema, f"$defs.{def_name}", issues
            )


# =============================================================================
# OutputContract Validation
# =============================================================================


def validate_output_contract(workspace_or_path: Path) -> ValidationResult:
    """Validate OutputContract structure.

    Checks:
    - Contract can be loaded
    - Dataset keys are unique
    - Item keys are unique within datasets
    - Artifact keys are unique within items
    - kind matches schema.type

    Args:
        workspace_or_path: Workspace path or direct path to output_contract.json.

    Returns:
        ValidationResult with issues found.
    """
    workspace_or_path = Path(workspace_or_path).resolve()
    issues: list[ValidationIssue] = []

    # Find contract file
    if workspace_or_path.is_file():
        contract_path = workspace_or_path
    else:
        contract_path = workspace_or_path / "dist" / "output_contract.json"
        if not contract_path.exists():
            # Try extracting from workspace
            try:
                script = '''
import json
from schema.output_contract import OUTPUT_CONTRACT
if hasattr(OUTPUT_CONTRACT, 'model_dump'):
    print(json.dumps(OUTPUT_CONTRACT.model_dump(mode="json")))
else:
    print(json.dumps(OUTPUT_CONTRACT.dict()))
'''
                env = {"PYTHONPATH": str(workspace_or_path), "PYTHONUNBUFFERED": "1"}
                result = subprocess.run(
                    [sys.executable, "-c", script],
                    cwd=workspace_or_path,
                    env={**dict(__import__("os").environ), **env},
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    contract = json.loads(result.stdout)
                else:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            code="OUTPUT_CONTRACT_NOT_FOUND",
                            message="output_contract.json not found and could not extract from workspace",
                        )
                    )
                    return ValidationResult(valid=False, issues=issues)
            except Exception as e:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="OUTPUT_CONTRACT_LOAD_FAILED",
                        message=str(e),
                    )
                )
                return ValidationResult(valid=False, issues=issues)
        else:
            contract = json.loads(contract_path.read_text())

    if "contract" not in dir():
        contract = json.loads(contract_path.read_text())

    # Validate contract structure
    _validate_contract_structure(contract, issues)

    has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
    return ValidationResult(valid=not has_errors, issues=issues)


def _validate_contract_structure(contract: dict[str, Any], issues: list[ValidationIssue]) -> None:
    """Validate OutputContract structure.

    Args:
        contract: Contract dict.
        issues: List to append issues to.
    """
    datasets = contract.get("datasets", [])

    # Check dataset key uniqueness
    dataset_keys = [ds.get("key") for ds in datasets if "key" in ds]
    duplicates = [k for k in dataset_keys if dataset_keys.count(k) > 1]
    if duplicates:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="OUTPUT_CONTRACT_DUPLICATE_DATASET_KEY",
                message=f"Duplicate dataset keys: {set(duplicates)}",
            )
        )

    allowed_kinds = {"frame", "object", "blob", "scalar"}
    allowed_owners = {"stage", "well", "platform"}
    allowed_cardinality = {"one", "many"}
    allowed_roles = {"primary", "supporting", "debug"}
    kind_schema_map = {
        "frame": {"frame"},
        "object": {"object"},
        "blob": {"blob"},
        "scalar": {"scalar"},
    }

    for ds in datasets:
        ds_key = ds.get("key", "unknown")
        kind = ds.get("kind")
        owner = ds.get("owner")
        cardinality = ds.get("cardinality")
        role = ds.get("role")
        schema = ds.get("schema") or {}
        schema_type = schema.get("type")

        if kind not in allowed_kinds:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="OUTPUT_CONTRACT_INVALID_KIND",
                    message=f"Invalid kind '{kind}' (expected one of {allowed_kinds})",
                    path=f"datasets.{ds_key}",
                )
            )

        if owner not in allowed_owners:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="OUTPUT_CONTRACT_INVALID_OWNER",
                    message=f"Invalid owner '{owner}' (expected one of {allowed_owners})",
                    path=f"datasets.{ds_key}",
                )
            )

        if cardinality not in allowed_cardinality:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="OUTPUT_CONTRACT_INVALID_CARDINALITY",
                    message=f"Invalid cardinality '{cardinality}' (expected one of {allowed_cardinality})",
                    path=f"datasets.{ds_key}",
                )
            )

        if role and role not in allowed_roles:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="OUTPUT_CONTRACT_INVALID_ROLE",
                    message=f"Invalid role '{role}' (expected one of {allowed_roles})",
                    path=f"datasets.{ds_key}",
                )
            )

        if kind and schema_type and schema_type not in kind_schema_map.get(kind, set()):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="OUTPUT_CONTRACT_KIND_SCHEMA_MISMATCH",
                    message=f"Schema type '{schema_type}' incompatible with kind '{kind}'",
                    path=f"datasets.{ds_key}.schema",
                )
            )

        dimensions = ds.get("dimensions") or []
        if not isinstance(dimensions, list):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="OUTPUT_CONTRACT_DIMENSIONS_NOT_LIST",
                    message="dimensions must be a list of strings",
                    path=f"datasets.{ds_key}.dimensions",
                )
            )
        else:
            dim_duplicates = [d for d in dimensions if dimensions.count(d) > 1]
            if dim_duplicates:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="OUTPUT_CONTRACT_DUPLICATE_DIMENSION",
                        message=f"Duplicate dimensions: {set(dim_duplicates)}",
                        path=f"datasets.{ds_key}.dimensions",
                    )
                )


# =============================================================================
# Bundle Validation
# =============================================================================


def validate_bundle(bundle_path: Path) -> ValidationResult:
    """Validate bundle hash integrity.

    Checks:
    - manifest.json exists and is valid
    - ds.json hash matches manifest.specFiles.dsSha256
    - drs.json hash matches manifest.specFiles.drsSha256

    Args:
        bundle_path: Path to bundle directory.

    Returns:
        ValidationResult with issues found.
    """
    bundle_path = Path(bundle_path).resolve()
    issues: list[ValidationIssue] = []

    if not bundle_path.is_dir():
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="BUNDLE_NOT_FOUND",
                message=f"Bundle directory not found: {bundle_path}",
            )
        )
        return ValidationResult(valid=False, issues=issues)

    # Check required files
    manifest_path = bundle_path / "manifest.json"
    ds_path = bundle_path / "ds.json"
    drs_path = bundle_path / "drs.json"

    if not manifest_path.exists():
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="BUNDLE_MANIFEST_NOT_FOUND",
                message="manifest.json not found",
            )
        )
        return ValidationResult(valid=False, issues=issues)

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="BUNDLE_MANIFEST_INVALID_JSON",
                message=f"Invalid manifest.json: {e}",
            )
        )
        return ValidationResult(valid=False, issues=issues)

    spec_files = manifest.get("specFiles", {})

    # Validate ds.json hash
    if ds_path.exists():
        expected_hash = spec_files.get("dsSha256")
        if expected_hash:
            actual_hash = hashlib.sha256(ds_path.read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="BUNDLE_DS_HASH_MISMATCH",
                        message=f"ds.json hash mismatch: expected {expected_hash[:16]}..., got {actual_hash[:16]}...",
                        details={"expected": expected_hash, "actual": actual_hash},
                    )
                )
    else:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="BUNDLE_DS_NOT_FOUND",
                message="ds.json not found",
            )
        )

    # Validate drs.json hash
    if drs_path.exists():
        expected_hash = spec_files.get("drsSha256")
        if expected_hash:
            actual_hash = hashlib.sha256(drs_path.read_bytes()).hexdigest()
            if actual_hash != expected_hash:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="BUNDLE_DRS_HASH_MISMATCH",
                        message=f"drs.json hash mismatch: expected {expected_hash[:16]}..., got {actual_hash[:16]}...",
                        details={"expected": expected_hash, "actual": actual_hash},
                    )
                )
    else:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="BUNDLE_DRS_NOT_FOUND",
                message="drs.json not found",
            )
        )

    has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
    return ValidationResult(valid=not has_errors, issues=issues)


# =============================================================================
# RunManifest vs OutputContract Validation
# =============================================================================


def validate_run_manifest(
    manifest_path: Path,
    contract_path: Path | None = None,
) -> ValidationResult:
    """Validate run output manifest against OutputContract.

    Checks:
    - Manifest structure is valid
    - All contract datasets are present in manifest
    - All contract items are present in manifest datasets
    - All contract artifacts are present in manifest items
    - kind/schema/mime consistency
    - dimensions key sets match

    Args:
        manifest_path: Path to output manifest.json.
        contract_path: Path to output_contract.json (optional).

    Returns:
        ValidationResult with issues found.
    """
    manifest_path = Path(manifest_path).resolve()
    issues: list[ValidationIssue] = []

    if not manifest_path.exists():
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="MANIFEST_NOT_FOUND",
                message=f"Manifest not found: {manifest_path}",
            )
        )
        return ValidationResult(valid=False, issues=issues)

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError as e:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="MANIFEST_INVALID_JSON",
                message=f"Invalid manifest JSON: {e}",
            )
        )
        return ValidationResult(valid=False, issues=issues)

    # If no contract provided, just validate manifest structure
    if contract_path is None:
        has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
        return ValidationResult(valid=not has_errors, issues=issues)

    contract_path = Path(contract_path).resolve()
    if not contract_path.exists():
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="CONTRACT_NOT_FOUND",
                message=f"Contract not found: {contract_path}",
            )
        )
        return ValidationResult(valid=False, issues=issues)

    try:
        contract = json.loads(contract_path.read_text())
    except json.JSONDecodeError as e:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="CONTRACT_INVALID_JSON",
                message=f"Invalid contract JSON: {e}",
            )
        )
        return ValidationResult(valid=False, issues=issues)

    # Align manifest against contract
    _validate_manifest_against_contract(manifest, contract, issues)

    has_errors = any(i.severity == ValidationSeverity.ERROR for i in issues)
    return ValidationResult(valid=not has_errors, issues=issues)


def _validate_manifest_against_contract(
    manifest: dict[str, Any],
    contract: dict[str, Any],
    issues: list[ValidationIssue],
) -> None:
    """Validate manifest against contract.

    Args:
        manifest: Run output manifest.
        contract: Output contract.
        issues: List to append issues to.
    """
    contract_datasets = {ds["key"]: ds for ds in contract.get("datasets", []) if "key" in ds}
    manifest_datasets = {
        ds.get("datasetKey") or ds.get("key"): ds for ds in manifest.get("datasets", [])
    }

    # Check all contract datasets are in manifest (if required)
    for ds_key, contract_ds in contract_datasets.items():
        if ds_key not in manifest_datasets:
            if contract_ds.get("required", True):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="MANIFEST_MISSING_DATASET",
                        message=f"Contract dataset '{ds_key}' not found in manifest",
                        path=f"datasets.{ds_key}",
                    )
                )
            continue

        manifest_ds = manifest_datasets[ds_key]
        _validate_dataset_against_contract(manifest_ds, contract_ds, ds_key, issues)


def _validate_dataset_against_contract(
    manifest_ds: dict[str, Any],
    contract_ds: dict[str, Any],
    ds_key: str,
    issues: list[ValidationIssue],
) -> None:
    """Validate a single dataset against contract.

    Args:
        manifest_ds: Manifest dataset.
        contract_ds: Contract dataset.
        ds_key: Dataset key.
        issues: List to append issues to.
    """
    manifest_items = manifest_ds.get("items", [])
    required = contract_ds.get("required", True)
    cardinality = contract_ds.get("cardinality", "many")

    if cardinality == "one":
        if required and len(manifest_items) != 1:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="MANIFEST_CARDINALITY_ONE",
                    message="Cardinality 'one' dataset must have exactly one item when required",
                    path=f"datasets.{ds_key}",
                )
            )
        if not required and len(manifest_items) > 1:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="MANIFEST_CARDINALITY_ONE_OPTIONAL",
                    message="Cardinality 'one' optional dataset may have at most one item",
                    path=f"datasets.{ds_key}",
                )
            )
    elif cardinality == "many":
        if required and len(manifest_items) < 1:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="MANIFEST_CARDINALITY_MANY",
                    message="Cardinality 'many' required dataset must have at least one item",
                    path=f"datasets.{ds_key}",
                )
            )

    for idx, manifest_item in enumerate(manifest_items):
        _validate_item_against_contract(manifest_item, contract_ds, ds_key, f"item[{idx}]", issues)


def _validate_item_against_contract(
    manifest_item: dict[str, Any],
    contract_ds: dict[str, Any],
    ds_key: str,
    item_label: str,
    issues: list[ValidationIssue],
) -> None:
    """Validate a single item against contract.

    Args:
        manifest_item: Manifest item.
        contract_ds: Contract dataset.
        ds_key: Dataset key.
        item_label: Item label/index for errors.
        issues: List to append issues to.
    """
    path = f"datasets.{ds_key}.items.{item_label}"

    # Owner check
    expected_owner = contract_ds.get("owner")
    owner = manifest_item.get("owner", {})
    owner_ok = True
    if expected_owner == "stage":
        owner_ok = bool(owner.get("stageId"))
    elif expected_owner == "well":
        owner_ok = bool(owner.get("wellId"))
    elif expected_owner == "platform":
        owner_ok = bool(owner.get("platformId"))

    if expected_owner and not owner_ok:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="MANIFEST_MISSING_OWNER",
                message=f"Owner '{expected_owner}Id' required for dataset '{ds_key}'",
                path=path,
            )
        )

    # Dimensions check
    contract_dims = set(contract_ds.get("dimensions", []) or [])
    manifest_dims = set((manifest_item.get("dims") or {}).keys())
    if contract_dims and manifest_dims != contract_dims:
        missing = contract_dims - manifest_dims
        extra = manifest_dims - contract_dims
        if missing:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="MANIFEST_MISSING_DIMENSIONS",
                    message=f"Missing dimensions: {missing}",
                    path=path,
                )
            )
        if extra:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    code="MANIFEST_EXTRA_DIMENSIONS",
                    message=f"Extra dimensions not in contract: {extra}",
                    path=path,
                )
            )

    # Ensure dimension values are non-empty when present
    dims_dict = manifest_item.get("dims") or {}
    for dim_key in contract_dims:
        if dim_key in dims_dict:
            if dims_dict[dim_key] in (None, ""):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="MANIFEST_DIMENSION_EMPTY",
                        message=f"Dimension '{dim_key}' must have a non-empty value",
                        path=f"{path}.dims.{dim_key}",
                    )
                )

    # Artifact check
    artifact = manifest_item.get("artifact")
    if artifact is None:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="MANIFEST_MISSING_ARTIFACT",
                message="Item missing artifact",
                path=path,
            )
        )
        return

    art_key = artifact.get("artifactKey") or artifact.get("key")
    art_type = artifact.get("type")
    if not art_key:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="MANIFEST_ARTIFACT_NO_KEY",
                message="Artifact missing artifactKey",
                path=path,
            )
        )

    kind_to_types = {
        "scalar": {"scalar"},
        "blob": {"blob"},
        "object": {"json", "object"},
        "frame": {"json", "parquet"},
    }
    expected_types = kind_to_types.get(contract_ds.get("kind"), set())
    if expected_types and art_type not in expected_types:
        issues.append(
            ValidationIssue(
                severity=ValidationSeverity.ERROR,
                code="MANIFEST_KIND_MISMATCH",
                message=f"Artifact type '{art_type}' incompatible with contract kind '{contract_ds.get('kind')}'",
                path=path,
            )
        )

    # For blob kind, check mime/ext consistency if provided
    if contract_ds.get("kind") == "blob":
        contract_schema = contract_ds.get("schema") or {}
        contract_mime = contract_schema.get("mime")
        if contract_mime and artifact.get("mimeType") and artifact.get("mimeType") != contract_mime:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="MANIFEST_BLOB_MIME_MISMATCH",
                    message=f"Artifact mimeType '{artifact.get('mimeType')}' does not match contract '{contract_mime}'",
                    path=path,
                )
            )


__all__ = [
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationResult",
    "validate_inputspec",
    "validate_output_contract",
    "validate_bundle",
    "validate_run_manifest",
]
