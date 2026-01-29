from enum import Enum

from marshmallow import fields

from marshmallow_tagged_union import TagUnionSchema


class AEnum(Enum):
    TYPE_STRING = "string"
    TYPE_NUMBER = "number"


class UnionSchema(TagUnionSchema):
    common_field = fields.String(required=True)
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


def test_children_dump():
    obj = StringMemberSchema().load(
        {"common_field": "common", "field_for_type": "string", "value": "hello"}
    )
    schema = StringMemberSchema()
    result = schema.dump(obj)
    assert result == {
        "common_field": "common",
        "field_for_type": "string",
        "value": "hello",
    }

    obj = NumberMemberSchema().load(
        {"common_field": "common", "field_for_type": "number", "value": 42}
    )
    schema = NumberMemberSchema()
    result = schema.dump(obj)
    assert result == {
        "common_field": "common",
        "field_for_type": "number",
        "value": 42,
    }


def test_dump():
    obj = StringMemberSchema().load(
        {"common_field": "common", "field_for_type": "string", "value": "hello"}
    )
    schema = UnionSchema()
    result = schema.dump(obj)
    assert result == {
        "common_field": "common",
        "field_for_type": "string",
        "value": "hello",
    }

    obj = NumberMemberSchema().load(
        {"common_field": "common", "field_for_type": "number", "value": 42}
    )
    schema = UnionSchema()
    result = schema.dump(obj)
    assert result == {
        "common_field": "common",
        "field_for_type": "number",
        "value": 42,
    }
