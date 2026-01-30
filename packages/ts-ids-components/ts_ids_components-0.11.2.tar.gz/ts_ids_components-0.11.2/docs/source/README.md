# Tetra Data Domain-Specific Components Documentation

`ts-ids-components` is home to domain-specific common components for use in programmatic IDSs.
For getting started with programmatic IDS or documentation about creating and using Tetra Data models, see [ids.tetrascience.com](https://ids.tetrascience.com/).

These components can be used in any IDS as a way to build upon existing data models.
When multiple IDSs use the same common components, accessing data becomes more consistent by enabling reuse of search queries and application code.

## Version

v0.11.2

## Install

```shell
pip install ts-ids-components
```

## Quickstart

After installing this package, components can be imported and used in any programmatic IDS definition.

Here is an example of a complete IDS definition which uses the {py:class}`Filter <ts_ids_components.plate_reader.Filter>` component:

```python

from typing import List

from ts_ids_core.schema import (
    IdsElement,
    IdsField,
    Required,
    SchemaExtraMetadataType,
    TetraDataSchema,
)

from ts_ids_components.plate_reader import Filter


class InstrumentMethod(IdsElement):
    """Methods defined for the instrument run"""

    protocol_id: str = IdsField(description="Identifier for the protocol used")
    filter: Filter


class MyPlateReaderModel(TetraDataSchema):
    """IDS demonstrating plate reader components"""

    schema_extra_metadata: SchemaExtraMetadataType = {
        "$id": "https://ids.tetrascience.com/common/plate-reader-component-demo/v1.0.0/schema.json",
        "$schema": "http://json-schema.org/draft-07/schema",
    }

    ids_type: Required[str] = IdsField(
        default="plate-reader-component-demo", alias="@idsType", const=True
    )
    ids_version: Required[str] = IdsField(
        default="v1.0.0", alias="@idsVersion", const=True
    )
    ids_namespace: Required[str] = IdsField(
        default="common", alias="@idsNamespace", const=True
    )

    methods: List[InstrumentMethod]

```

See {external+ts-ids-core:doc}`ts-ids-core export-schema <cli/export_schema>` documentation for an explanation of generating JSON Schema from a programmatic IDS.

<details>
<summary><a>Expand to show JSON schema for `MyPlateReaderModel`</a></summary>

```JSON
{
  "description": "IDS demonstrating plate reader components",
  "type": "object",
  "properties": {
    "@idsType": {
      "const": "plate-reader-component-demo",
      "type": "string"
    },
    "@idsVersion": {
      "const": "v1.0.0",
      "type": "string"
    },
    "@idsNamespace": {
      "const": "common",
      "type": "string"
    },
    "@idsConventionVersion": {
      "description": "IDS convention version. Defined by TetraScience.",
      "const": "v1.0.0",
      "type": "string"
    },
    "methods": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/InstrumentMethod"
      }
    }
  },
  "required": [
    "@idsType",
    "@idsVersion",
    "@idsNamespace",
    "@idsConventionVersion"
  ],
  "additionalProperties": false,
  "$id": "https://ids.tetrascience.com/common/plate-reader-component-demo/v1.0.0/schema.json",
  "$schema": "http://json-schema.org/draft-07/schema",
  "definitions": {
    "ValueUnit": {
      "type": "object",
      "properties": {
        "value": {
          "type": [
            "number",
            "null"
          ]
        },
        "unit": {
          "type": [
            "string",
            "null"
          ]
        }
      },
      "required": [
        "value",
        "unit"
      ],
      "additionalProperties": false
    },
    "Filter": {
      "description": "Optical filter properties",
      "type": "object",
      "properties": {
        "position": {
          "description": "Position of this filter in a container like a filter wheel",
          "type": [
            "string",
            "null"
          ]
        },
        "bandwidth": {
          "description": "The range of frequencies associated with this filter",
          "$ref": "#/definitions/ValueUnit"
        },
        "wavelength": {
          "description": "Characteristic wavelength of this filter",
          "$ref": "#/definitions/ValueUnit"
        }
      },
      "additionalProperties": false
    },
    "InstrumentMethod": {
      "description": "Methods defined for the instrument run",
      "type": "object",
      "properties": {
        "protocol_id": {
          "description": "Identifier for the protocol used",
          "type": "string"
        },
        "filter": {
          "$ref": "#/definitions/Filter"
        }
      },
      "additionalProperties": false
    }
  }
}
```

</details>

## License

License information can be found here: [LICENSE](https://ids.tetrascience.com/ts-ids-components/main/license).
