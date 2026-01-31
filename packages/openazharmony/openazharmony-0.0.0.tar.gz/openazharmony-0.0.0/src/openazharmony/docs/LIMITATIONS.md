# Limitations

- The wrapper only exposes a subset of OpenAI client parameters.
- Streaming responses are not supported by the helper methods.
- Retry/backoff behavior is not included; configure that in the underlying client.
- Azure endpoint inference only works for hostnames ending in `.openai.azure.com`
  with no extra path.
- The wrapper does not validate provider-side parameters beyond the
  `ResponseFormat` contracts.
