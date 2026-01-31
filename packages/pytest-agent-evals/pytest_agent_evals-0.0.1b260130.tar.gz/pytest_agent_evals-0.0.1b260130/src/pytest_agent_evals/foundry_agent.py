from typing import List, Union
from azure.identity import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.ai.evaluation._converters._models import _BUILT_IN_DESCRIPTIONS, _BUILT_IN_PARAMS
from openai.types.responses import ResponseOutputItem
import json
from .types import AgentResponse

class FoundryAgentRunner:
    """
    Runner for Microsoft Foundry Agents.
    """
    def __init__(self, name: str, project_endpoint: str = None):
        self.name = name
        self.project_endpoint = project_endpoint
        
        if not self.project_endpoint:
            raise ValueError(
                "Foundry Agent connection requires a project endpoint. "
                "Please provide 'project_endpoint' in the marker or environment variables."
            )
            
        self.credential = DefaultAzureCredential()

    async def run(self, query: str) -> AgentResponse:
        """
        Run the agent with the given query.
        Returns a standardized AgentResponse object.
        """
        async with AIProjectClient(
            endpoint=self.project_endpoint,
            credential=self.credential
        ) as project_client:
            # Using the agent service client
            async with project_client.get_openai_client() as openai_client:
                # 1. Resolve Agent (by name)
                agent = await project_client.agents.get(agent_name=self.name)
                if agent.versions.latest.definition.kind != "prompt":
                    raise ValueError("Only prompt agents are supported.")
                definition: PromptAgentDefinition = agent.versions.latest.definition
                
                # Extract system instructions
                instructions = definition.instructions
                
                # Extract tool definitions
                tool_definitions = []
                if definition.tools:
                    for tool in definition.tools:
                        if tool.type in _BUILT_IN_DESCRIPTIONS:
                            tool_definitions.append({
                                "type": tool.type,
                                "description": _BUILT_IN_DESCRIPTIONS[tool.type],
                                "name": tool.type,
                                "parameters": _BUILT_IN_PARAMS.get(tool.type, {}),
                            })

                # 2. Create Conversation
                conversation = await openai_client.conversations.create()

                # Set auto approval for MCP tools
                tools = []
                if definition.tools:
                    for tool in definition.tools:
                        if tool.type == "mcp":
                            tool.require_approval = "never"
                        tools.append(tool)

                # 3. Create request
                response = await openai_client.responses.create(
                    conversation=conversation.id,
                    model=definition.model,
                    instructions=instructions,
                    input=query,
                    tools=tools,
                )
                
                # Extract output text and output items
                output_text = response.output_text
                output_items = response.output
                
                # Add mcp tool definitions
                for output_item in output_items:
                    if output_item.type == "mcp_list_tools":
                        for tool in output_item.tools:
                            tool_definitions.append({
                                "name": tool.name,
                                "description": tool.description,
                                "parameters": tool.input_schema,
                            })
                
                # Extract Tool Calls
                tool_calls = []
                for output_item in output_items:
                    if output_item.type == "file_search_call":
                        tool_calls.append({
                            "type": "tool_call",
                            "name": "file_search",
                            "tool_call_id": output_item.id
                        })
                    elif output_item.type == "code_interpreter_call":
                        tool_calls.append({
                            "type": "tool_call",
                            "name": "code_interpreter",
                            "tool_call_id": output_item.id,
                            "arguments": {
                                "input": output_item.code
                            }
                        })
                    elif output_item.type == "mcp_call":
                        tool_calls.append({
                            "type": "tool_call",
                            "name": output_item.name,
                            "tool_call_id": output_item.id,
                            "arguments": json.loads(output_item.arguments) if output_item.arguments else {}
                        })
                
                return AgentResponse(
                    output_text=output_text,
                    tool_calls=tool_calls,
                    tool_definitions=tool_definitions,
                    output_items=output_items,
                    instructions=instructions,
                    raw=response,
                    type="foundry_agent"
                )

    @staticmethod
    def convert_response_for_evaluator(response_obj: AgentResponse) -> Union[str, list]:
        """
        Returns a simplified conversation history for Foundry agents.
        """
        output_items: List[ResponseOutputItem] = response_obj.output_items
        
        ALLOWED_RESPONSE_TYPES = {
            "message", 
            "file_search_call", 
            "code_interpreter_call", 
            "mcp_call", 
            "mcp_list_tools"
        }
        
        can_support = True
        for output_item in output_items:
            if output_item.type not in ALLOWED_RESPONSE_TYPES:
                can_support = False
                break
        
        if can_support:
            output = []
            for output_item in output_items:
                if output_item.type == "file_search_call":
                    output.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_call",
                                "name": "file_search",
                                "tool_call_id": output_item.id,
                                "arguments": {}
                            }
                        ]
                    })
                    output.append({
                        "role": "tool",
                        "tool_call_id": output_item.id,
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_result": output_item.results
                            }
                        ]
                    })
                elif output_item.type == "code_interpreter_call":
                    output.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_call",
                                "name": "code_interpreter",
                                "tool_call_id": output_item.id,
                                "arguments": {
                                    "input": output_item.code
                                }
                            }
                        ]
                    })
                elif output_item.type == "mcp_call":
                    output.append({
                        "role": "assistant",
                        "content": [
                            {
                                "type": "tool_call",
                                "name": output_item.name,
                                "tool_call_id": output_item.id,
                                "arguments": json.loads(output_item.arguments) if output_item.arguments else {}
                            }
                        ]
                    })
                    if output_item.output:
                        tool_result = output_item.output
                        try:
                            tool_result = json.loads(output_item.output)
                        except Exception:
                            pass
                        output.append({
                            "role": "tool",
                            "tool_call_id": output_item.id,
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_result": tool_result
                                }
                            ]
                        })
                elif output_item.type == "message":
                    content = []
                    for content_item in output_item.content:
                        if content_item.type == "output_text":
                            content.append({
                                "type": "text",
                                "text": content_item.text
                            })
                        elif content_item.type == "refusal":
                            content.append({
                                "type": "text",
                                "text": content_item.refusal
                            })
                    output.append({
                        "role": "assistant",
                        "content": content
                    })
            return output
        else:
            return response_obj.output_text
