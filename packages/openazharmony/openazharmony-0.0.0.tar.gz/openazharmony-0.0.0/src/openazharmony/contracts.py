from __future__ import annotations

from typing import Any, Dict, Mapping, Optional, Union, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

JsonObj = Dict[str, Any]
ToolChoice = Union[str, JsonObj]


class ClientConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    api_key: Optional[str] = None
    model: str
    base_url: Optional[str] = None
    azure_endpoint: Optional[str] = None
    api_version: Optional[str] = None
    use_azure_v1_base_url: bool = True

    @model_validator(mode="after")
    def _validate_azure(self) -> "ClientConfig":
        if (
            self.azure_endpoint
            and not self.use_azure_v1_base_url
            and not self.api_version
        ):
            raise ValueError(
                "api_version is required when use_azure_v1_base_url=False"
            )
        return self


class JsonSchemaSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: Optional[str] = None
    description: Optional[str] = None
    schema_: Optional[JsonObj] = Field(default=None, alias="schema")
    strict: Optional[bool] = None


class ResponseFormat(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: Literal["json_object", "json_schema"]
    json_schema: Optional[JsonSchemaSpec] = None
    schema_: Optional[JsonObj] = Field(default=None, alias="schema")
    strict: Optional[bool] = None

    @model_validator(mode="after")
    def _validate(self) -> "ResponseFormat":
        if self.type == "json_object":
            if (
                self.json_schema is not None
                or self.schema_ is not None
                or self.strict is not None
            ):
                raise ValueError(
                    "json_object cannot include json_schema, schema, or strict"
                )
        if self.type == "json_schema":
            if self.json_schema is None and self.schema_ is None:
                raise ValueError(
                    "json_schema response_format requires json_schema or schema"
                )
        return self

    def to_chat_response_format(self) -> JsonObj:
        if self.type == "json_object":
            return {"type": "json_object"}

        if self.json_schema is not None:
            payload = self.json_schema.model_dump(exclude_none=True, by_alias=True)
        else:
            payload = {}
            if self.schema_ is not None:
                payload["schema"] = self.schema_
            if self.strict is not None:
                payload["strict"] = self.strict

        return {"type": "json_schema", "json_schema": payload}

    def to_responses_text_format(self) -> JsonObj:
        if self.type == "json_object":
            return {"type": "json_object"}

        payload: JsonObj = {"type": "json_schema"}
        if self.schema_ is not None:
            payload["schema"] = self.schema_
        elif self.json_schema is not None and self.json_schema.schema_ is not None:
            payload["schema"] = self.json_schema.schema_

        if self.strict is not None:
            payload["strict"] = self.strict
        elif self.json_schema is not None and self.json_schema.strict is not None:
            payload["strict"] = self.json_schema.strict

        return payload


def normalize_response_format(
    value: Optional[Union[ResponseFormat, Mapping[str, Any]]]
) -> Optional[ResponseFormat]:
    if value is None:
        return None
    if isinstance(value, ResponseFormat):
        return value
    return ResponseFormat.model_validate(value)
