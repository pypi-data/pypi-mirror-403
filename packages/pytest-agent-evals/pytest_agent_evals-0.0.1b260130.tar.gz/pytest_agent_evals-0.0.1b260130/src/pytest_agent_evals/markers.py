import pytest
from _pytest.fixtures import FixtureFunctionDefinition
from typing import Union, List, Dict, Any
from .types import (
    FoundryAgentConfig, 
    ChatAgentConfig, 
    AzureOpenAIModelConfig, 
    OpenAIModelConfig,
    BuiltInEvaluatorConfig,
    CustomPromptEvaluatorConfig,
    CustomCodeEvaluatorConfig
)

def agent(config: Union[FoundryAgentConfig, ChatAgentConfig]):
    """
    Connects the test to an AI Agent using a typed configuration.

    The agent must be one of the following two types:
    1. A remote agent hosted in Microsoft Foundry (configured via `FoundryAgentConfig`).
    2. A local agent defined using `agent_framework.ChatAgent` (configured via `ChatAgentConfig`).
    
    To access the agent's output (output text, tool calls, etc.), add the `agent_response` fixture 
    to your test function arguments.
    
    Args:
        config: The configuration object for the agent. Must be an instance of:
            - `FoundryAgentConfig`: For connecting to an agent hosted in Microsoft Foundry.
            - `ChatAgentConfig`: For using a local `ChatAgent` fixture.
    """
    if isinstance(config, FoundryAgentConfig):
        return pytest.mark.agent(
            name=config.agent_name, 
            type="foundry_agent", 
            project_endpoint=config.project_endpoint
        )
    elif isinstance(config, ChatAgentConfig):
        # Handle both string identifiers (for conftest fixtures) and function objects
        agent_name = (
            config.agent_fixture.__name__ 
            if isinstance(config.agent_fixture, FixtureFunctionDefinition) 
            else str(config.agent_fixture)
        )
        return pytest.mark.agent(
            name=agent_name,
            type="chat_agent"
        )
    raise TypeError(f"Invalid agent configuration. Received type '{type(config).__name__}'. Expected one of: FoundryAgentConfig, ChatAgentConfig.")

def judge_model(config: Union[AzureOpenAIModelConfig, OpenAIModelConfig]):
    """
    Configures the LLM Judge using a typed configuration.
    
    Args:
        config: One of:
            - AzureOpenAIModelConfig(deployment_name, endpoint, api_key=None)
            - OpenAIModelConfig(model, api_key, base_url=None)
    """
    if isinstance(config, AzureOpenAIModelConfig):
        return pytest.mark.judge_model(
            type="azure_openai",
            model=config.deployment_name,
            endpoint=config.endpoint,
            api_key=config.api_key
        )
    elif isinstance(config, OpenAIModelConfig):
        return pytest.mark.judge_model(
            type="openai",
            model=config.model,
            endpoint=config.base_url,
            api_key=config.api_key
        )
    raise TypeError(f"Invalid judge model configuration. Received type '{type(config).__name__}'. Expected one of: AzureOpenAIModelConfig, OpenAIModelConfig.")

def dataset(source: Union[str, List[Dict[str, Any]]]):
    """
    Defines the input dataset for the tests.
    
    Args:
        source: The dataset source.
            - If `str`, it specifies the path to a dataset file (JSONL). 
              The path can be absolute, or relative to the test file.
            - If `list[dict]`, it provides the test cases inline.
            
            Each test case (row or dict) must contain 'query' field.
            The 'id' field is optional but recommended for stable tracking and caching.
    """
    return pytest.mark.dataset(source)

def evaluator(config: Union[BuiltInEvaluatorConfig, CustomPromptEvaluatorConfig, CustomCodeEvaluatorConfig]):
    """
    Registers an evaluator (built-in or custom) to be performed on the agent's response.
    The evaluator is executed after the agent generates a response.
    
    ### Arguments
    
    - **config**: One of:
        - `BuiltInEvaluatorConfig(name, threshold=None)`
        - `CustomPromptEvaluatorConfig(name, prompt, threshold)`
        - `CustomCodeEvaluatorConfig(name, grader, threshold)`
    
    ### Inputs passed to Evaluators
    
    1. **Built-in Evaluators**:
       Inputs are automatically sourced and resolved based on the specific evaluator's requirements:
       - **From Dataset**: `query`, `context`, `ground_truth`, etc.
       - **From Agent**: `tool_definitions` (Auto-extracted from agent definition).
       - **From Response**: `response` and `tool_calls` (Auto-extracted from agent response).
       
       *Note: The plugin automatically handles data format variations required by different evaluators:*
       - *Query*: Some evaluators require a list of messages (system instruction and user message) rather than a simple query string.
       - *Response*: Some evaluators require the full agent response history rather than just the final text output.

    2. **Custom Prompt Evaluators**:
       The prompt template supports Jinja2-style placeholders for all inputs:
       - `{{query}}`: The input query string (from dataset).
       - `{{response}}`: The agent's final text response.
       - `{{tool_calls}}`: List of tool calls made by the agent.
       - `{{tool_definitions}}`: List of tools available to the agent.
       - `{{context}}`, `{{ground_truth}}`, etc: Any other columns from your dataset.

    3. **Custom Code Evaluators**:
       Receives the `sample` (agent output) and `item` (dataset row) dictionaries.

    ### Results Access
    
    Results are available in the test function via the `evaluator_results` fixture, 
    accessed by the evaluator's name (e.g., `evaluator_results.relevance`).
            
    ### Examples
    
    ```python
    # 1. Built-in Evaluator
    @evals.evaluator(BuiltInEvaluatorConfig("relevance"))
    
    # 2. Custom Prompt Evaluator
    my_prompt = \"\"\"
    You are an AI assistant that ...
    Score the response on a scale of 1 to 5, where 1 is ... and 5 is ...
    Provide a brief reason for your score.
    
    Input:
    Query: {{query}}
    Response: {{response}}
    
    You must output your result in the following JSON format:
    {
        "result": <integer from 1 to 5>,
        "reason": "<brief explanation>"
    }
    \"\"\"
    
    @evals.evaluator(CustomPromptEvaluatorConfig("my_prompt", prompt=my_prompt, threshold=3))
    
    # 3. Custom Code Evaluator
    def grade(sample: dict[str, Any], item: dict[str, Any]) -> float:
        return 1.0
        
    @evals.evaluator(CustomCodeEvaluatorConfig("my_code", grader=grade, threshold=0.8))
    ```
    """
    if isinstance(config, BuiltInEvaluatorConfig):
        return pytest.mark.evaluator(
            config.name, 
            threshold=config.threshold
        )
    elif isinstance(config, CustomPromptEvaluatorConfig):
        return pytest.mark.evaluator(
            config.name, 
            prompt=config.prompt, 
            threshold=config.threshold
        )
    elif isinstance(config, CustomCodeEvaluatorConfig):
        return pytest.mark.evaluator(
            config.name, 
            grader=config.grader, 
            threshold=config.threshold
        )
    raise TypeError(f"Invalid evaluator configuration. Received type '{type(config).__name__}'. Expected one of: BuiltInEvaluatorConfig, CustomPromptEvaluatorConfig, CustomCodeEvaluatorConfig.")
