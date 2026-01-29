# marshmallow-tagged-union

[![PyPI version](https://badge.fury.io/py/marshmallow-tagged-union.svg)](https://badge.fury.io/py/marshmallow-tagged-union)

Provide support for tagged unions (discriminated unions) in [marshmallow](https://marshmallow.readthedocs.io/) schemas.

## Installation

```bash
pip install marshmallow-tagged-union
```

## What is a Tagged Union?

A tagged union (also known as a discriminated union or variant) is a data structure that can hold values of different types, with a "tag" field that indicates which type is currently stored. This is useful for modeling polymorphic data where you have a common base structure with type-specific fields.

## Usage

### Basic Example

```python
from enum import Enum
from marshmallow import fields
from marshmallow_tagged_union import TagUnionSchema


class ShapeType(Enum):
    CIRCLE = "circle"
    RECTANGLE = "rectangle"


# Define the base union schema
class ShapeSchema(TagUnionSchema):
    name = fields.String(required=True)  # Common field
    shape_type = fields.Enum(ShapeType, required=True, by_value=True)
    
    class Meta(TagUnionSchema.Meta):
        tag_field = "shape_type"  # Field that discriminates the type


# Define specific union members
class CircleSchema(ShapeSchema):
    shape_type = ShapeType.CIRCLE
    radius = fields.Float(required=True)
    
    class Meta(ShapeSchema.Meta):
        pass


class RectangleSchema(ShapeSchema):
    shape_type = ShapeType.RECTANGLE
    width = fields.Float(required=True)
    height = fields.Float(required=True)
    
    class Meta(ShapeSchema.Meta):
        pass


# Usage: Deserialize (load)
schema = ShapeSchema()
circle_data = {
    "name": "My Circle",
    "shape_type": "circle",
    "radius": 5.0
}
result = schema.load(circle_data)
# Returns: {'name': 'My Circle', 'shape_type': <ShapeType.CIRCLE: 'circle'>, 'radius': 5.0}

# Usage: Serialize (dump)
rectangle_data = {
    "name": "My Rectangle",
    "shape_type": ShapeType.RECTANGLE,
    "width": 10.0,
    "height": 20.0
}
result = schema.dump(rectangle_data)
# Returns: {'name': 'My Rectangle', 'shape_type': 'rectangle', 'width': 10.0, 'height': 20.0}
```

### Key Concepts

1. **Base Schema**: Inherit from `TagUnionSchema` and define common fields shared by all union members
2. **Tag Field**: Set `tag_field` in the `Meta` class to specify which field discriminates between types
3. **Member Schemas**: Inherit from the base schema and:
   - Set the tag field to a specific value (e.g., `shape_type = ShapeType.CIRCLE`)
   - Add type-specific fields (e.g., `radius` for circles)

### Features

- **Automatic type resolution**: The correct schema is automatically selected based on the tag field value during deserialization
- **Validation**: All marshmallow validation features work on both common and type-specific fields
- **Common fields**: Define fields once in the base schema and they're available in all union members
- **Type safety**: Use Python enums for type-safe tag values

## Development

### Install in Development Mode

```bash
pip install --editable ".[dev]"
```

### Run Tests

```bash
pytest
```

### Building

To build the distribution packages:

```bash
pip install build
python -m build
```

This will create both wheel (`.whl`) and source distribution (`.tar.gz`) files in the `dist/` directory.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
