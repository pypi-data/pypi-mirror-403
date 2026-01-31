"""Tests for FieldsPath class."""

import pytest

from fields_metadata.metadata import FieldMetadata
from fields_metadata.path import FieldsMetadataMap, FieldsPath


def test_fields_path_basic_instantiation() -> None:
    """FieldsPath can be instantiated with minimal required fields."""
    metadata = FieldMetadata(field_name="test_field", field_type=str)
    path = FieldsPath(name="test_field", metadata=metadata)
    assert path.name == "test_field"
    assert path.metadata == metadata
    assert path.prev is None
    assert path.next is None


def test_fields_path_iteration_single_node() -> None:
    """FieldsPath iteration works for a single node."""
    metadata = FieldMetadata(field_name="field", field_type=str)
    path = FieldsPath(name="field", metadata=metadata)

    nodes = list(path)
    assert len(nodes) == 1
    assert nodes[0].name == "field"


def test_fields_path_iteration_multiple_nodes() -> None:
    """FieldsPath iteration works for multiple nodes."""
    # Create metadata for a path: root -> child -> grandchild
    root_metadata = FieldMetadata(field_name="root", field_type=object, composite=True)
    child_metadata = FieldMetadata(
        field_name="child", field_type=object, composite=True, parent_field=None
    )
    grandchild_metadata = FieldMetadata(field_name="grandchild", field_type=str, parent_field=None)

    # Build the path
    root = FieldsPath(name="root", metadata=root_metadata)
    child = FieldsPath(name="child", metadata=child_metadata, prev=root)
    grandchild = FieldsPath(name="grandchild", metadata=grandchild_metadata, prev=child)

    root.next = child
    child.next = grandchild

    # Iterate from root
    nodes = list(root)
    assert len(nodes) == 3
    assert nodes[0].name == "root"
    assert nodes[1].name == "child"
    assert nodes[2].name == "grandchild"


def test_fields_path_last_property_single_node() -> None:
    """FieldsPath.last returns self for single node."""
    metadata = FieldMetadata(field_name="field", field_type=str)
    path = FieldsPath(name="field", metadata=metadata)
    assert path.last == path


def test_fields_path_last_property_multiple_nodes() -> None:
    """FieldsPath.last returns the last node in the chain."""
    # Create three nodes
    first_metadata = FieldMetadata(field_name="first", field_type=object, composite=True)
    second_metadata = FieldMetadata(field_name="second", field_type=object, composite=True)
    third_metadata = FieldMetadata(field_name="third", field_type=str)

    first = FieldsPath(name="first", metadata=first_metadata)
    second = FieldsPath(name="second", metadata=second_metadata, prev=first)
    third = FieldsPath(name="third", metadata=third_metadata, prev=second)

    first.next = second
    second.next = third

    assert first.last == third
    assert second.last == third
    assert third.last == third


@pytest.mark.parametrize(
    "field_type,is_derived,direction,expected_string",
    [
        ("composite", False, "forward", "address.street"),
        ("composite", False, "backward", "address.street"),
        ("derived", True, "forward", "date__year"),
        ("derived", True, "backward", "date__year"),
    ],
)
def test_get_path_string_generation(
    field_type: str, is_derived: bool, direction: str, expected_string: str
) -> None:
    """Test path string generation for different field types and directions."""
    if field_type == "composite":
        parent_metadata = FieldMetadata(field_name="address", field_type=object, composite=True)
        child_metadata = FieldMetadata(field_name="street", field_type=str, parent_field="address")
    else:
        parent_metadata = FieldMetadata(field_name="date", field_type=object)
        child_metadata = FieldMetadata(field_name="year", field_type=int, derived=is_derived)

    parent = FieldsPath(name=parent_metadata.field_name, metadata=parent_metadata)
    child = FieldsPath(name=child_metadata.field_name, metadata=child_metadata, prev=parent)
    parent.next = child

    if direction == "forward":
        assert parent.get_path_string() == expected_string
    else:
        assert child.get_path_string(complimentary=True) == expected_string


def test_get_path_string_custom_separators() -> None:
    """get_path_string uses custom separators correctly."""
    # Create composite path
    parent_metadata = FieldMetadata(field_name="parent", field_type=object, composite=True)
    child_metadata = FieldMetadata(field_name="child", field_type=str, parent_field="parent")

    parent = FieldsPath(name="parent", metadata=parent_metadata)
    child = FieldsPath(name="child", metadata=child_metadata, prev=parent)
    parent.next = child

    assert parent.get_path_string(composite_separator="/") == "parent/child"


def test_from_field_metadata_simple_field() -> None:
    """from_field_metadata creates path for a simple root field."""
    metadata_map: FieldsMetadataMap = {"name": FieldMetadata(field_name="name", field_type=str)}

    path = FieldsPath.from_field_metadata("name", metadata_map)
    assert path is not None
    assert path.name == "name"
    assert path.prev is None
    assert path.next is None


