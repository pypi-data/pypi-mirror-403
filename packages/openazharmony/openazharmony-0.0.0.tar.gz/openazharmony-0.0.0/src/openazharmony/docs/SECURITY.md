# Security

- Treat API keys as secrets. Do not commit them to source control.
- Avoid logging full request/response payloads if they contain sensitive data.
- openazharmony does not send telemetry; requests go directly to the provider
  via the OpenAI Python client.
- Review your provider's data retention and logging policies for compliance.
