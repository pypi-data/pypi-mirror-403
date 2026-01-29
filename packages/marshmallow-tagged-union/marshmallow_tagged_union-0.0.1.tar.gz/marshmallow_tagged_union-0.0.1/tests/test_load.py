from enum import Enum

import pytest
from marshmallow import ValidationError, fields

from marshmallow_tagged_union import TagUnionSchema


class AEnum(Enum):
    TYPE_STRING = "string"
    TYPE_NUMBER = "number"


class UnionSchema(TagUnionSchema):
    common_field_1 = fields.String(required=True)
    common_field_2 = fields.Integer(required=True)
    common_field_enum = fields.Enum(AEnum, required=False, by_value=True)
    field_for_type = fields.Enum(AEnum, required=True, by_value=True)

    class Meta(TagUnionSchema.Meta):
        tag_field = "field_for_type"


class StringMemberSchema(UnionSchema):
    field_for_type = AEnum.TYPE_STRING
    value = fields.String(required=True)

    class Meta(UnionSchema.Meta):
        pass


class NumberMemberSchema(UnionSchema):
    field_for_type = AEnum.TYPE_NUMBER
    value = fields.Integer(required=True)

    class Meta(UnionSchema.Meta):
        pass


def test_children_load():
    data = {
        "common_field_1": "common",
        "common_field_2": 1,
        "field_for_type": "string",
        "value": "hello",
    }
    schema = StringMemberSchema()
    result = schema.load(data)
    assert result == {
        "common_field_1": "common",
        "common_field_2": 1,
        "field_for_type": AEnum.TYPE_STRING,
        "value": "hello",
    }

    data = {
        "common_field_1": "common",
        "common_field_2": 1,
        "field_for_type": "number",
        "value": 42,
    }
    schema = NumberMemberSchema()
    result = schema.load(data)
    assert result == {
        "common_field_1": "common",
        "common_field_2": 1,
        "field_for_type": AEnum.TYPE_NUMBER,
        "value": 42,
    }


def test_load():
    data = {
        "common_field_1": "common",
        "common_field_2": 1,
        "field_for_type": "string",
        "value": "hello",
    }
    schema = UnionSchema()
    result = schema.load(data)
    assert result == {
        "common_field_1": "common",
        "common_field_2": 1,
        "field_for_type": AEnum.TYPE_STRING,
        "value": "hello",
    }

    data = {
        "common_field_1": "common",
        "common_field_2": 1,
        "field_for_type": "number",
        "value": 42,
    }
    schema = UnionSchema()
    result = schema.load(data)
    assert result == {
        "common_field_1": "common",
        "common_field_2": 1,
        "field_for_type": AEnum.TYPE_NUMBER,
        "value": 42,
    }


def test_load_missing_common_field():
    data = {
        "common_field_2": 1,
        "field_for_type": "string",
        "value": "hello",
    }
    schema = UnionSchema()
    with pytest.raises(ValidationError) as exc_info:
        schema.load(data)
    assert exc_info.value.field_name == "_schema"
    assert exc_info.value.messages == {
        "common_field_1": ["Missing data for required field."]
    }


def test_load_missing_tag():
    data = {"common_field_1": "common", "common_field_2": 1, "value": "hello"}
    schema = UnionSchema()
    with pytest.raises(ValidationError) as exc_info:
        schema.load(data)
    assert exc_info.value.field_name == "_schema"
    assert exc_info.value.messages == {
        "field_for_type": ["Missing data for required field."]
    }


def test_load_invalid_enum_in_common_field():
    data = {
        "common_field_1": "common",
        "common_field_2": 1,
        "common_field_enum": "invalid_enum",
        "field_for_type": "string",
        "value": "hello",
    }
    schema = UnionSchema()
    with pytest.raises(ValidationError) as exc_info:
        schema.load(data)
    assert exc_info.value.field_name == "_schema"
    assert exc_info.value.messages == {
        "common_field_enum": ["Must be one of: string, number."]
    }


def test_load_invalid_tag():
    data = {
        "common_field_1": "common",
        "common_field_2": 1,
        "field_for_type": "invalid",
        "value": "hello",
    }
    schema = UnionSchema()
    with pytest.raises(ValidationError) as exc_info:
        schema.load(data)
    assert exc_info.value.field_name == "_schema"
    assert exc_info.value.messages == {
        "field_for_type": ["Must be one of: string, number."]
    }


def test_load_invalid_child_schema_number():
    data = {
        "common_field_1": "common",
        "common_field_2": 1,
        "field_for_type": "number",
        "value": "not_a_number",
    }
    schema = UnionSchema()
    with pytest.raises(ValidationError) as exc_info:
        schema.load(data)
    assert exc_info.value.field_name == "_schema"
    assert exc_info.value.messages == {"value": ["Not a valid integer."]}
