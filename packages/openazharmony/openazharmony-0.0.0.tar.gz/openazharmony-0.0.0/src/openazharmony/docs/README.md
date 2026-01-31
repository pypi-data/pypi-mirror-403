# openazharmony documentation

This documentation suite is bundled inside the installed package so it is
available offline.

## Access after installation

List available docs:

```bash
python -m openazharmony.docs --list
```

Print a document to stdout:

```bash
python -m openazharmony.docs --show PYTHON
```

Write all docs to a folder:

```bash
python -m openazharmony.docs --write-dir .\openazharmony-docs
```

## Document map

- INSTALL: installation and requirements
- PYTHON: API usage and core objects
- RESPONSE_FORMATS: response_format contracts and examples
- AZURE: Azure/OpenAI configuration notes
- EXAMPLES: ready-to-run snippets
- LIMITATIONS: design tradeoffs and constraints
- SECURITY: privacy and data-handling notes
- TROUBLESHOOTING: common problems and fixes
- FAQ: common questions
- CHANGELOG: notable changes by release

## Overview

openazharmony is a small compatibility wrapper around the OpenAI Python client.
It provides a single client with helpers for chat and responses calls plus
pydantic contracts for response_format, so you can share the same settings
across both APIs.

See the documents above for details and examples.
