"""Tests for final_types configuration in MetadataExtractor."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated

import pytest

from fields_metadata.annotations import FinalType, final_type
from fields_metadata.extractor import MetadataExtractor


@dataclass
class Money:
    """Money value object - treat as final."""

    amount: Decimal
    currency: str


@dataclass
class Coordinates:
    """Geographic coordinates - treat as final."""

    latitude: float
    longitude: float


@dataclass
class Address:
    """Address with money and coordinates."""

    street: str
    city: str
    postal_code: str
    location: Coordinates


@dataclass
class Product:
    """Product with price and location."""

    name: str
    price: Money
    origin: Address


def test_without_final_types_expands_all():
    """Test that without final_types, all composite types are expanded."""
    extractor = MetadataExtractor()
    metadata = extractor.extract(Product)

    # Without final_types, Money and Coordinates are expanded
    assert "price" in metadata
    assert metadata["price"].composite is True
    assert "price.amount" in metadata
    assert "price.currency" in metadata

    assert "origin" in metadata
    assert metadata["origin"].composite is True
    assert "origin.location" in metadata
    assert metadata["origin.location"].composite is True
    assert "origin.location.latitude" in metadata
    assert "origin.location.longitude" in metadata


def test_with_final_types_stops_expansion():
    """Test that final_types prevents recursive extraction."""
    extractor = MetadataExtractor(final_types={Money, Coordinates})
    metadata = extractor.extract(Product)

    # Money fields should NOT be expanded
    assert "price" in metadata
    assert metadata["price"].composite is False  # Treated as final
    assert metadata["price"].field_type == Money
    assert "price.amount" not in metadata
    assert "price.currency" not in metadata

    # Address is still expanded
    assert "origin" in metadata
    assert metadata["origin"].composite is True
    assert "origin.street" in metadata
    assert "origin.city" in metadata

    # But Coordinates within Address should NOT be expanded
    assert "origin.location" in metadata
    assert metadata["origin.location"].composite is False  # Treated as final
    assert metadata["origin.location"].field_type == Coordinates
    assert "origin.location.latitude" not in metadata
    assert "origin.location.longitude" not in metadata


def test_final_types_with_list():
    """Test that final_types works with multivalued fields."""

    @dataclass
    class Transaction:
        description: str
        amounts: list[Money]

    extractor = MetadataExtractor(final_types={Money})
    metadata = extractor.extract(Transaction)

    assert "amounts" in metadata
    assert metadata["amounts"].multivalued is True
    assert metadata["amounts"].items_type == Money
    assert metadata["amounts"].effective_type == Money
    # Money is treated as final, so it should not be composite
    assert metadata["amounts"].composite is False

    # No Money fields should be extracted
    assert "amounts.amount" not in metadata
    assert "amounts.currency" not in metadata


def test_final_types_empty_set():
    """Test that empty final_types set works like default behavior."""
    extractor1 = MetadataExtractor()
    extractor2 = MetadataExtractor(final_types=set())

    metadata1 = extractor1.extract(Product)
    metadata2 = extractor2.extract(Product)

    # Both should have the same fields
    assert set(metadata1.keys()) == set(metadata2.keys())

    # Both should expand Money
    assert "price.amount" in metadata1
    assert "price.amount" in metadata2


def test_final_types_with_optional():
    """Test that final_types works with optional fields."""

    @dataclass
    class Order:
        product_name: str
        discount_amount: Money | None = None

    extractor = MetadataExtractor(final_types={Money})
    metadata = extractor.extract(Order)

    assert "discount_amount" in metadata
    assert metadata["discount_amount"].optional is True
    assert metadata["discount_amount"].field_type == Money
    assert metadata["discount_amount"].composite is False

    # Money fields should not be extracted
    assert "discount_amount.amount" not in metadata
    assert "discount_amount.currency" not in metadata


def test_final_types_preserves_field_type():
    """Test that final_types preserves the correct field_type."""

    @dataclass
    class Invoice:
        total: Money
        location: Coordinates

    extractor = MetadataExtractor(final_types={Money, Coordinates})
    metadata = extractor.extract(Invoice)

    # Field types should be the actual types, not simplified
    assert metadata["total"].field_type == Money
    assert metadata["total"].effective_type == Money
    assert metadata["location"].field_type == Coordinates
    assert metadata["location"].effective_type == Coordinates


@pytest.mark.parametrize(
    "wrapper_type,field_name,expected_multivalued,expected_optional",
    [
        ("bare", "price", False, False),
        ("list", "tags", True, False),
        ("optional", "rating", False, True),
    ],
)
def test_final_type_decorator_with_wrappers(
    wrapper_type: str, field_name: str, expected_multivalued: bool, expected_optional: bool
) -> None:
    """Test that @final_type decorator works with different type wrappers."""

    @final_type
    @dataclass
    class FinalClass:
        field1: str
        field2: str

    if wrapper_type == "bare":

        @dataclass
        class Container:
            name: str
            price: FinalClass

    elif wrapper_type == "list":

        @dataclass
        class Container:
            title: str
            tags: list[FinalClass]

    else:

        @dataclass
        class Container:
            content: str
            rating: FinalClass | None = None

    extractor = MetadataExtractor()
    metadata = extractor.extract(Container)

    assert field_name in metadata
    assert metadata[field_name].multivalued == expected_multivalued
    assert metadata[field_name].optional == expected_optional
    assert metadata[field_name].composite is False

    assert f"{field_name}.field1" not in metadata
    assert f"{field_name}.field2" not in metadata


@pytest.mark.parametrize(
    "wrapper_type,field_name,expected_multivalued,expected_optional",
    [
        ("bare", "price", False, False),
        ("list", "labels", True, False),
        ("optional", "author", False, True),
    ],
)
def test_final_type_annotation_with_wrappers(
    wrapper_type: str, field_name: str, expected_multivalued: bool, expected_optional: bool
) -> None:
    """Test that FinalType annotation works with different type wrappers."""

    @dataclass
    class FinalClass:
        field1: str
        field2: str

    if wrapper_type == "bare":

        @dataclass
        class Container:
            name: str
            price: Annotated[FinalClass, FinalType()]

    elif wrapper_type == "list":

        @dataclass
        class Container:
            title: str
            labels: list[Annotated[FinalClass, FinalType()]]

    else:

        @dataclass
        class Container:
            title: str
            author: Annotated[FinalClass, FinalType()] | None = None

    extractor = MetadataExtractor()
    metadata = extractor.extract(Container)

    assert field_name in metadata
    assert metadata[field_name].multivalued == expected_multivalued
    assert metadata[field_name].optional == expected_optional
    assert metadata[field_name].composite is False

    assert f"{field_name}.field1" not in metadata
    assert f"{field_name}.field2" not in metadata


def test_final_type_all_three_methods():
    """Test that all three methods (constructor, decorator, annotation) work together."""

    @dataclass
    class ConstructorFinal:
        value: str

    @final_type
    @dataclass
    class DecoratorFinal:
        value: str

    @dataclass
    class AnnotationFinal:
        value: str

    @dataclass
    class Container:
        a: ConstructorFinal
        b: DecoratorFinal
        c: Annotated[AnnotationFinal, FinalType()]

    extractor = MetadataExtractor(final_types={ConstructorFinal})
    metadata = extractor.extract(Container)

    # All three should be treated as final
    assert metadata["a"].composite is False
    assert "a.value" not in metadata

    assert metadata["b"].composite is False
    assert "b.value" not in metadata

    assert metadata["c"].composite is False
    assert "c.value" not in metadata


def test_final_type_annotation_overrides_normal_behavior():
    """Test that FinalType annotation works even for types that would normally expand."""

    @dataclass
    class NormallyExpanded:
        field1: str
        field2: int

    @dataclass
    class Container:
        normal: NormallyExpanded
        annotated_final: Annotated[NormallyExpanded, FinalType()]

    extractor = MetadataExtractor()
    metadata = extractor.extract(Container)

    # normal should be expanded
    assert metadata["normal"].composite is True
    assert "normal.field1" in metadata
    assert "normal.field2" in metadata

    # annotated_final should NOT be expanded
    assert metadata["annotated_final"].composite is False
    assert "annotated_final.field1" not in metadata
    assert "annotated_final.field2" not in metadata


def test_final_type_decorator_can_be_combined_with_constructor():
    """Test that decorator and constructor parameter work together."""

    @final_type
    @dataclass
    class DecoratedType:
        value: str

    @dataclass
    class ConstructorType:
        value: str

    @dataclass
    class Container:
        a: DecoratedType
        b: ConstructorType

    # Even though we only pass ConstructorType to final_types,
    # DecoratedType should still be final due to decorator
    extractor = MetadataExtractor(final_types={ConstructorType})
    metadata = extractor.extract(Container)

    assert metadata["a"].composite is False
    assert "a.value" not in metadata

    assert metadata["b"].composite is False
    assert "b.value" not in metadata
