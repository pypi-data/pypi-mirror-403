# Examples

## Basic chat

```python
from openazharmony import HarmonyClient

client = HarmonyClient(api_key="...", model="gpt-4o-mini")
response = client.chat(question="Say hello.")
print(response)
```

## Responses API with context

```python
from openazharmony import HarmonyClient

client = HarmonyClient(api_key="...", model="gpt-4o-mini")
response = client.responses(
    context="We only answer in short bullets.",
    question="Summarize the note.",
)
print(response)
```

## Structured output

```python
from openazharmony import HarmonyClient, ResponseFormat

client = HarmonyClient(api_key="...", model="gpt-4o-mini")
response = client.chat(
    question="Return JSON with a greeting field.",
    response_format=ResponseFormat(type="json_object"),
)
print(response)
```

## Azure OpenAI

```python
from openazharmony import HarmonyClient

client = HarmonyClient(
    api_key="...",
    model="gpt-4o-mini",
    azure_endpoint="https://your-resource.openai.azure.com",
    api_version="2024-02-15-preview",
    use_azure_v1_base_url=False,
)
response = client.responses(question="Hello from Azure.")
print(response)
```
