# openazharmony

A small compatibility wrapper around the OpenAI Python client, with pydantic
contracts for response formatting and Azure/OpenAI configuration. It provides
chat and responses helpers with unified response_format handling.

- Unified chat/responses helpers
- Pydantic contracts for response_format
- Azure endpoint inference from base_url

## Install

```bash
pip install openazharmony
```

## Quickstart

```python
from openazharmony import HarmonyClient, ResponseFormat

client = HarmonyClient(
    api_key="...",
    model="gpt-4o-mini",
)

response = client.chat(
    question="Say hello",
    response_format=ResponseFormat(type="json_object"),
)
print(response)
```

## Azure quickstart

```python
from openazharmony import HarmonyClient

client = HarmonyClient(
    api_key="...",
    model="gpt-4o-mini",
    azure_endpoint="https://your-resource.openai.azure.com",
    api_version="2024-02-15-preview",
    use_azure_v1_base_url=False,
)
response = client.responses(question="Say hello")
print(response)
```

## Documentation (bundled)

The package ships with offline documentation that is accessible after install:

```bash
python -m openazharmony.docs --list
python -m openazharmony.docs --show PYTHON
python -m openazharmony.docs --show RESPONSE_FORMATS
python -m openazharmony.docs --show AZURE
python -m openazharmony.docs --show EXAMPLES
python -m openazharmony.docs --show LIMITATIONS
python -m openazharmony.docs --show SECURITY
python -m openazharmony.docs --show TROUBLESHOOTING
python -m openazharmony.docs --show FAQ
python -m openazharmony.docs --show CHANGELOG
python -m openazharmony.docs --write-dir .\openazharmony-docs
```

## Python API (core objects)

### `HarmonyClient`

```python
HarmonyClient(
    config: ClientConfig | None = None,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    azure_endpoint: str | None = None,
    api_version: str | None = None,
    use_azure_v1_base_url: bool = True,
    client: object | None = None,
)
```

### Response format models

```python
ResponseFormat(type="json_object")

ResponseFormat(
    type="json_schema",
    json_schema=JsonSchemaSpec(
        name="summary",
        schema={"type": "object", "properties": {"summary": {"type": "string"}}},
        strict=True,
    ),
)
```