def test_from_field_metadata_composite_field() -> None:
    """from_field_metadata creates path for composite nested fields."""
    address_metadata = FieldMetadata(field_name="address", field_type=object, composite=True)
    street_metadata = FieldMetadata(field_name="street", field_type=str, parent_field="address")

    metadata_map: FieldsMetadataMap = {
        "address": address_metadata,
        "address.street": street_metadata,
    }

    path = FieldsPath.from_field_metadata("address.street", metadata_map)
    assert path is not None
    assert path.name == "address"
    assert path.next is not None
    assert path.next.name == "street"
    assert path.next.prev == path


def test_from_field_metadata_derived_field() -> None:
    """from_field_metadata creates path for derived fields."""
    date_metadata = FieldMetadata(field_name="date", field_type=object)
    year_metadata = FieldMetadata(field_name="year", field_type=int, derived=True)

    metadata_map: FieldsMetadataMap = {
        "date": date_metadata,
        "date__year": year_metadata,
    }

    path = FieldsPath.from_field_metadata("date__year", metadata_map)
    assert path is not None
    assert path.name == "date"
    assert path.next is not None
    assert path.next.name == "year"
    assert path.next.metadata.derived is True


def test_from_field_metadata_deep_nesting() -> None:
    """from_field_metadata creates path for deeply nested fields."""
    root_metadata = FieldMetadata(field_name="root", field_type=object, composite=True)
    mid_metadata = FieldMetadata(
        field_name="mid", field_type=object, composite=True, parent_field="root"
    )
    leaf_metadata = FieldMetadata(field_name="leaf", field_type=str, parent_field="root.mid")

    metadata_map: FieldsMetadataMap = {
        "root": root_metadata,
        "root.mid": mid_metadata,
        "root.mid.leaf": leaf_metadata,
    }

    path = FieldsPath.from_field_metadata("root.mid.leaf", metadata_map)
    assert path is not None

    nodes = list(path)
    assert len(nodes) == 3
    assert nodes[0].name == "root"
    assert nodes[1].name == "mid"
    assert nodes[2].name == "leaf"


def test_from_field_metadata_missing_field() -> None:
    """from_field_metadata returns None for missing field."""
    metadata_map: FieldsMetadataMap = {
        "existing": FieldMetadata(field_name="existing", field_type=str)
    }

    path = FieldsPath.from_field_metadata("nonexistent", metadata_map)
    assert path is None


def test_from_field_metadata_empty_map() -> None:
    """from_field_metadata returns None for empty metadata map."""
    metadata_map: FieldsMetadataMap = {}
    path = FieldsPath.from_field_metadata("field", metadata_map)
    assert path is None


def test_full_doc_single_field_with_doc() -> None:
    """full_doc returns documentation for a single field."""
    metadata = FieldMetadata(field_name="field", field_type=str, doc="Field documentation")
    path = FieldsPath(name="field", metadata=metadata)

    docs = FieldsPath.full_doc(path)
    assert docs == ["Field documentation"]


def test_full_doc_single_field_without_doc() -> None:
    """full_doc returns empty list for field without documentation."""
    metadata = FieldMetadata(field_name="field", field_type=str)
    path = FieldsPath(name="field", metadata=metadata)

    docs = FieldsPath.full_doc(path)
    assert docs == []


def test_full_doc_multiple_fields_with_docs() -> None:
    """full_doc concatenates documentation from all fields in path."""
    parent_metadata = FieldMetadata(
        field_name="parent", field_type=object, composite=True, doc="Parent field documentation"
    )
    child_metadata = FieldMetadata(
        field_name="child",
        field_type=str,
        parent_field=parent_metadata,
        doc="Child field documentation",
    )

    parent = FieldsPath(name="parent", metadata=parent_metadata)
    child = FieldsPath(name="child", metadata=child_metadata, prev=parent)
    parent.next = child

    docs = FieldsPath.full_doc(parent)
    assert docs == ["Parent field documentation", "Child field documentation"]


def test_full_doc_mixed_documentation() -> None:
    """full_doc includes only fields that have documentation."""
    first_metadata = FieldMetadata(
        field_name="first", field_type=object, composite=True, doc="First field doc"
    )
    second_metadata = FieldMetadata(
        field_name="second", field_type=object, composite=True, parent_field=None
    )
    third_metadata = FieldMetadata(
        field_name="third", field_type=str, parent_field=second_metadata, doc="Third field doc"
    )

    first = FieldsPath(name="first", metadata=first_metadata)
    second = FieldsPath(name="second", metadata=second_metadata, prev=first)
    third = FieldsPath(name="third", metadata=third_metadata, prev=second)

    first.next = second
    second.next = third

    docs = FieldsPath.full_doc(first)
    assert docs == ["First field doc", "Third field doc"]
