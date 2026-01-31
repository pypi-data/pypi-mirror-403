"""
Specification Frontmatter Validator.

Validates YAML frontmatter in SDLC 6.0.0 specification documents.

Rules:
- SPC-001: Missing required frontmatter fields
- SPC-002: Invalid field format or value
- SPC-003: Invalid YAML syntax
- SPC-004: Missing frontmatter block

SDLC 6.0.0 Standard (SPEC-0002):
- Required: spec_id, title, version, status, tier, owner, last_updated
- Optional: pillar, tags, related_adrs, related_specs, author, created, epic, sprint
- Format: YAML frontmatter enclosed in triple dashes (---)

Part of Sprint 125 - Multi-Frontend Alignment.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..base_validator import BaseValidator
from ..violation import Severity, ViolationReport

# Try to import YAML parser
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Try to import jsonschema for validation
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


class SpecFrontmatterValidator(BaseValidator):
    """
    Validates YAML frontmatter in specification documents.

    Checks:
    - Required fields present (spec_id, title, version, status, tier, owner, last_updated)
    - Valid field formats per SPEC-0002 schema
    - Valid YAML syntax
    - Frontmatter block present
    """

    VALIDATOR_ID = "spec-frontmatter"
    VALIDATOR_NAME = "Specification Frontmatter Validator"
    VALIDATOR_DESCRIPTION = "Validates YAML frontmatter in SDLC 6.0.0 specification documents"

    # YAML frontmatter pattern (matches content between ---)
    YAML_FRONTMATTER = re.compile(
        r"^---\s*\n(.*?)\n---\s*\n", re.MULTILINE | re.DOTALL
    )

    # Required fields per SPEC-0002
    REQUIRED_FIELDS = {
        "spec_id",
        "title",
        "version",
        "status",
        "tier",
        "owner",
        "last_updated",
    }

    # Field validation patterns (fallback when jsonschema unavailable)
    FIELD_PATTERNS = {
        "spec_id": re.compile(r"^SPEC-[0-9]{4}$"),
        "version": re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$"),
        "status": re.compile(r"^(DRAFT|REVIEW|APPROVED|ACTIVE|DEPRECATED)$"),
        "last_updated": re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$"),
    }

    # Valid status values
    VALID_STATUSES = {"DRAFT", "REVIEW", "APPROVED", "ACTIVE", "DEPRECATED"}

    # Valid tier values
    VALID_TIERS = {"LITE", "STANDARD", "PROFESSIONAL", "ENTERPRISE"}

    # Specification file patterns
    SPEC_FILE_PATTERNS = [
        "SPEC-*.md",
        "**/SPEC-*.md",
    ]

    # Directories to search for specs
    SPEC_DIRECTORIES = [
        "02-design/14-Technical-Specs",
        "docs/02-design/14-Technical-Specs",
        "specs",
        "docs/specs",
    ]

    # Folders to skip
    SKIP_FOLDERS = {"node_modules", ".git", "__pycache__", "99-legacy", "10-archive"}

    def __init__(self, docs_root: Path):
        """
        Initialize validator.

        Args:
            docs_root: Root directory of SDLC documentation
        """
        super().__init__(docs_root)
        self._schema: Optional[Dict[str, Any]] = None

    @property
    def schema(self) -> Optional[Dict[str, Any]]:
        """Load JSON schema lazily."""
        if self._schema is None:
            schema_path = Path(__file__).parent.parent.parent / "schemas" / "spec-frontmatter-schema.json"
            if schema_path.exists():
                try:
                    with open(schema_path, "r", encoding="utf-8") as f:
                        self._schema = json.load(f)
                except Exception:
                    self._schema = {}
            else:
                self._schema = {}
        return self._schema

    def validate(self, paths: Optional[List[Path]] = None) -> List[ViolationReport]:
        """
        Validate specification frontmatter.

        Args:
            paths: Optional list of specific paths to validate

        Returns:
            List of violations found
        """
        violations: List[ViolationReport] = []

        if not self.docs_root.exists():
            return violations

        # Find specification files
        spec_files = self._find_spec_files(paths)

        for spec_file in spec_files:
            # Skip files in ignored folders
            if self._should_skip_file(spec_file):
                continue

            # Validate frontmatter
            file_violations = self._validate_file(spec_file)
            violations.extend(file_violations)

        return violations

    def _find_spec_files(self, paths: Optional[List[Path]] = None) -> List[Path]:
        """
        Find specification files to validate.

        Args:
            paths: Optional specific paths to validate

        Returns:
            List of spec file paths
        """
        if paths:
            return [p for p in paths if p.suffix == ".md" and "SPEC-" in p.name]

        spec_files = []

        # Search in standard spec directories
        for spec_dir in self.SPEC_DIRECTORIES:
            dir_path = self.docs_root / spec_dir
            if dir_path.exists():
                spec_files.extend(dir_path.glob("SPEC-*.md"))

        # Also search for SPEC-*.md anywhere in docs_root
        for pattern in self.SPEC_FILE_PATTERNS:
            spec_files.extend(self.docs_root.glob(pattern))

        # Deduplicate while preserving order
        seen = set()
        unique_files = []
        for f in spec_files:
            if f not in seen:
                seen.add(f)
                unique_files.append(f)

        return unique_files

    def _should_skip_file(self, file: Path) -> bool:
        """
        Check if file should be skipped.

        Args:
            file: File path to check

        Returns:
            True if file should be skipped
        """
        for part in file.parts:
            if part in self.SKIP_FOLDERS:
                return True

        if file.name.startswith("."):
            return True

        return False

    def _validate_file(self, file: Path) -> List[ViolationReport]:
        """
        Validate a single specification file.

        Args:
            file: Specification file to validate

        Returns:
            List of violations for this file
        """
        violations = []

        try:
            content = file.read_text(encoding="utf-8")
        except Exception as e:
            violations.append(
                ViolationReport(
                    rule_id="SPC-003",
                    severity=Severity.ERROR,
                    file_path=file,
                    message=f"Cannot read file: {e}",
                    fix_suggestion="Ensure file is accessible and has valid encoding",
                    auto_fixable=False,
                    context={"error": str(e)},
                )
            )
            return violations

        # Check for frontmatter block
        frontmatter_match = self.YAML_FRONTMATTER.match(content)
        if not frontmatter_match:
            violations.append(
                ViolationReport(
                    rule_id="SPC-004",
                    severity=Severity.ERROR,
                    file_path=file,
                    message="Missing YAML frontmatter block",
                    fix_suggestion=self._generate_frontmatter_template(file),
                    auto_fixable=True,
                    context={"file": str(file)},
                )
            )
            return violations

        # Parse YAML
        frontmatter_text = frontmatter_match.group(1)
        frontmatter = self._parse_yaml(frontmatter_text)

        if frontmatter is None:
            violations.append(
                ViolationReport(
                    rule_id="SPC-003",
                    severity=Severity.ERROR,
                    file_path=file,
                    message="Invalid YAML syntax in frontmatter",
                    fix_suggestion="Fix YAML syntax errors in frontmatter block",
                    auto_fixable=False,
                    context={"frontmatter": frontmatter_text[:200]},
                )
            )
            return violations

        # Validate using JSON schema if available
        if HAS_JSONSCHEMA and self.schema:
            schema_violations = self._validate_with_schema(file, frontmatter)
            violations.extend(schema_violations)
        else:
            # Fallback to manual validation
            manual_violations = self._validate_manually(file, frontmatter)
            violations.extend(manual_violations)

        return violations

    def _parse_yaml(self, yaml_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse YAML frontmatter.

        Args:
            yaml_text: YAML content to parse

        Returns:
            Parsed dictionary or None if invalid
        """
        if HAS_YAML:
            try:
                return yaml.safe_load(yaml_text)
            except yaml.YAMLError:
                return None
        else:
            # Simple fallback parser for key: value pairs
            result = {}
            for line in yaml_text.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, _, value = line.partition(":")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if value:
                        result[key] = value
            return result if result else None

    def _validate_with_schema(
        self, file: Path, frontmatter: Dict[str, Any]
    ) -> List[ViolationReport]:
        """
        Validate frontmatter using JSON schema.

        Args:
            file: File being validated
            frontmatter: Parsed frontmatter dictionary

        Returns:
            List of schema validation violations
        """
        violations = []

        try:
            jsonschema.validate(frontmatter, self.schema)
        except jsonschema.ValidationError as e:
            # Extract field name from error path
            field_path = ".".join(str(p) for p in e.absolute_path) or "(root)"

            violations.append(
                ViolationReport(
                    rule_id="SPC-002",
                    severity=Severity.ERROR,
                    file_path=file,
                    message=f"Invalid frontmatter field '{field_path}': {e.message}",
                    fix_suggestion=self._get_field_suggestion(field_path, frontmatter),
                    auto_fixable=True,
                    context={
                        "field": field_path,
                        "error": e.message,
                        "current_value": frontmatter.get(field_path),
                    },
                )
            )
        except jsonschema.SchemaError as e:
            violations.append(
                ViolationReport(
                    rule_id="SPC-002",
                    severity=Severity.WARNING,
                    file_path=file,
                    message=f"Schema error: {e.message}",
                    fix_suggestion="Contact maintainers to fix schema",
                    auto_fixable=False,
                    context={"schema_error": str(e)},
                )
            )

        return violations

    def _validate_manually(
        self, file: Path, frontmatter: Dict[str, Any]
    ) -> List[ViolationReport]:
        """
        Validate frontmatter manually (fallback when jsonschema unavailable).

        Args:
            file: File being validated
            frontmatter: Parsed frontmatter dictionary

        Returns:
            List of validation violations
        """
        violations = []

        # Check required fields
        missing_fields = self.REQUIRED_FIELDS - set(frontmatter.keys())
        if missing_fields:
            violations.append(
                ViolationReport(
                    rule_id="SPC-001",
                    severity=Severity.ERROR,
                    file_path=file,
                    message=f"Missing required frontmatter fields: {', '.join(sorted(missing_fields))}",
                    fix_suggestion=self._generate_missing_fields_template(frontmatter, missing_fields),
                    auto_fixable=True,
                    context={
                        "missing_fields": sorted(missing_fields),
                        "current_fields": list(frontmatter.keys()),
                    },
                )
            )

        # Validate field patterns
        for field, pattern in self.FIELD_PATTERNS.items():
            if field in frontmatter:
                value = str(frontmatter[field])
                if not pattern.match(value):
                    violations.append(
                        ViolationReport(
                            rule_id="SPC-002",
                            severity=Severity.ERROR,
                            file_path=file,
                            message=f"Invalid format for '{field}': '{value}'",
                            fix_suggestion=self._get_field_suggestion(field, frontmatter),
                            auto_fixable=True,
                            context={
                                "field": field,
                                "current_value": value,
                                "expected_pattern": pattern.pattern,
                            },
                        )
                    )

        # Validate status enum
        if "status" in frontmatter:
            status = str(frontmatter["status"]).upper()
            if status not in self.VALID_STATUSES:
                violations.append(
                    ViolationReport(
                        rule_id="SPC-002",
                        severity=Severity.ERROR,
                        file_path=file,
                        message=f"Invalid status: '{frontmatter['status']}'. Must be one of: {', '.join(sorted(self.VALID_STATUSES))}",
                        fix_suggestion=f"Use one of: {', '.join(sorted(self.VALID_STATUSES))}",
                        auto_fixable=True,
                        context={
                            "field": "status",
                            "current_value": frontmatter["status"],
                            "valid_values": sorted(self.VALID_STATUSES),
                        },
                    )
                )

        # Validate tier values
        if "tier" in frontmatter:
            tiers = frontmatter["tier"]
            if isinstance(tiers, str):
                tiers = [tiers]
            if isinstance(tiers, list):
                invalid_tiers = [t for t in tiers if str(t).upper() not in self.VALID_TIERS]
                if invalid_tiers:
                    violations.append(
                        ViolationReport(
                            rule_id="SPC-002",
                            severity=Severity.ERROR,
                            file_path=file,
                            message=f"Invalid tier values: {', '.join(invalid_tiers)}. Must be one of: {', '.join(sorted(self.VALID_TIERS))}",
                            fix_suggestion=f"Use valid tiers: {', '.join(sorted(self.VALID_TIERS))}",
                            auto_fixable=True,
                            context={
                                "field": "tier",
                                "invalid_values": invalid_tiers,
                                "valid_values": sorted(self.VALID_TIERS),
                            },
                        )
                    )

        return violations

    def _get_field_suggestion(self, field: str, frontmatter: Dict[str, Any]) -> str:
        """
        Get fix suggestion for a specific field.

        Args:
            field: Field name
            frontmatter: Current frontmatter

        Returns:
            Fix suggestion string
        """
        suggestions = {
            "spec_id": "Use format: spec_id: SPEC-0001",
            "title": "Add descriptive title: title: \"My Specification Title\"",
            "version": "Use semantic versioning: version: \"1.0.0\"",
            "status": f"Use valid status: status: {'/'.join(sorted(self.VALID_STATUSES))}",
            "tier": "Specify applicable tiers:\ntier:\n  - LITE\n  - STANDARD\n  - PROFESSIONAL\n  - ENTERPRISE",
            "owner": "Specify owner: owner: \"Team/Person Name\"",
            "last_updated": "Use ISO date format: last_updated: \"2026-01-30\"",
            "pillar": "Specify pillar: pillar: \"Pillar 7 - Quality Assurance\"",
            "tags": "Add categorization tags:\ntags:\n  - tag-name",
            "related_adrs": "Reference related ADRs:\nrelated_adrs:\n  - ADR-001-Description",
            "related_specs": "Reference related specs:\nrelated_specs:\n  - SPEC-0001",
        }
        return suggestions.get(field, f"Fix the '{field}' field according to SPEC-0002 standard")

    def _generate_frontmatter_template(self, file: Path) -> str:
        """
        Generate frontmatter template for a spec file.

        Args:
            file: Spec file path

        Returns:
            Template string
        """
        # Extract spec ID from filename
        spec_id_match = re.search(r"SPEC-(\d{4})", file.name)
        spec_id = f"SPEC-{spec_id_match.group(1)}" if spec_id_match else "SPEC-0000"

        # Generate title from filename
        title_part = file.stem.replace(spec_id + "-", "").replace("-", " ").title()

        return f'''Add YAML frontmatter at the beginning of the file:

---
spec_id: {spec_id}
title: "{title_part}"
version: "1.0.0"
status: DRAFT
tier:
  - LITE
  - STANDARD
  - PROFESSIONAL
  - ENTERPRISE
owner: "<owner-name>"
last_updated: "<YYYY-MM-DD>"
---'''

    def _generate_missing_fields_template(
        self, frontmatter: Dict[str, Any], missing: set
    ) -> str:
        """
        Generate template for missing fields.

        Args:
            frontmatter: Current frontmatter
            missing: Set of missing field names

        Returns:
            Template showing missing fields
        """
        lines = ["Add the following missing fields to frontmatter:", ""]

        defaults = {
            "spec_id": "SPEC-0000",
            "title": '"<specification-title>"',
            "version": '"1.0.0"',
            "status": "DRAFT",
            "tier": "\n  - LITE\n  - STANDARD\n  - PROFESSIONAL\n  - ENTERPRISE",
            "owner": '"<owner-name>"',
            "last_updated": '"<YYYY-MM-DD>"',
        }

        for field in sorted(missing):
            default = defaults.get(field, '"<value>"')
            lines.append(f"{field}: {default}")

        return "\n".join(lines)
