from typing import Any, Dict, Optional, Union, Callable, Literal, List
from dataclasses import dataclass
from pydantic import TypeAdapter
from _pytest.fixtures import FixtureFunctionDefinition
from agent_framework import AgentResponse as AgentRunResponse, ChatMessage
from openai.types.responses import ResponseOutputItem, Response

# --- Agent Configurations ---

@dataclass
class FoundryAgentConfig:
    """
    Configuration for an agent hosted in Microsoft Foundry.
    
    Args:
        agent_name: The name of the agent in Microsoft Foundry.
        project_endpoint: The project endpoint URL (e.g. "https://<your-resource>.services.ai.azure.com/api/projects/<your-project>").
    """
    agent_name: str
    project_endpoint: str

@dataclass
class ChatAgentConfig:
    """
    Configuration for a local ChatAgent fixture.
    
    The referenced fixture must yield or return an instance of `agent_framework.ChatAgent`.
    
    Args:
        agent_fixture: Reference to the pytest fixture. This can be:
            1. A string: The name of the fixture (e.g., "my_agent"). 
               Useful for fixtures defined in `conftest.py` which are not directly importable.
            2. A FixtureFunctionDefinition: The fixture function symbol itself (e.g., my_agent_fixture).
               Recommended when the fixture is defined in the same file or importable.

    Example:
        ```python
        # Assuming you have an agent factory in your source code:
        # from my_app.agents import create_support_agent
        
        @pytest.fixture
        def support_agent():
            # Return the agent instance to be tested
            return create_support_agent()

        @evals.agent(ChatAgentConfig(agent_fixture=support_agent))
        class TestSupportAgent:
            ...
        ```
    """
    agent_fixture: Union[str, FixtureFunctionDefinition]

# --- Judge Model Configurations ---

@dataclass
class AzureOpenAIModelConfig:
    """
    Configuration for an LLM Judge using Azure OpenAI.
    
    Args:
        deployment_name: The name of the deployment in Azure OpenAI (e.g., "gpt-4.1").
        endpoint: The endpoint URL for the Azure OpenAI resource (e.g., "https://my-resource.openai.azure.com/").
        api_key: The API key for the Azure OpenAI resource. If not provided, azure.identity.DefaultAzureCredential will be used.
    """
    deployment_name: str
    endpoint: str
    api_key: Optional[str] = None

@dataclass
class OpenAIModelConfig:
    """
    Configuration for an LLM Judge using the OpenAI-compatible API.
    
    Args:
        model: The model identifier (e.g., "gpt-4.1").
        api_key: The API key for authentication.
        base_url: The base URL of the API. Optional. 
                  Defaults to the public OpenAI API if not provided.
                  Use this to point to a local inference server (e.g. vLLM) or other compatible providers.
    """
    model: str
    api_key: str
    base_url: Optional[str] = None

# --- Evaluator Configurations ---

@dataclass
class BuiltInEvaluatorConfig:
    """
    Configuration for a built-in evaluator provided by the plugin.
    
    Args:
        name: The identifier of the built-in evaluator (e.g., "relevance", "coherence", "tool_call_accuracy").
        threshold: The passing score threshold. If the evaluator's score is >= this value, the result is 'pass'.
                   Default depends on the specific evaluator (usually 3.0 on a 1-5 scale).
    
    ### Evaluator Details
    
    For details on specific evaluators (goals, default thresholds, etc.), see the 
    [Azure AI Evaluation documentation](https://learn.microsoft.com/en-us/python/api/azure-ai-evaluation/azure.ai.evaluation).
    """
    name: Literal[
        "coherence", "fluency", "tool_call_accuracy", "intent_resolution", 
        "task_adherence", "similarity", "f1_score", "bleu_score", 
        "gleu_score", "rouge_score", "meteor_score", "relevance", 
        "groundedness", "retrieval", "response_completeness", "document_retrieval",
        "task_completion", "task_navigation_efficiency", "tool_call_success",
        "tool_input_accuracy", "tool_output_utilization", "tool_selection"
    ]
    threshold: Optional[float] = None

@dataclass
class CustomPromptEvaluatorConfig:
    """
    Configuration for a custom evaluator using a prompt template.

    Args:
        name: A unique name for your evaluator (e.g., "my_style_check").
        prompt: The prompt template string or a path to a prompt file. 
                See **Template Variables** and **Output Requirements** below for details.
        threshold: The passing threshold. Can be either:
                   - `int`: A score value (e.g., 1-5). Use this when your prompt instructs the LLM to return an ordinal value. 
                     If the evaluator's score is >= this threshold, the result is 'pass'.
                   - `float`: A score value (e.g., 0.0-1.0). Use this when your prompt instructs the LLM to return a continuous value.
                     If the evaluator's score is >= this threshold, the result is 'pass'.
                   - `bool`: Use this when your prompt instructs the LLM to return a boolean value (true/false).
                     If the evaluator's returned boolean matches this threshold, the result is 'pass'.

    ### Template Variables
    
    The prompt supports the following **Jinja2 variables**:
    - `{{query}}`: The input query string (from dataset).
    - `{{response}}`: The agent's final text response.
    - `{{tool_calls}}`: List of tool calls made by the agent.
    - `{{tool_definitions}}`: List of tools available to the agent.
    - `{{context}}`, `{{ground_truth}}`: Any other columns from your dataset.

    ### Output Requirements
    
    The prompt must instruct the LLM to output a JSON object with the following keys:
    - `"result"`: The value must be one of the following:
        - `int`: A rating (e.g. 1 to 5).
        - `float`: A score (e.g. 0.0 to 1.0).
        - `bool`: A boolean (True/False).
        - `str`: A string "true" or "false".
    - `"reason"`: A brief string explanation for the score.

    Example:
        ```python
        prompt_tmpl = \"\"\"
        Score the response relevance from 1 to 5.
        
        Q: {{query}}
        A: {{response}}
        
        Output JSON format: {"result": int, "reason": str}
        \"\"\"
        
        CustomPromptEvaluatorConfig("relevance_check", prompt=prompt_tmpl, threshold=3.5)
        ```
    """
    name: str
    prompt: str
    threshold: Union[int, float, bool]

