from typing import Optional, List

import yaml
from pydantic import BaseModel, Field, ConfigDict

from codemie_sdk.models.assistant import MCPServerDetails


def prepare_yaml_content(model_dump: str) -> str:
    yaml.add_representer(str, str_presenter)
    return yaml.dump(
        model_dump,
        sort_keys=False,
        allow_unicode=True,
    )


def str_presenter(dumper, data):
    style = None
    if "\n" in data:
        style = "|"
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


# ------------------- MODELS -------------------


class CustomNodeModel(BaseModel):
    id: str
    custom_node_id: str
    name: Optional[str] = None
    model: Optional[str] = None
    config: Optional[dict] = None


class ToolModel(BaseModel):
    id: Optional[str] = None
    tool: Optional[str] = None
    name: Optional[str] = None
    integration_alias: Optional[str] = None
    tool_args: Optional[dict] = None
    datasource_ids: Optional[List[str]] = None


class AssistantModel(BaseModel):
    id: str
    model: str
    assistant_id: Optional[str] = None
    system_prompt: Optional[str] = None
    datasource_ids: Optional[List[str]] = None
    tools: Optional[List[ToolModel]] = None
    mcp_servers: Optional[List[MCPServerDetails]] = None


class StateModel(BaseModel):
    id: str
    assistant_id: Optional[str] = None
    custom_node_id: Optional[str] = None
    tool_id: Optional[str] = None
    task: Optional[str] = None
    next: Optional[dict] = {"state_id": "end"}
    output_schema: Optional[str] = None
    resolve_dynamic_values_in_prompt: Optional[bool] = True


class WorkflowYamlModel(BaseModel):
    max_concurrency: Optional[int] = None
    enable_summarization_node: Optional[bool] = None
    custom_nodes: List[CustomNodeModel] = Field(default_factory=list)
    tools: List[ToolModel] = Field(default_factory=list)
    assistants: List[AssistantModel] = Field(default_factory=list)
    states: List[StateModel] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")
