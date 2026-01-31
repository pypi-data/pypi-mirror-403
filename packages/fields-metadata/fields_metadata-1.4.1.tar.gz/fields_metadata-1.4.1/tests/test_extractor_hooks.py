"""Tests for hook system in MetadataExtractor."""

from dataclasses import dataclass
from datetime import date, datetime

from fields_metadata.extractor import MetadataExtractor
from fields_metadata.metadata import FieldMetadata


@dataclass
class EventData:
    """Test model with datetime fields."""

    event_name: str
    event_date: datetime
    created_at: date


@dataclass
class UserProfile:
    """Test model with nested structure."""

    username: str
    reported_by_organization_id: str


def build_field_path(metadata: FieldMetadata) -> str:
    """Build field path by traversing parent relationships."""
    parts = [metadata.field_name]
    current = metadata.parent_field
    while current:
        parts.insert(0, current.field_name)
        current = current.parent_field
    return ".".join(parts)


def test_type_hook_datetime() -> None:
    """Test type-based hook that generates derived fields from datetime."""
    extractor = MetadataExtractor()

    # Register hook to generate year, month, day fields from datetime
    def datetime_hook(source: FieldMetadata) -> dict[str, FieldMetadata]:
        """Generate year, month, day fields from datetime field."""
        base_path = build_field_path(source)
        parent = source.parent_field

        return {
            f"{base_path}__year": FieldMetadata(
                field_name=f"{source.field_name}__year",
                field_type=int,
                effective_type=int,
                numeric=True,
                derived=True,
                parent_field=parent,
            ),
            f"{base_path}__month": FieldMetadata(
                field_name=f"{source.field_name}__month",
                field_type=int,
                effective_type=int,
                numeric=True,
                derived=True,
                parent_field=parent,
            ),
            f"{base_path}__day": FieldMetadata(
                field_name=f"{source.field_name}__day",
                field_type=int,
                effective_type=int,
                numeric=True,
                derived=True,
                parent_field=parent,
            ),
        }

    extractor.register_type_hook(datetime, datetime_hook)

    result = extractor.extract(EventData)

    # Check original fields exist
    assert "event_name" in result
    assert "event_date" in result
    assert "created_at" in result

    # Check derived fields from event_date (datetime)
    assert "event_date__year" in result
    assert "event_date__month" in result
    assert "event_date__day" in result

    # Verify derived field properties
    assert result["event_date__year"].derived is True
    assert result["event_date__year"].field_type == int
    assert result["event_date__year"].numeric is True
    assert result["event_date__year"].parent_field is result["event_date"].parent_field

    # Date type should not trigger datetime hook
    assert "created_at__year" not in result  # date != datetime, won't trigger


def test_type_hook_date() -> None:
    """Test type-based hook for date type."""
    extractor = MetadataExtractor()

    def date_hook(source: FieldMetadata) -> dict[str, FieldMetadata]:
        """Generate year field from date field."""
        base_path = build_field_path(source)

        return {
            f"{base_path}__year": FieldMetadata(
                field_name=f"{source.field_name}__year",
                field_type=int,
                effective_type=int,
                numeric=True,
                derived=True,
                parent_field=source.parent_field,
            ),
        }

    extractor.register_type_hook(date, date_hook)

    result = extractor.extract(EventData)

    # Only created_at should generate derived field
    assert "created_at__year" in result
    assert result["created_at__year"].derived is True

    # event_date is datetime, not date, so no derived field from this hook
    assert "event_date__year" not in result


def test_name_hook_with_regex() -> None:
    """Test name-based hook using regex pattern."""
    extractor = MetadataExtractor()

    def organization_id_hook(source: FieldMetadata) -> dict[str, FieldMetadata]:
        """Generate derived field for organization ID fields."""
        base_path = build_field_path(source)

        return {
            f"{base_path}__hash": FieldMetadata(
                field_name=f"{source.field_name}__hash",
                field_type=str,
                effective_type=str,
                derived=True,
                parent_field=source.parent_field,
            ),
        }

    # Register hook that matches any field path containing "organization" and ending with "id"
    extractor.register_name_hook(r".*organization.*id$", organization_id_hook)

    result = extractor.extract(UserProfile)

    # Check original fields
    assert "username" in result
    assert "reported_by_organization_id" in result

    # Check derived field
    assert "reported_by_organization_id__hash" in result
    assert result["reported_by_organization_id__hash"].derived is True

    # username should not trigger the hook
    assert "username__hash" not in result


def test_name_hook_with_predicate() -> None:
    """Test name-based hook using predicate function."""
    extractor = MetadataExtractor()

    def name_ends_with_id_hook(source: FieldMetadata) -> dict[str, FieldMetadata]:
        """Generate derived field for fields ending with _id."""
        base_path = build_field_path(source)

        return {
            f"{base_path}__normalized": FieldMetadata(
                field_name=f"{source.field_name}__normalized",
                field_type=str,
                effective_type=str,
                derived=True,
                parent_field=source.parent_field,
            ),
        }

    # Register hook with custom predicate
    extractor.register_name_hook(lambda path: path.endswith("_id"), name_ends_with_id_hook)

    result = extractor.extract(UserProfile)

    # reported_by_organization_id ends with _id, should trigger hook
    assert "reported_by_organization_id__normalized" in result
    assert result["reported_by_organization_id__normalized"].derived is True

    # username doesn't end with _id
    assert "username__normalized" not in result


