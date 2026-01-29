"""Pydantic models and helpers for artifact input/output schemas."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class FieldSpec(BaseModel):
    name: str
    type: str = Field(..., description="JSON Schema type, e.g. string, integer, object")
    required: bool = Field(False)
    description: Optional[str] = None


class ArtifactSchema(BaseModel):
    """Simple artifact schema representation used for discovery and validation.

    This is intentionally small: it describes allowed `kind` values and a set of
    named fields with types and required flags.
    
    For JSON artifacts, you can optionally provide a full JSON Schema in `json_schema`
    for deep validation of nested structures. If `json_schema` is provided, it takes
    precedence over `fields` for validation. Fields can be auto-generated from json_schema
    if not explicitly provided.
    """

    kind: str = Field(..., description="Artifact kind, e.g. text, file, json, url")
    description: Optional[str] = None
    fields: List[FieldSpec] = Field(default_factory=list)
    json_schema: Optional[Dict[str, Any]] = Field(
        None, description="Full JSON Schema for deep validation (primarily for JSON artifacts)"
    )

    def model_post_init(self, __context: Any) -> None:
        """Auto-generate fields from json_schema if json_schema is provided and fields is empty."""
        if self.json_schema and not self.fields:
            self.fields = self._extract_fields_from_json_schema(self.json_schema)

    @staticmethod
    def _extract_fields_from_json_schema(json_schema: Dict[str, Any]) -> List[FieldSpec]:
        """Extract FieldSpec objects from a JSON Schema.
        
        This creates a simplified field list for discovery/metadata purposes.
        Only extracts top-level properties (does not recurse into nested objects).
        
        Args:
            json_schema: JSON Schema dictionary
            
        Returns:
            List of FieldSpec objects extracted from the schema
        """
        fields: List[FieldSpec] = []
        
        # Handle case where schema is wrapped in a reference or has a schema property
        schema = json_schema
        if "$ref" in schema:
            # Can't resolve references here, return empty
            return fields
        
        # Get the actual schema object
        if "schema" in schema:
            schema = schema["schema"]
        
        # Extract properties
        properties = schema.get("properties", {})
        required_fields = set(schema.get("required", []))
        
        # Map JSON Schema types to our simplified types
        type_mapping: Dict[str, str] = {
            "string": "string",
            "integer": "integer",
            "number": "number",
            "boolean": "boolean",
            "object": "object",
            "array": "array",
            "null": "null",
        }
        
        for prop_name, prop_schema in properties.items():
            # Handle type (can be string or array)
            prop_type = prop_schema.get("type")
            if isinstance(prop_type, list):
                # Take first non-null type
                prop_type = next((t for t in prop_type if t != "null"), prop_type[0] if prop_type else "object")
            
            # Map to our type system
            field_type = type_mapping.get(prop_type, "object" if prop_type is None else str(prop_type))
            
            # Check if required
            is_required = prop_name in required_fields
            
            # Get description
            field_description = prop_schema.get("description")
            
            fields.append(
                FieldSpec(
                    name=prop_name,
                    type=field_type,
                    required=is_required,
                    description=field_description,
                )
            )
        
        return fields


def validate_artifact_against_schema(artifact: Dict[str, Any], schema: ArtifactSchema) -> None:
    """Validate a raw artifact dict against an ArtifactSchema.

    Raises ValueError on validation failure with a short message.
    This is a conservative validator used at API boundary to give clear errors.
    
    For JSON artifacts, if `json_schema` is provided, it performs full JSON Schema
    validation on the artifact's `value` field. Otherwise, falls back to simple
    field-based validation.
    """
    # Check kind
    art_kind = artifact.get("kind")
    if art_kind != schema.kind:
        raise ValueError(f"artifact.kind must be '{schema.kind}', got '{art_kind}'")

    # For JSON artifacts with json_schema, use JSON Schema validation
    if art_kind == "json" and schema.json_schema is not None:
        value = artifact.get("value")
        if value is None:
            raise ValueError(f"JSON artifact must have a 'value' field")
        
        try:
            import jsonschema
            jsonschema.validate(instance=value, schema=schema.json_schema)
        except jsonschema.ValidationError as e:
            # Format JSON Schema validation error for user
            error_path = ".".join(str(p) for p in e.path) if e.path else "root"
            raise ValueError(
                f"JSON Schema validation failed at '{error_path}': {e.message}"
            ) from e
        except Exception as e:
            # Handle other JSON Schema errors (e.g., invalid schema)
            raise ValueError(f"JSON Schema validation error: {str(e)}") from e
        # If JSON Schema validation passed, we're done
        return

    # Fallback to simple field-based validation
    # Validate required fields presence
    for field in schema.fields:
        if field.required and field.name not in artifact:
            raise ValueError(f"missing required field '{field.name}' for kind '{schema.kind}'")

    # Basic type checks (best-effort)
    for field in schema.fields:
        if field.name in artifact and artifact[field.name] is not None:
            value = artifact[field.name]
            expected = field.type
            if expected == "string" and not isinstance(value, str):
                raise ValueError(f"field '{field.name}' must be a string")
            if expected == "integer" and not isinstance(value, int):
                raise ValueError(f"field '{field.name}' must be an integer")
            if expected == "object" and not isinstance(value, dict):
                raise ValueError(f"field '{field.name}' must be an object")
            if expected == "array" and not isinstance(value, list):
                raise ValueError(f"field '{field.name}' must be an array")


def validate_artifact_against_schemas(artifact: Dict[str, Any], schemas: List[ArtifactSchema]) -> None:
    """Validate a raw artifact dict against a list of ArtifactSchemas.

    The artifact must match at least one schema in the list. If none match,
    raises ValueError with details about why validation failed.

    Args:
        artifact: Raw artifact dict to validate
        schemas: List of ArtifactSchema objects to validate against

    Raises:
        ValueError: If artifact doesn't match any schema in the list
    """
    if not schemas:
        # No schemas defined, skip validation
        return

    errors = []
    for schema in schemas:
        try:
            validate_artifact_against_schema(artifact, schema)
            # If we get here, validation passed
            return
        except ValueError as e:
            errors.append(f"schema '{schema.kind}': {str(e)}")
            continue

    # If we get here, none of the schemas matched
    artifact_kind = artifact.get("kind", "unknown")
    raise ValueError(
        f"artifact with kind '{artifact_kind}' does not match any allowed schema. "
        f"Errors: {'; '.join(errors)}"
    )


