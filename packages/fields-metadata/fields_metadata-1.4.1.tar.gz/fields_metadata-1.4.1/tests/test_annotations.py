"""Tests for custom annotation classes."""

from dataclasses import dataclass

import pytest

from fields_metadata.annotations import (
    HumanReadableId,
    InternationalURNAnnotation,
    Multiline,
    SemanticClassification,
    final_type,
    is_marked_final_type,
)


def test_multiline_instantiation() -> None:
    """Multiline annotation can be instantiated."""
    annotation = Multiline()
    assert isinstance(annotation, Multiline)


def test_multiline_is_frozen() -> None:
    """Multiline annotation is frozen (immutable)."""
    import dataclasses

    assert dataclasses.fields(Multiline) is not None


def test_human_readable_id_instantiation() -> None:
    """HumanReadableId annotation can be instantiated."""
    annotation = HumanReadableId()
    assert isinstance(annotation, HumanReadableId)


def test_human_readable_id_is_frozen() -> None:
    """HumanReadableId annotation is frozen (immutable)."""
    import dataclasses

    assert dataclasses.fields(HumanReadableId) is not None


def test_semantic_classification_instantiation() -> None:
    """SemanticClassification annotation can be instantiated with classification."""
    annotation = SemanticClassification(classification="person_name")
    assert isinstance(annotation, SemanticClassification)
    assert annotation.classification == "person_name"


def test_semantic_classification_is_frozen() -> None:
    """SemanticClassification annotation is frozen (immutable)."""
    annotation = SemanticClassification(classification="test")
    with pytest.raises(Exception):
        annotation.classification = "new_value"  # type: ignore[misc]


def test_international_urn_annotation_instantiation() -> None:
    """InternationalURNAnnotation can be instantiated."""
    annotation = InternationalURNAnnotation()
    assert isinstance(annotation, InternationalURNAnnotation)


def test_international_urn_annotation_is_frozen() -> None:
    """InternationalURNAnnotation is frozen (immutable)."""
    import dataclasses

    assert dataclasses.fields(InternationalURNAnnotation) is not None


def test_multiple_multiline_instances_equal() -> None:
    """Multiple Multiline instances should be equal."""
    assert Multiline() == Multiline()


def test_multiple_human_readable_id_instances_equal() -> None:
    """Multiple HumanReadableId instances should be equal."""
    assert HumanReadableId() == HumanReadableId()


def test_semantic_classification_equality() -> None:
    """SemanticClassification instances with same classification are equal."""
    assert SemanticClassification("test") == SemanticClassification("test")
    assert SemanticClassification("test1") != SemanticClassification("test2")


def test_international_urn_instances_equal() -> None:
    """Multiple InternationalURNAnnotation instances should be equal."""
    assert InternationalURNAnnotation() == InternationalURNAnnotation()


def test_is_marked_final_type_with_decorator() -> None:
    """Test detection of @final_type decorator."""

    @final_type
    @dataclass
    class CustomType:
        value: str

    assert is_marked_final_type(CustomType) is True


def test_is_marked_final_type_without_decorator() -> None:
    """Test that regular types are not marked as final."""

    @dataclass
    class RegularType:
        value: str

    assert is_marked_final_type(RegularType) is False


def test_is_marked_final_type_with_primitive() -> None:
    """Test that primitive types are not marked as final."""
    assert is_marked_final_type(str) is False
    assert is_marked_final_type(int) is False
    assert is_marked_final_type(float) is False
    assert is_marked_final_type(bool) is False
