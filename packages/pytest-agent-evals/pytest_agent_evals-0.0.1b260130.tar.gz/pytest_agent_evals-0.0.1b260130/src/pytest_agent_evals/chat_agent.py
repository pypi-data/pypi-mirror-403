from typing import List
from agent_framework import AIFunction, ChatAgent, ChatMessage, ai_function
from .types import AgentResponse

class ChatAgentRunner:
    """Runner for agent-framework ChatAgent."""
    def __init__(self, agent: ChatAgent):
        self.agent = agent

    async def run(self, query: str) -> AgentResponse:
        # Run agent
        response_obj = await self.agent.run(query)
        
        # Extract tool definitions
        tool_definitions = self._extract_tools(self.agent)
        
        # Extract instructions
        instructions = self._extract_instructions(self.agent)

        # Extract output items
        output_items = response_obj.messages

        # Extract tool calls
        tool_calls = []
        for message in response_obj.messages:
            for content in message.contents:
                if content.type == "function_call":
                    tool_calls.append({
                        "type": "tool_call",
                        "name": content.name,
                        "arguments": content.arguments,
                        "tool_call_id": content.call_id
                    })

        output_text = response_obj.messages[-1].text

        return AgentResponse(
            type="chat_agent",
            output_text=output_text,
            tool_calls=tool_calls,
            tool_definitions=tool_definitions,
            output_items=output_items,
            instructions=instructions,
            raw=response_obj
        )

    def _extract_tools(self, agent: ChatAgent):
        tool_definitions = []
        tools = agent.default_options.get("tools")
        if not tools:
            return tool_definitions

        for tool in tools:
            spec = None
            # Case A: Tool is already an AIFunction object
            if isinstance(tool, AIFunction):
                spec = tool.to_json_schema_spec()
            
            # Case B: Tool is a raw function (Callable) - Wrap it
            elif callable(tool):
                wrapped_tool = ai_function(tool)
                spec = wrapped_tool.to_json_schema_spec()
            
            # Case C: Raw Dictionary
            elif isinstance(tool, dict):
                spec = tool

            # Unwrap OpenAI format: {"type": "function", "function": {...}}
            if isinstance(spec, dict) and "function" in spec:
                spec = spec["function"]
                     
            if spec:
                tool_definitions.append(spec)
        
        return tool_definitions


    def _extract_instructions(self, agent: ChatAgent):
        instructions = None
        if hasattr(agent, "default_options") and isinstance(agent.default_options, dict):
            instructions = agent.default_options.get("instructions")
        if not instructions and hasattr(agent, "chat_options") and hasattr(agent.chat_options, "instructions"):
             instructions = agent.chat_options.instructions
        return instructions

    @staticmethod
    def convert_response_for_evaluator(response_obj: AgentResponse) -> list:
        """
        Returns the conversation history in the strict format required by Azure AI Evaluation.
        Format:
        - Tool calls are embedded in 'content' list with type='tool_call'.
        - Tool results are embedded in 'content' list with type='tool_result'.
        """
        messages: List[ChatMessage]  = response_obj.output_items

        output = []
        
        for msg in messages:
            out_msg = {"role": msg.role.value, "content": []}
            
            for content in msg.contents:
                if content.type == "text":
                    out_msg["content"].append({
                        "type": "text",
                        "text": content.text
                    })
                elif content.type == "function_call":
                    # Map function_call -> tool_call
                    out_msg["content"].append({
                        "type": "tool_call",
                        "name": content.name,
                        "tool_call_id": content.call_id,
                        "arguments": content.arguments
                    })
                elif content.type == "function_result":
                    # Map function_result -> tool_result
                    out_msg["content"].append({
                        "type": "tool_result",
                        "tool_result": content.result 
                    })
            
            output.append(out_msg)
            
        return output
