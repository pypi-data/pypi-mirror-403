"""Parse OData EDMX $metadata XML into Pydantic models.

Supports OData V4 and V3 namespace conventions.
"""

import xml.etree.ElementTree as ET

from pydantic import BaseModel

# OData V4 namespaces (primary)
_NS_EDMX_V4 = "http://docs.oasis-open.org/odata/ns/edmx"
_NS_EDM_V4 = "http://docs.oasis-open.org/odata/ns/edm"

# OData V3 / Microsoft namespaces (fallback)
_NS_EDMX_V3 = "http://schemas.microsoft.com/ado/2009/11/edmx"
_NS_EDM_V3 = "http://schemas.microsoft.com/ado/2009/11/edm"


class EdmProperty(BaseModel):
    """A scalar property on an entity type."""

    name: str
    type: str
    nullable: bool = True


class EdmNavigationProperty(BaseModel):
    """A navigation property (relationship) on an entity type."""

    name: str
    type: str
    partner: str | None = None


class EdmEntityType(BaseModel):
    """An OData entity type with its keys and properties."""

    name: str
    keys: list[str] = []
    properties: list[EdmProperty] = []
    navigation_properties: list[EdmNavigationProperty] = []


class EdmEntitySet(BaseModel):
    """An OData entity set (collection endpoint)."""

    name: str
    entity_type: str


class EdmxSchema(BaseModel):
    """Parsed EDMX schema containing entity types and entity sets."""

    entity_types: dict[str, EdmEntityType] = {}
    entity_sets: dict[str, EdmEntitySet] = {}


def _detect_namespaces(root: ET.Element) -> tuple[str, str]:
    """Detect whether the document uses V4 or V3 namespaces."""
    tag = root.tag
    if _NS_EDMX_V4 in tag:
        return _NS_EDMX_V4, _NS_EDM_V4
    if _NS_EDMX_V3 in tag:
        return _NS_EDMX_V3, _NS_EDM_V3
    # Default to V4
    return _NS_EDMX_V4, _NS_EDM_V4


def parse_edmx(xml_text: str) -> EdmxSchema:
    """Parse an EDMX XML string into an EdmxSchema.

    Args:
        xml_text: Raw XML string from $metadata endpoint.

    Returns:
        Parsed schema with entity types and entity sets.

    Raises:
        ET.ParseError: If the XML is malformed.
    """
    root = ET.fromstring(xml_text)
    ns_edmx, ns_edm = _detect_namespaces(root)

    entity_types: dict[str, EdmEntityType] = {}
    entity_sets: dict[str, EdmEntitySet] = {}

    for schema_el in root.iter(f"{{{ns_edm}}}Schema"):
        namespace = schema_el.get("Namespace", "")

        # Parse EntityType elements
        for et_el in schema_el.findall(f"{{{ns_edm}}}EntityType"):
            name = et_el.get("Name", "")
            qualified_name = f"{namespace}.{name}" if namespace else name

            # Keys
            keys: list[str] = []
            key_el = et_el.find(f"{{{ns_edm}}}Key")
            if key_el is not None:
                for prop_ref in key_el.findall(f"{{{ns_edm}}}PropertyRef"):
                    key_name = prop_ref.get("Name", "")
                    if key_name:
                        keys.append(key_name)

            # Properties
            properties: list[EdmProperty] = []
            for prop_el in et_el.findall(f"{{{ns_edm}}}Property"):
                prop_name = prop_el.get("Name", "")
                prop_type = prop_el.get("Type", "Edm.String")
                nullable_str = prop_el.get("Nullable", "true")
                properties.append(
                    EdmProperty(
                        name=prop_name,
                        type=prop_type,
                        nullable=nullable_str.lower() != "false",
                    )
                )

            # Navigation properties
            nav_properties: list[EdmNavigationProperty] = []
            for nav_el in et_el.findall(f"{{{ns_edm}}}NavigationProperty"):
                nav_name = nav_el.get("Name", "")
                nav_type = nav_el.get("Type", "")
                nav_partner = nav_el.get("Partner")
                nav_properties.append(
                    EdmNavigationProperty(
                        name=nav_name,
                        type=nav_type,
                        partner=nav_partner,
                    )
                )

            entity_types[qualified_name] = EdmEntityType(
                name=name,
                keys=keys,
                properties=properties,
                navigation_properties=nav_properties,
            )

        # Parse EntityContainer > EntitySet elements
        for container_el in schema_el.findall(f"{{{ns_edm}}}EntityContainer"):
            for es_el in container_el.findall(f"{{{ns_edm}}}EntitySet"):
                es_name = es_el.get("Name", "")
                es_type = es_el.get("EntityType", "")
                entity_sets[es_name] = EdmEntitySet(
                    name=es_name,
                    entity_type=es_type,
                )

    return EdmxSchema(entity_types=entity_types, entity_sets=entity_sets)