@dataclass
class CustomCodeEvaluatorConfig:
    """
    Configuration for a custom evaluator using a Python function.

    Args:
        name: A unique name for your evaluator.
        grader: A Python function used for grading.
                See **Grader Function** below for signature details.
        threshold: The passing score threshold. Must be a float value between 0.0 and 1.0. If the grader's score is >= this value, the result is 'pass'.

    ### Grader Function
    
    The grader function must follow this signature:
    
    ```python
    def grade(sample: dict[str, Any], item: dict[str, Any]) -> float:
        ...
    ```

    **Arguments**:
    - `sample`: The output from the agent. Contains:
        - `'output_text'`: The string response.
        - `'tool_calls'`: List of tool calls made.
        - `'tool_definitions'`: List of tools available.
    - `item`: The input data row. Contains keys from your dataset (e.g., `'query'`, `'context'`).

    **Returns**:
    - A float score (e.g., 0.0 to 1.0).

    Example:
        ```python
        def length_check(sample, item):
            # Pass if response is shorter than 100 chars
            return 1.0 if len(sample['output_text']) < 100 else 0.0
            
        CustomCodeEvaluatorConfig("short_response", grader=length_check, threshold=0.9)
        ```
    """
    name: str
    grader: Callable[[Dict[str, Any], Dict[str, Any]], float]
    threshold: float


class AgentResponse:
    """
    Standardized response object for agent evaluations.
    Holds the execution result and metadata required for evaluators.
    """
    def __init__(
        self, 
        type: Literal["chat_agent", "foundry_agent"],
        output_text: str, 
        tool_calls: List[Dict[str, Any]], 
        tool_definitions: List[Dict[str, Any]], 
        output_items: Union[List[ChatMessage], List[ResponseOutputItem]], 
        instructions: Optional[str] = None,
        raw: Union[AgentRunResponse, Response] = None
    ):
        self.type = type
        self.output_text = output_text
        self.tool_calls = tool_calls
        self.tool_definitions = tool_definitions
        self.output_items = output_items
        self.instructions = instructions
        self.raw = raw

    def to_json(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "output_text": self.output_text,
            "tool_calls": self.tool_calls,
            "tool_definitions": self.tool_definitions,
            "output_items": self._serialize_items(self.output_items),
            "instructions": self.instructions
        }

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "AgentResponse":
        agent_type = data.get("type")
        raw_items = data.get("output_items", [])
        output_items = []

        if agent_type == "chat_agent":
            output_items = [
                ChatMessage.from_dict(item) if isinstance(item, dict) else item 
                for item in raw_items
            ]
        elif agent_type == "foundry_agent":
            adapter = TypeAdapter(ResponseOutputItem)
            output_items = [
                adapter.validate_python(item) if isinstance(item, dict) else item 
                for item in raw_items
            ]
        else:
            output_items = raw_items

        return cls(
            type=agent_type,
            output_text=data.get("output_text", ""),
            tool_calls=data.get("tool_calls", []),
            tool_definitions=data.get("tool_definitions", []),
            output_items=output_items,
            instructions=data.get("instructions")
        )

    def _serialize_items(self, items: List[Any]) -> List[Any]:
        # Helper to ensure items are JSON-serializable
        if not items:
            return []
        
        # Both ChatMessage and ResponseOutputItem have to_dict()
        return [item.to_dict() if hasattr(item, "to_dict") else item for item in items]


class EvaluatorResult:
    """
    Standardized output object for an evaluator result.
    """
    def __init__(self, score: float, reason: Optional[str] = None, result: Optional[Literal["pass", "fail"]] = None, threshold: Optional[float] = None, raw: Optional[Dict[str, Any]] = None):
        self.score = score
        self.reason = reason
        self.result = result
        self.threshold = threshold
        self.raw = raw or {}

    def __repr__(self):
        return f"<EvaluatorResult score={self.score} result={self.result}>"

class EvaluatorResults:
    """
    Container for all evaluator results in a test.
    Access individual results by name (e.g. results.relevance.score).
    """
    def __init__(self, data: Dict[str, Dict[str, Any]]):
        self._data = data 
        self._outputs = {}

    def __getattr__(self, name: str) -> EvaluatorResult:
        if name in self._outputs:
            return self._outputs[name]
        
        if name in self._data:
            val = self._data[name]
            if isinstance(val, dict):
                 score = val.get("score")
                 reason = val.get("reason")
                 result = val.get("result")
                 threshold = val.get("threshold")
                 
                 # Normalization for Built-ins if needed
                 # Check if this is a raw dictionary from SDK (might be missing 'score' key at top level)
                 if score is None:
                     # Check for {name}.score or gpt_{name}
                     if name in val:
                         score = val[name]
                     elif f"{name}.score" in val:
                         score = val[f"{name}.score"]
                     elif f"gpt_{name}" in val:
                         score = val[f"gpt_{name}"]
                         
                 output = EvaluatorResult(score, reason, result, threshold, raw=val)
                 self._outputs[name] = output
                 return output
            
        raise AttributeError(f"No evaluator result found for '{name}'. Available: {list(self._data.keys())}")
        
    def __repr__(self):
         keys = list(self._data.keys())
         return f"<EvaluatorResults: {keys}>"
