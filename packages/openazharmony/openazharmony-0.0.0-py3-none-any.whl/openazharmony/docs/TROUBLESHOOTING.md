# Troubleshooting

## "Unknown document" when using openazharmony.docs

Make sure the name matches a bundled file. List available docs with:

```bash
python -m openazharmony.docs --list
```

## "model is required when config is not provided"

If you do not pass a `ClientConfig`, you must pass `model` to `HarmonyClient`:

```python
HarmonyClient(api_key="...", model="gpt-4o-mini")
```

## "api_version is required when use_azure_v1_base_url=False"

When you use Azure with `use_azure_v1_base_url=False`, supply `api_version` in
the config or constructor.

## "Client does not support chat.completions" or "responses"

Your `openai` client may be too old or you passed a custom client that does not
expose the expected interfaces.

## ResponseFormat validation errors

Common causes:

- `json_object` with `schema`, `json_schema`, or `strict`
- `json_schema` without a schema