def test_multiple_hooks_same_field() -> None:
    """Test that multiple hooks can be triggered for the same field."""
    extractor = MetadataExtractor()

    def hook1(source: FieldMetadata) -> dict[str, FieldMetadata]:
        base_path = build_field_path(source)
        return {
            f"{base_path}__derived1": FieldMetadata(
                field_name=f"{source.field_name}__derived1",
                field_type=int,
                effective_type=int,
                derived=True,
            ),
        }

    def hook2(source: FieldMetadata) -> dict[str, FieldMetadata]:
        base_path = build_field_path(source)
        return {
            f"{base_path}__derived2": FieldMetadata(
                field_name=f"{source.field_name}__derived2",
                field_type=str,
                effective_type=str,
                derived=True,
            ),
        }

    # Register both hooks for datetime type
    extractor.register_type_hook(datetime, hook1)
    extractor.register_type_hook(datetime, hook2)

    result = extractor.extract(EventData)

    # Both hooks should be executed for event_date
    assert "event_date__derived1" in result
    assert "event_date__derived2" in result
    assert result["event_date__derived1"].field_type == int
    assert result["event_date__derived2"].field_type == str


def test_no_hooks_registered() -> None:
    """Test that extraction works normally when no hooks are registered."""
    extractor = MetadataExtractor()

    result = extractor.extract(EventData)

    # Should only have original fields
    assert len(result) == 3
    assert "event_name" in result
    assert "event_date" in result
    assert "created_at" in result

    # No derived fields
    for metadata in result.values():
        assert metadata.derived is False


def test_hook_returns_empty_dict() -> None:
    """Test that hook can return empty dict."""
    extractor = MetadataExtractor()

    def empty_hook(source: FieldMetadata) -> dict[str, FieldMetadata]:
        """Hook that returns empty dict."""
        return {}

    extractor.register_type_hook(datetime, empty_hook)

    result = extractor.extract(EventData)

    # Should still have all original fields
    assert len(result) == 3
    assert all(not m.derived for m in result.values())


def test_derived_field_marked_automatically() -> None:
    """Test that derived=True is set automatically if not specified."""
    extractor = MetadataExtractor()

    def hook_without_derived_flag(source: FieldMetadata) -> dict[str, FieldMetadata]:
        """Hook that doesn't set derived=True explicitly."""
        base_path = build_field_path(source)
        return {
            f"{base_path}__auto": FieldMetadata(
                field_name=f"{source.field_name}__auto",
                field_type=int,
                effective_type=int,
            ),
        }

    extractor.register_type_hook(datetime, hook_without_derived_flag)

    result = extractor.extract(EventData)

    assert "event_date__auto" in result
    assert result["event_date__auto"].derived is True


def test_register_before_extract_hook() -> None:
    """Test that before_extract hook is called before extraction starts."""
    extractor = MetadataExtractor()
    called_types = []

    def before_hook(obj_type: type) -> None:
        called_types.append(obj_type)

    extractor.register_before_extract_hook(before_hook)
    result = extractor.extract(EventData)

    assert EventData in called_types
    assert len(result) > 0


def test_register_after_extract_hook() -> None:
    """Test that after_extract hook can modify metadata after extraction."""
    extractor = MetadataExtractor()

    def after_hook(obj_type: type, metadata: dict[str, FieldMetadata]) -> None:
        for field_metadata in metadata.values():
            if not field_metadata.derived and field_metadata.field_type == str:
                field_metadata.categorical = False

    extractor.register_after_extract_hook(after_hook)
    result = extractor.extract(EventData)

    assert result["event_name"].categorical is False


def test_register_after_derived_hook() -> None:
    """Test that after_derived hook is called after all derived fields are added."""
    extractor = MetadataExtractor()

    def datetime_hook(source: FieldMetadata) -> dict[str, FieldMetadata]:
        base_path = build_field_path(source)
        return {
            f"{base_path}__year": FieldMetadata(
                field_name=f"{source.field_name}__year",
                field_type=int,
                effective_type=int,
                derived=True,
            ),
        }

    extractor.register_type_hook(datetime, datetime_hook)

    derived_count = []

    def after_derived_hook(obj_type: type, metadata: dict[str, FieldMetadata]) -> None:
        count = sum(1 for m in metadata.values() if m.derived)
        derived_count.append(count)

    extractor.register_after_derived_hook(after_derived_hook)
    result = extractor.extract(EventData)

    assert len(derived_count) == 1
    assert derived_count[0] == 1
    assert "event_date__year" in result


def test_register_before_field_hook() -> None:
    """Test that before_field hook is called before extracting each field."""
    extractor = MetadataExtractor()
    processed_fields = []

    def before_field_hook(field_name: str, field_type: type, parent_type: type) -> None:
        processed_fields.append((field_name, field_type, parent_type))

    extractor.register_before_field_hook(before_field_hook)
    extractor.extract(EventData)

    assert len(processed_fields) == 3
    field_names = [f[0] for f in processed_fields]
    assert "event_name" in field_names
    assert "event_date" in field_names
    assert "created_at" in field_names


def test_register_after_field_hook() -> None:
    """Test that after_field hook can modify field metadata after extraction."""
    extractor = MetadataExtractor()

    def after_field_hook(field_name: str, field_metadata: FieldMetadata, parent_type: type) -> None:
        if field_name == "event_name":
            field_metadata.categorical = False

    extractor.register_after_field_hook(after_field_hook)
    result = extractor.extract(EventData)

    assert result["event_name"].categorical is False
    assert result["event_date"].categorical is False
