"""JSON Schema adapter for converting JSON Schema definitions to ColumnSpec definitions."""

from __future__ import annotations

from typing import Any, Callable, List, Mapping, Optional

from ..core import DEFAULT_FAKER_LOCALE, ColumnSpec, KeyRegistry, choices, faker_value, sequence
from .base import SchemaAdapter


class JSONSchemaAdapter(SchemaAdapter):
    """
    Adapter for JSON Schema format.

    Converts JSON Schema definitions to ColumnSpec objects.
    Supports: type inference, format detection, property name inference,
    constraints (enum, const, min/max), and smart ID field detection.
    """

    def to_columns(
        self,
        schema: Mapping[str, Any],
        *,
        faker_locale: str = DEFAULT_FAKER_LOCALE,
        seed: Optional[int] = None,
        registry: Optional[KeyRegistry] = None,
    ) -> List[ColumnSpec]:
        """Convert JSON Schema properties to ColumnSpec list."""
        properties = schema.get("properties")
        if not properties:
            raise ValueError("JSON Schema must define 'properties'")

        columns: List[ColumnSpec] = []

        for prop_name, prop_schema in properties.items():
            description = prop_schema.get("description")

            value_factory = self._create_value_factory(
                prop_name,
                prop_schema,
                faker_locale=faker_locale,
                seed=seed,
            )

            columns.append(
                ColumnSpec(
                    name=prop_name,
                    value=value_factory,
                    description=description,
                )
            )

        return columns

    def _create_value_factory(
        self,
        name: str,
        schema: Mapping[str, Any],
        *,
        faker_locale: str,
        seed: Optional[int],
    ) -> Callable[[int], Any]:
        """Create a value factory from a JSON Schema property definition."""

        # Handle const
        if "const" in schema:
            return schema["const"]

        # Handle enum as choices
        if "enum" in schema:
            return choices(schema["enum"])

        # Get type (default to string if not specified)
        schema_type = schema.get("type", "string")

        # Handle string type
        if schema_type == "string":
            return self._handle_string_type(name, schema, faker_locale, seed)

        # Handle integer type
        elif schema_type == "integer":
            return self._handle_integer_type(name, schema, faker_locale, seed)

        # Handle number type (float)
        elif schema_type == "number":
            minimum = schema.get("minimum", 0.0)
            maximum = schema.get("maximum", 1000.0)
            return faker_value(
                "pyfloat",
                locale=faker_locale,
                seed=seed,
                min_value=minimum,
                max_value=maximum,
            )

        # Handle boolean type
        elif schema_type == "boolean":
            return faker_value("pybool", locale=faker_locale, seed=seed)

        # Handle array type (generate empty arrays for simplicity)
        elif schema_type == "array":
            return lambda _: []

        # Handle object type (generate empty objects)
        elif schema_type == "object":
            return lambda _: {}

        # Default fallback
        return faker_value("word", locale=faker_locale, seed=seed)

    def _handle_string_type(
        self,
        name: str,
        schema: Mapping[str, Any],
        faker_locale: str,
        seed: Optional[int],
    ) -> Callable[[int], Any]:
        """Handle string type with format and property name inference."""

        # Check for format
        format_type = schema.get("format")
        if format_type:
            faker_provider = self._infer_faker_from_format(format_type)
            if faker_provider:
                kwargs = {}
                if format_type == "date":
                    kwargs = {"pattern": "%Y-%m-%d"}
                return faker_value(faker_provider, locale=faker_locale, seed=seed, **kwargs)

        # Try to infer from property name
        faker_provider = self._infer_faker_from_property_name(name)
        if faker_provider:
            return faker_value(faker_provider, locale=faker_locale, seed=seed)

        # Check for length constraints
        max_length = schema.get("maxLength", 50)

        # Default to text generator
        return faker_value("text", locale=faker_locale, seed=seed, max_nb_chars=max_length)

    def _handle_integer_type(
        self,
        name: str,
        schema: Mapping[str, Any],
        faker_locale: str,
        seed: Optional[int],
    ) -> Callable[[int], Any]:
        """Handle integer type with ID field detection."""
        minimum = schema.get("minimum", 0)
        maximum = schema.get("maximum", 1000)

        # If it looks like an ID field, use sequence
        if name.lower() in ["id", "pk", "key"] or name.lower().endswith("_id"):
            return sequence(start=minimum or 1, step=1)

        # Otherwise use random integers
        return faker_value(
            "pyint",
            locale=faker_locale,
            seed=seed,
            min_value=minimum,
            max_value=maximum,
        )

    @staticmethod
    def _infer_faker_from_format(format_type: str) -> Optional[str]:
        """Map JSON Schema format to Faker provider."""
        format_map = {
            "email": "email",
            "uri": "url",
            "url": "url",
            "uuid": "uuid4",
            "date": "date",
            "date-time": "iso8601",
            "time": "time",
            "ipv4": "ipv4",
            "ipv6": "ipv6",
            "hostname": "hostname",
        }
        return format_map.get(format_type)

    @staticmethod
    def _infer_faker_from_property_name(name: str) -> Optional[str]:
        """Infer Faker provider from common property names."""
        name_lower = name.lower()

        # Exact matches
        exact_matches = {
            "email": "email",
            "e-mail": "email",
            "mail": "email",
            "firstname": "first_name",
            "first_name": "first_name",
            "fname": "first_name",
            "lastname": "last_name",
            "last_name": "last_name",
            "lname": "last_name",
            "surname": "last_name",
            "name": "name",
            "fullname": "name",
            "full_name": "name",
            "phone": "phone_number",
            "telephone": "phone_number",
            "phone_number": "phone_number",
            "phonenumber": "phone_number",
            "address": "address",
            "street_address": "address",
            "city": "city",
            "country": "country",
            "zipcode": "postcode",
            "zip_code": "postcode",
            "postalcode": "postcode",
            "postal_code": "postcode",
            "company": "company",
            "company_name": "company",
            "url": "url",
            "website": "url",
            "username": "user_name",
            "user_name": "user_name",
            "password": "password",
        }

        if name_lower in exact_matches:
            return exact_matches[name_lower]

        # Partial matches
        if "email" in name_lower:
            return "email"
        if "phone" in name_lower:
            return "phone_number"
        if "address" in name_lower:
            return "address"
        if "city" in name_lower:
            return "city"
        if "country" in name_lower:
            return "country"
        if "company" in name_lower:
            return "company"

        return None


__all__ = ["JSONSchemaAdapter"]
