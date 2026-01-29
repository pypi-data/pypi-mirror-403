"""
Tests for complex types and edge cases.
"""

import pytest
from typing import List, Dict, Set, Tuple, Optional, Union, Literal, Any, FrozenSet, Annotated
from decimal import Decimal
from uuid import UUID, uuid4
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field

from pydantic_variants import variants, basic_variant_pipeline
from pydantic_variants.transformers import FilterFields, SwitchVariant


class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class TestComplexTypes:
    """Tests for complex type handling."""

    def test_literal_types_preserved(self):
        """Literal types are preserved in variants."""

        @variants(basic_variant_pipeline("Input"))
        class Config(BaseModel):
            mode: Literal["read", "write", "admin"]
            level: Literal[1, 2, 3]

        # Literal types should work
        config = Config.Input(mode="read", level=1)  # type: ignore[attr-defined]
        assert config.mode == "read"
        assert config.level == 1

        # Invalid values should fail
        with pytest.raises(Exception):
            Config.Input(mode="invalid", level=1)  # type: ignore[attr-defined]

    def test_enum_types_preserved(self):
        """Enum types are preserved in variants."""

        @variants(basic_variant_pipeline("Input"))
        class User(BaseModel):
            name: str
            status: Status

        user = User.Input(name="John", status=Status.ACTIVE)  # type: ignore[attr-defined]
        assert user.status == Status.ACTIVE

        # String coercion should work
        user2 = User.Input(name="Jane", status="inactive")  # type: ignore[attr-defined]
        assert user2.status == Status.INACTIVE

    def test_nested_collections(self):
        """Nested collection types are handled."""

        @variants(basic_variant_pipeline("Input"))
        class Data(BaseModel):
            matrix: List[List[int]]
            nested_dict: Dict[str, Dict[str, int]]
            mixed: List[Dict[str, List[str]]]

        data = Data.Input(matrix=[[1, 2], [3, 4]], nested_dict={"a": {"x": 1}, "b": {"y": 2}}, mixed=[{"keys": ["a", "b"]}])  # type: ignore[attr-defined]

        assert data.matrix == [[1, 2], [3, 4]]
        assert data.nested_dict["a"]["x"] == 1

    def test_tuple_types(self):
        """Tuple types are preserved."""

        @variants(basic_variant_pipeline("Input"))
        class Coordinate(BaseModel):
            point: Tuple[float, float]
            rgb: Tuple[int, int, int]

        coord = Coordinate.Input(point=(1.5, 2.5), rgb=(255, 128, 0))  # type: ignore[attr-defined]
        assert coord.point == (1.5, 2.5)
        assert coord.rgb == (255, 128, 0)

    def test_frozenset_type(self):
        """FrozenSet types work."""

        @variants(basic_variant_pipeline("Input"))
        class Tags(BaseModel):
            immutable_tags: FrozenSet[str]

        tags = Tags.Input(immutable_tags=frozenset(["a", "b"]))  # type: ignore[attr-defined]
        assert "a" in tags.immutable_tags

    def test_uuid_type(self):
        """UUID types are preserved."""

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["id"])))
        class Entity(BaseModel):
            id: UUID = Field(default_factory=uuid4)
            name: str

        # id should be filtered
        assert "id" not in Entity.Input.model_fields  # type: ignore[attr-defined]

        entity = Entity.Input(name="Test")  # type: ignore[attr-defined]
        assert entity.name == "Test"

    def test_decimal_type(self):
        """Decimal types are handled."""

        @variants(basic_variant_pipeline("Input"))
        class Product(BaseModel):
            price: Decimal
            discount: Decimal = Decimal("0.00")

        product = Product.Input(price=Decimal("19.99"))  # type: ignore[attr-defined]
        assert product.price == Decimal("19.99")

    def test_datetime_types(self):
        """DateTime and Date types work."""

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["created_at"])))
        class Event(BaseModel):
            name: str
            event_date: date
            created_at: datetime

        from datetime import date as date_type

        event = Event.Input(name="Conference", event_date=date_type(2024, 6, 15))  # type: ignore[attr-defined]
        assert event.event_date == date_type(2024, 6, 15)

    def test_any_type(self):
        """Any type is preserved."""

        @variants(basic_variant_pipeline("Input"))
        class Flexible(BaseModel):
            data: Any
            metadata: Dict[str, Any] = {}

        flex = Flexible.Input(data=[1, "two", 3.0], metadata={"key": [1, 2]})  # type: ignore[attr-defined]
        assert flex.data == [1, "two", 3.0]

    def test_complex_union_types(self):
        """Complex Union types are handled."""

        @variants(basic_variant_pipeline("Input"))
        class Response(BaseModel):
            result: Union[str, int, List[str], None]
            error: Union[str, Dict[str, str], None] = None

        resp1 = Response.Input(result="success")  # type: ignore[attr-defined]
        resp2 = Response.Input(result=42)  # type: ignore[attr-defined]
        resp3 = Response.Input(result=["a", "b"])  # type: ignore[attr-defined]
        resp4 = Response.Input(result=None)  # type: ignore[attr-defined]

        assert resp1.result == "success"
        assert resp2.result == 42
        assert resp3.result == ["a", "b"]
        assert resp4.result is None

    def test_pipe_union_syntax(self):
        """X | Y union syntax is handled."""

        @variants(basic_variant_pipeline("Input"))
        class Data(BaseModel):
            value: str | int | None
            items: list[str] | None = None

        data1 = Data.Input(value="test")  # type: ignore[attr-defined]
        data2 = Data.Input(value=42)  # type: ignore[attr-defined]
        data3 = Data.Input(value=None)  # type: ignore[attr-defined]

        assert data1.value == "test"
        assert data2.value == 42
        assert data3.value is None

    def test_nested_optional(self):
        """Nested Optional types work."""

        @variants(basic_variant_pipeline("Input"))
        class User(BaseModel):
            name: str
            profile: Optional[Dict[str, Optional[str]]] = None

        user = User.Input(name="John", profile={"bio": "Hello", "website": None})  # type: ignore[attr-defined]
        assert user.profile["bio"] == "Hello"
        assert user.profile["website"] is None

    def test_constrained_types(self):
        """Constrained types are preserved."""
        from pydantic import PositiveInt, NegativeFloat, constr, conint

        @variants(basic_variant_pipeline("Input"))
        class Constrained(BaseModel):
            positive: PositiveInt
            negative: NegativeFloat
            short_str: Annotated[str, constr(min_length=1, max_length=10)] = "default"  # type: ignore[assignment]
            bounded_int: Annotated[int, conint(ge=0, le=100)] = 50  # type: ignore[assignment]

        item = Constrained.Input(positive=5, negative=-1.5)  # type: ignore[attr-defined]
        assert item.positive == 5

        with pytest.raises(Exception):
            Constrained.Input(positive=-1, negative=-1.5)  # type: ignore[attr-defined]

    def test_switch_variant_with_dict_model_values(self):
        """SwitchVariant works with Dict[str, Model]."""

        @variants(basic_variant_pipeline("Input"))
        class Item(BaseModel):
            name: str

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class Container(BaseModel):
            items: Dict[str, Item]
            optional_items: Optional[Dict[str, Item]] = None

        # Dict values should use Item.Input
        items_type = Container.Input.model_fields["items"].annotation  # type: ignore[attr-defined]
        assert items_type.__args__[1] is Item.Input  # type: ignore[attr-defined]

    def test_set_with_models(self):
        """Set types work (though models must be hashable)."""

        @variants(basic_variant_pipeline("Input"))
        class Tags(BaseModel):
            values: Set[str]

        tags = Tags.Input(values={"a", "b", "c"})  # type: ignore[attr-defined]
        assert "a" in tags.values
        assert len(tags.values) == 3
