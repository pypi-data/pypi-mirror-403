# Python API

## HarmonyClient

The main entry point. You can supply a `ClientConfig` or pass parameters
directly.

```python
from openazharmony import HarmonyClient

client = HarmonyClient(api_key="...", model="gpt-4o-mini")
response = client.chat(question="Say hello")
```

## ClientConfig

```python
from openazharmony import ClientConfig, HarmonyClient

config = ClientConfig(
    api_key="...",
    model="gpt-4o-mini",
)
client = HarmonyClient(config=config)
```

If you provide `azure_endpoint` and set `use_azure_v1_base_url=False`, you must
also set `api_version`.

## Chat and responses

```python
from openazharmony import HarmonyClient, ResponseFormat

client = HarmonyClient(api_key="...", model="gpt-4o-mini")

chat = client.chat(
    question="Summarize the note.",
    response_format=ResponseFormat(type="json_object"),
)

resp = client.responses(
    question="Summarize the note.",
    response_format=ResponseFormat(type="json_object"),
)
```

## Helper builders

Use these helpers when you want to build inputs yourself.

```python
from openazharmony import build_chat_messages, build_responses_input

messages = build_chat_messages(
    agent="You are a helpful assistant.",
    context="Background info.",
    question="What is the summary?",
)

responses_input = build_responses_input(
    context="Background info.",
    question="What is the summary?",
)
```

## ResponseFormat contracts

```python
from openazharmony import ResponseFormat, JsonSchemaSpec

format_json_object = ResponseFormat(type="json_object")

format_json_schema = ResponseFormat(
    type="json_schema",
    json_schema=JsonSchemaSpec(
        name="summary",
        schema={
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
        },
        strict=True,
    ),
)
```
