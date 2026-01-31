# Response formats

openazharmony wraps response_format handling so the same contract works across
chat and responses calls.

## json_object

```python
from openazharmony import HarmonyClient, ResponseFormat

client = HarmonyClient(api_key="...", model="gpt-4o-mini")
format_json = ResponseFormat(type="json_object")

chat = client.chat(
    question="Return JSON.",
    response_format=format_json,
)

resp = client.responses(
    question="Return JSON.",
    response_format=format_json,
)
```

## json_schema

You can provide `json_schema` as a structured object or pass `schema`/`strict`
directly.

```python
from openazharmony import HarmonyClient, ResponseFormat, JsonSchemaSpec

client = HarmonyClient(api_key="...", model="gpt-4o-mini")

format_schema = ResponseFormat(
    type="json_schema",
    json_schema=JsonSchemaSpec(
        name="answer",
        schema={
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
        },
        strict=True,
    ),
)

chat = client.chat(
    question="Answer in JSON.",
    response_format=format_schema,
)
```

Equivalent inline schema:

```python
format_schema = ResponseFormat(
    type="json_schema",
    schema={
        "type": "object",
        "properties": {"answer": {"type": "string"}},
        "required": ["answer"],
    },
    strict=True,
)
```

## Validation rules

- `type="json_object"` cannot include `json_schema`, `schema`, or `strict`.
- `type="json_schema"` must include `json_schema` or `schema`.
