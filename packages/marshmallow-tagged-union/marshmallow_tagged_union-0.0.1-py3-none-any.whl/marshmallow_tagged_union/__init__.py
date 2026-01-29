from marshmallow import Schema, ValidationError
from marshmallow.schema import SchemaMeta

TagUnionSchema = None  # type: ignore[assignment]


class TagUnionSchemaMeta(SchemaMeta):
    def __new__(mcs, name, bases, attrs):
        klass = super().__new__(mcs, name, bases, attrs)
        # We want to only override the _deserialize and _serialize methods on
        # the immediate children of TagUnionSchema. Grandchildren should
        # inherit the methods from Schema.
        if TagUnionSchema and TagUnionSchema not in bases:
            klass._deserialize = Schema._deserialize
            klass._serialize = Schema._serialize

        for base in bases:
            base_meta = getattr(base, "Meta", None)
            tag_field = getattr(base_meta, "tag_field", None)

            if tag_field is None:
                continue

            base_meta.tag_mapping[attrs[tag_field]] = klass

        return klass


class TagUnionSchema(Schema, metaclass=TagUnionSchemaMeta):  # noqa: F811
    def _deserialize(self, data, *args, **kwargs):
        tag = data.get(self.Meta.tag_field)
        if tag is None:
            raise ValidationError(
                {self.Meta.tag_field: ["Missing data for required field."]}
            )

        if self.Meta.tag_field in self.fields:
            tag_field = self.fields[self.Meta.tag_field]
            try:
                tag = tag_field.deserialize(tag)
            except ValidationError as e:
                raise ValidationError({self.Meta.tag_field: e.messages}) from e
            if tag is None:
                raise ValidationError(
                    {self.Meta.tag_field: ["Missing data for required field."]}
                )

            schema = self.Meta.tag_mapping.get(tag)
            if schema is None:
                raise ValidationError(f"Unknown tag value {tag}")
            return schema()._deserialize(data, *args, **kwargs)

    def _serialize(self, obj, *args, **kwargs):
        tag_field = obj[self.Meta.tag_field]
        for tag, schema in self.Meta.tag_mapping.items():
            if tag == tag_field:
                return schema().dump(obj, *args, **kwargs)
        raise ValueError(f"Unknown schema {obj.__class__}")

    class Meta:
        tag_field = None
        tag_mapping = {}
