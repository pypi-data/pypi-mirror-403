from __future__ import annotations

from typing import Any, List, Optional, Sequence
from urllib.parse import urlparse

from .contracts import ClientConfig, JsonObj, ToolChoice, normalize_response_format


def build_chat_messages(
    *,
    agent: str,
    context: Optional[str],
    question: Optional[str],
) -> List[JsonObj]:
    messages: List[JsonObj] = [{"role": "system", "content": str(agent)}]
    if context:
        messages.append({"role": "user", "content": str(context)})
    if question:
        messages.append({"role": "user", "content": str(question)})
    return messages


def build_responses_input(
    *,
    context: Optional[str],
    question: Optional[str],
) -> Any:
    parts: List[JsonObj] = []
    if context:
        parts.append({"role": "user", "content": str(context)})
    if question:
        parts.append({"role": "user", "content": str(question)})

    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]["content"]
    return parts


def _compact_dict(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


def _infer_azure_endpoint(base_url: Optional[str]) -> Optional[str]:
    if not base_url:
        return None
    parsed = urlparse(base_url)
    if not parsed.scheme:
        return None
    host = (parsed.hostname or "").lower()
    if not host.endswith(".openai.azure.com"):
        return None
    if parsed.path and parsed.path not in ("", "/"):
        return None
    return base_url.rstrip("/")


def _build_openai_client(config: ClientConfig) -> Any:
    import importlib

    openai = importlib.import_module("openai")

    azure_endpoint = config.azure_endpoint or _infer_azure_endpoint(config.base_url)

    if azure_endpoint:
        if config.use_azure_v1_base_url:
            base_url = f"{azure_endpoint.rstrip('/')}/openai/v1/"
            return openai.OpenAI(api_key=config.api_key, base_url=base_url)

        return openai.AzureOpenAI(
            api_key=config.api_key,
            api_version=config.api_version,
            azure_endpoint=azure_endpoint,
        )

    return openai.OpenAI(api_key=config.api_key, base_url=config.base_url)


class HarmonyClient:
    def __init__(
        self,
        *,
        config: Optional[ClientConfig] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        azure_endpoint: Optional[str] = None,
        api_version: Optional[str] = None,
        use_azure_v1_base_url: bool = True,
        client: Optional[Any] = None,
    ) -> None:
        if config is None:
            if model is None:
                raise ValueError("model is required when config is not provided")
            config = ClientConfig(
                api_key=api_key,
                model=model,
                base_url=base_url,
                azure_endpoint=azure_endpoint,
                api_version=api_version,
                use_azure_v1_base_url=use_azure_v1_base_url,
            )

        self.config = config
        self.client = client or _build_openai_client(config)

    def chat(
        self,
        *,
        messages: Optional[Sequence[JsonObj]] = None,
        question: Optional[str] = None,
        agent: str = "You are a helpful assistant.",
        temperature: Optional[float] = None,
        context: Optional[str] = None,
        max_tokens: Optional[int] = None,
        functions: Optional[List[JsonObj]] = None,
        function_call: Optional[JsonObj] = None,
        response_format: Optional[dict[str, Any]] = None,
        model: Optional[str] = None,
    ) -> Any:
        if messages is None:
            messages = build_chat_messages(
                agent=agent,
                context=context,
                question=question,
            )

        fmt = normalize_response_format(response_format)

        kwargs = _compact_dict(
            {
                "model": model or self.config.model,
                "messages": list(messages),
                "temperature": temperature,
                "max_tokens": max_tokens,
                "functions": functions,
                "function_call": function_call,
            }
        )
        if fmt is not None:
            kwargs["response_format"] = fmt.to_chat_response_format()

        if not hasattr(self.client, "chat"):
            raise AttributeError("Client does not support chat.completions")

        return self.client.chat.completions.create(**kwargs)

    def responses(
        self,
        *,
        input: Optional[Any] = None,
        question: Optional[str] = None,
        agent: str = "You are a helpful assistant.",
        temperature: Optional[float] = None,
        context: Optional[str] = None,
        max_output_tokens: Optional[int] = None,
        tools: Optional[List[JsonObj]] = None,
        tool_choice: Optional[ToolChoice] = None,
        response_format: Optional[dict[str, Any]] = None,
        previous_response_id: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Any:
        if input is None:
            input = build_responses_input(context=context, question=question)

        fmt = normalize_response_format(response_format)

        kwargs = _compact_dict(
            {
                "model": model or self.config.model,
                "input": input,
                "instructions": str(agent),
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            }
        )
        if tools is not None:
            kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
        if fmt is not None:
            kwargs["text"] = {"format": fmt.to_responses_text_format()}
        if previous_response_id is not None:
            kwargs["previous_response_id"] = previous_response_id

        if not hasattr(self.client, "responses"):
            raise AttributeError("Client does not support responses")

        return self.client.responses.create(**kwargs)
