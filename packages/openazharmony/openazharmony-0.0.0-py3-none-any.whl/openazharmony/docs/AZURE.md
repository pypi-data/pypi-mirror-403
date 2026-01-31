# Azure configuration

openazharmony supports Azure OpenAI and can infer Azure endpoints from
`base_url` when possible.

## Using azure_endpoint

```python
from openazharmony import HarmonyClient

client = HarmonyClient(
    api_key="...",
    model="gpt-4o-mini",
    azure_endpoint="https://your-resource.openai.azure.com",
    api_version="2024-02-15-preview",
    use_azure_v1_base_url=False,
)
```

When `use_azure_v1_base_url=False`, openazharmony uses `openai.AzureOpenAI` and
requires `api_version`.

## Using base_url inference

If you pass a base URL that looks like an Azure endpoint, openazharmony will
infer the Azure endpoint automatically:

```python
client = HarmonyClient(
    api_key="...",
    model="gpt-4o-mini",
    base_url="https://your-resource.openai.azure.com",
)
```

This inference only runs when the host ends with `.openai.azure.com` and the
URL has no extra path segments.

## Azure v1-style base URL

With `use_azure_v1_base_url=True` (default), openazharmony will call
`openai.OpenAI` and set the base URL to:

```
{azure_endpoint}/openai/v1/
```
