# FAQ

## Can I use my own OpenAI client instance?

Yes. Pass `client=...` to `HarmonyClient`. This lets you configure retries,
proxies, or advanced settings in the underlying client.

## Does openazharmony support Azure OpenAI?

Yes. Use `azure_endpoint` and (when needed) `api_version`. See `AZURE`.

## Can I pass extra OpenAI parameters?

The wrapper exposes a focused set of parameters. If you need additional
options, create and call the underlying client directly.

## Does it support streaming?

Not in the helper methods. Use the underlying client for streaming calls.
