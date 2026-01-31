"""
pytest-agent-evals Plugin

This plugin provides a comprehensive framework for evaluating AI Agents using pytest.
It handles:
1.  **Data Loading**: Parametrizing tests from dataset files (JSONL) or inline data using `@pytest.mark.dataset`.
2.  **Agent Execution**: Running agents (`ChatAgent` or Foundry) and caching responses to disk to avoid redundant API calls.
3.  **Evaluation**: Running built-in or custom evaluators (LLM-based or code-based) on the agent's response.
4.  **Reporting**: Aggregating evaluation results into a JSON report and a terminal summary.

Key Components:
- `dataset`: Marker for defining test cases.
- `agent`: Marker for connecting to a Foundry agent or a ChatAgent fixture.
- `judge_model`: Marker for configuring the LLM used for evaluation.
- `evaluator`: Marker for defining evaluators (built-in or custom).
"""

import sys
import json
import inspect
import textwrap
import hashlib
import asyncio
import random
import re
import ast
import linecache
import pytest
import pytest_asyncio
from functools import partial
from datetime import datetime
from pathlib import Path
from typing import Union
from filelock import FileLock
from azure.identity import DefaultAzureCredential
from .types import AgentResponse, EvaluatorResults



def is_rate_limit_error(e: Exception) -> bool:
    """
    Checks if the exception or its cause is a 429 Rate Limit error 
    by inspecting the status_code property or error message.
    """
    # 1. Check if the exception itself has status_code 429
    if getattr(e, "status_code", None) == 429:
        return True
    
    # 2. Check if the underlying cause has status_code 429
    # The 'raise ... from ex' syntax sets the __cause__ attribute
    if e.__cause__ and getattr(e.__cause__, "status_code", None) == 429:
        return True

    # 3. Check for specific error messages (e.g. wrapped errors with 400 code but 429 message)
    error_msg = str(e).lower()
    if "too many requests" in error_msg:
        return True
        
    return False

# --- 1. Data Loading Infrastructure ---

def pytest_addoption(parser):
    """Register CLI options."""
    parser.addoption(
        "--collect-evals", 
        action="store_true", 
        help="List the evaluations (grouped by Agent/Dataset/Evaluators)."
    )
    parser.addoption(
        "--cache-mode",
        choices=["session", "persistence"],
        default="session",
        help="Control agent response caching behavior. 'session' (default): Clears cache at startup. Ensures consistency by sharing the same fresh response across all evaluators for a query. 'persistence': Preserves cache across sessions. Avoids redundant agent execution, enabling rapid evaluator tuning without agent changes."
    )

def pytest_configure(config):
    """Register custom markers."""
    
    # Disable xdist workers when only collecting evaluation metadata.
    # This prevents worker overhead and ensures stdout is not captured/mangled.
    if config.getoption("--collect-evals"):
        if hasattr(config.option, "numprocesses"):
            config.option.numprocesses = None
        if hasattr(config.option, "dist"):
            config.option.dist = "no"

    # Enhanced marker descriptions for pytest --help
    config.addinivalue_line("markers", "dataset(source: Union[str, List[Dict[str, Any]]]): Defines the input dataset for the tests. Source can be a file path (JSONL) or a list of inline test cases. Use @evals.dataset for better code intelligence.")
    config.addinivalue_line("markers", "judge_model(type: Literal['azure_openai', 'openai'], model: str, *, endpoint: Optional[str] = None, api_key: Optional[str] = None): Configures the LLM Judge used for evaluations. Use @evals.judge_model for better code intelligence.")
    config.addinivalue_line("markers", "evaluator(name: str, threshold: Optional[Union[float, int, bool]] = None, *, prompt: Optional[str] = None, grader: Optional[Callable[[Dict[str, Any], Dict[str, Any]], float]] = None): Registers an evaluator (built-in or custom) to be performed on the agent's response. Use @evals.evaluator for better code intelligence.")
    config.addinivalue_line("markers", "agent(name: Union[str, FixtureFunctionDefinition], type: Literal['foundry_agent', 'chat_agent'] = 'chat_agent', project_endpoint: Optional[str] = None): Connects the test to an AI Agent. Use @evals.agent for better code intelligence.")

@pytest.fixture
def _dataset_case(request):
    """
    Fixture that returns the current dataset case (dictionary).
    It receives the value via indirect parametrization.
    """
    if not hasattr(request, "param"):
        return {}
    
    # Lazy Loading Strategy
    # If the param has '_line_index', it's a file pointer -> Load it now
    case_metadata = request.param
    
    if "_line_index" in case_metadata and "_dataset_file" in case_metadata:
        file_path = case_metadata["_dataset_file"]
        line_idx = case_metadata["_line_index"] # 1-based usually
        
        try:
            # Force linecache to check for file updates
            linecache.checkcache(file_path)

            # linecache uses 1-based indexing
            # Note: linecache.getline returns empty string if line not found
            line_content = linecache.getline(file_path, line_idx)
            
            if not line_content:
                 pytest.fail(f"Dataset Error: Could not read line {line_idx} from '{file_path}'. "
                             "The file may have been modified or shortened. Please refresh the test explorer.")

            case_data = json.loads(line_content)

            # Safety Check: Verify Identity to detect file drift (e.g. lines shifted)
            if "id" in case_metadata:
                expected_id = str(case_metadata["id"])
                actual_id = str(case_data.get("id", ""))
                
                if expected_id != actual_id:
                    pytest.fail(f"Dataset Mismatch: Expected case id='{expected_id}' at line {line_idx}, but found id='{actual_id}'. "
                                f"The dataset file '{file_path}' has changed. Please refresh the test explorer.")

        except json.JSONDecodeError:
            pytest.fail(f"Dataset Error: Line {line_idx} in '{file_path}' is not valid JSON. Please check the file content.")
        except Exception as e:
            # If it's a pytest failure (from above), re-raise it
            # pytest.fail raises an exception that inherits from BaseException or Exception depending on version/plugins
            # To be safe, we check if it's the specific mismatch or failure we just raised.
            if "Dataset " in str(e):
                raise e
            # Unexpected error
            case_data = {}

        # Merge metadata back (preserve test_id etc)
        case_data.update(case_metadata)
        # remove internal pointer keys if desired, or keep them
        return case_data

    # Fallback: Inline data (already fully loaded)
    return case_metadata

def pytest_generate_tests(metafunc):
    """
    Parametrizes the '_dataset_case' fixture.
    Usage: 
        @pytest.mark.dataset("my_data.jsonl")  # File path
        @pytest.mark.dataset([{"query": "foo"}]) # Inline list
    """
    marker = metafunc.definition.get_closest_marker("dataset")
    
    # Check if '_dataset_case' is requested OR if @dataset is present
    if "_dataset_case" in metafunc.fixturenames or marker:
        
        # If implied by marker but not requested, add it to fixturenames
        # This ensures '_dataset_case' is treated as a fixture for this test
        if "_dataset_case" not in metafunc.fixturenames:
            metafunc.fixturenames.append("_dataset_case")

        # 1. Check for explicit marker
        dataset_arg = None
        if marker:
            if marker.args:
                dataset_arg = marker.args[0]
            elif "source" in marker.kwargs:
                dataset_arg = marker.kwargs["source"]
        
        if dataset_arg is None:
            if marker:
                raise pytest.UsageError(f"Error in test '{metafunc.definition.nodeid}': @pytest.mark.dataset requires a source argument (file path or inline list).")
            return

        cases = []
        
        # Case A: Inline List
        if isinstance(dataset_arg, list):
            # We treat inline data as a virtual dataset named "inline"
            # Note: This means cache might collide if multiple tests use inline data 
            # with same ID+Query in the same module.
            import copy
            cases = copy.deepcopy(dataset_arg)
            for case_data in cases:
                case_data["_dataset"] = "inline"

        # Case B: File Path (String)
        elif isinstance(dataset_arg, str):
            file_name = dataset_arg
            
            # Resolve file path behavior:
            # 1. If 'file_name' is absolute, it overrides 'test_file_path' due to pathlib behavior.
            # 2. If 'file_name' is relative, it is resolved relative to the directory containing the test file.
            # note: We interpret relative paths strictly relative to the test file, not the CWD.
            test_file_path = Path(metafunc.definition.fspath).parent
            dataset_path = test_file_path / file_name

            if dataset_path.exists():
                # Resolve to absolute path for consistent reporting and tool integration
                abs_dataset_path = str(dataset_path.resolve())
                with open(dataset_path, "r", encoding="utf-8") as f:
                    # Enumerate lines (1-based for linecache compatibility)
                    for line_idx, line in enumerate(f, 1):
                        if line.strip():
                            try:
                                temp_data = json.loads(line)
                                
                                # Create lightweight pointer
                                case_pointer = {
                                    "_dataset": abs_dataset_path,      # For cache key logic
                                    "_dataset_file": abs_dataset_path, # For linecache loading
                                    "_line_index": line_idx,
                                }
                                
                                # We need 'id' for the test ID generation below
                                if "id" in temp_data:
                                    case_pointer["id"] = temp_data["id"]
                                
                                cases.append(case_pointer)
                            except json.JSONDecodeError:
                                pass # Skip invalid lines
            
        # Assign IDs and inject into case data for downstream usage
        ids = []
        for i, c in enumerate(cases):
            # Prefer explicit 'id', fallback to string index
            if "id" in c:
                # Ensure it's a string
                t_id = str(c["id"])
            else:
                t_id = str(i)
            
            ids.append(t_id)
            # Inject stable ID for reporting
            c["_test_id"] = t_id
        
        # Use indirect=True so the value is passed to the '_dataset_case' fixture factory
        # rather than being forced as a test function argument.
        metafunc.parametrize("_dataset_case", cases, ids=ids, indirect=["_dataset_case"])

def pytest_collection_modifyitems(config, items):
    """
    Hook to intercept test execution for --collect-evals.
    Groups collected items by (Agent, Dataset, Evaluators) and prints metadata.
    """
    if config.getoption("--collect-evals"):
        groups = {}
        
        for item in items:
            # Only process items that use our '_dataset_case' fixture
            if not hasattr(item, "callspec") or "_dataset_case" not in item.callspec.params:
                continue
            
            case_data = item.callspec.params["_dataset_case"]
            
            if not isinstance(case_data, dict):
                continue

            # 1. Required: Agent Marker
            agent_marker = item.get_closest_marker("agent")
            if not agent_marker:
                continue

            # 2. Required: Dataset (via internal key injected by fixture)
            dataset_path = case_data.get("_dataset")
            if not dataset_path:
                continue

            # 3. Required: At least one Evaluator
            if not item.get_closest_marker("evaluator"):
                continue
            
            # Extract Agent
            # usage: @pytest.mark.agent("my_agent") or @pytest.mark.agent(name="my_agent")
            agent_info = {"name": None}
            
            # 1. Positional args (Name) - Align with runner logic
            # This is the most common case: @pytest.mark.agent("agent_fixture")
            if agent_marker.args:
                agent_info["name"] = agent_marker.args[0]

            # 2. Kwargs
            agent_info.update(agent_marker.kwargs)
            
            # Extract Judge Model Config
            judge_model_marker = item.get_closest_marker("judge_model")
            judge_model = None
            if judge_model_marker:
                judge_model = judge_model_marker.kwargs.copy()
                # Remove sensitive information
                judge_model.pop("api_key", None)
            
            # Extract Evaluators
            evaluators = []
            for mark in item.iter_markers():
                if mark.name == "evaluator":
                    # Unified Evaluator Logic
                    name = mark.args[0] if mark.args else mark.kwargs.get("name")
                    if not name:
                        # Skip malformed
                        continue

                    kwargs = mark.kwargs
                    
                    # 1. Custom Code
                    if "grader" in kwargs:
                        grader_func = kwargs.get("grader")
                        if grader_func:
                            try:
                                grader_source = inspect.getsource(grader_func)
                                # Normalize indentation to ensure it is clean code block
                                grader_source = textwrap.dedent(grader_source)
                                
                                # Rename function to 'grade' using AST
                                try:
                                    tree = ast.parse(grader_source)
                                    if tree.body and isinstance(tree.body[0], (ast.FunctionDef, ast.AsyncFunctionDef)):
                                        tree.body[0].name = "grade"
                                        if hasattr(ast, "unparse"):
                                            grader_source = ast.unparse(tree)
                                        else:
                                            # Fallback for Python < 3.9
                                            grader_source = re.sub(r"def\s+" + re.escape(grader_func.__name__), "def grade", grader_source, count=1)
                                except Exception:
                                    pass

                                evaluators.append({
                                    "kind": "custom_code",
                                    "name": name,
                                    "threshold": kwargs.get("threshold"),
                                    "grader": grader_source
                                })
                            except Exception:
                                # Fallback if source cannot be retrieved (e.g. interactive implementation)
                                pass
                    
                    # 2. Custom Prompt
                    elif "prompt" in kwargs:
                         evaluators.append({
                            "kind": "custom_prompt",
                            "name": name,
                            "prompt": kwargs.get("prompt"),
                            "threshold": kwargs.get("threshold")
                        })

                    # 3. Built-in
                    else:
                        evaluators.append({
                            "kind": "builtin",
                            "name": name,
                            "threshold": kwargs.get("threshold")
                        })
            
            # Use explicit name if available, otherwise skip (since we require an agent name now)
            agent_identifier = agent_info.get("name")
            if not agent_identifier:
                continue

            group_key = (agent_identifier, dataset_path)
            
            if group_key not in groups:
                groups[group_key] = {
                    "agent": agent_info,
                    "dataset": dataset_path,
                    "evaluators": [],
                    "cases": {},
                    "judge_model": judge_model
                }
            
            # Merge Evaluators
            current_group = groups[group_key]
            existing_eval_names = {e["name"] for e in current_group["evaluators"]}
            for e in evaluators:
                if e["name"] not in existing_eval_names:
                    current_group["evaluators"].append(e)
                    existing_eval_names.add(e["name"])

            # Add case data (excluding internal keys)
            clean_case = {k: v for k, v in case_data.items() if not k.startswith("_")}

            if "_line_index" in case_data and "query" not in clean_case:
                try:
                     line_content = linecache.getline(case_data["_dataset_file"], case_data["_line_index"])
                     full_data = json.loads(line_content)
                     clean_case.update(full_data)
                     clean_case = {k: v for k, v in clean_case.items() if not k.startswith("_")}
                except:
                    pass
            
            # Use injected ID for grouping
            case_id = case_data.get("_test_id", str(clean_case))
            
            if case_id not in current_group["cases"]:
                current_group["cases"][case_id] = clean_case
            
        # Output result
        final_output = []
        for g in groups.values():
            g["cases"] = list(g["cases"].values())
            final_output.append(g)
            
        # Use terminal reporter to ensure output is visible even with xdist/capturing
        # Fallback to sys.stdout directly if reporter is unavailable or capturing is aggressive
        reporter = config.pluginmanager.get_plugin("terminalreporter")
        output_str = json.dumps(final_output, indent=2)
        
        if reporter:
            try:
                reporter.write_line(output_str)
            except Exception:
                sys.stdout.write(output_str + "\n")
                sys.stdout.flush()
        else:
            sys.stdout.write(output_str + "\n")
            sys.stdout.flush()
        
        # Prevent actual execution
        items.clear()

def pytest_runtest_setup(item):
    """
    Called before each test item is executed.
    Used for validating markers to ensure correct usage.
    """
    _validate_markers(item)

def _validate_markers(item):
    """
    Validates that the custom markers are used correctly.
    Raises pytest.fail() if any validation error is found.
    """
    # 1. Validate @agent
    agent_marker = item.get_closest_marker("agent")
    if agent_marker:
        args = agent_marker.args
        kwargs = agent_marker.kwargs
        
        # Name
        name = args[0] if args else kwargs.get("name")
        
        # Type
        agent_type = kwargs.get("type", "chat_agent") # default
        
        if agent_type not in ("chat_agent", "foundry_agent"):
            pytest.fail(f"[Configuration Error] @pytest.mark.agent: Invalid type '{agent_type}'. Usage: type must be 'chat_agent' or 'foundry_agent'.")

        if agent_type == "chat_agent":
            # Name must be a fixture
            fixture_name = None
            if callable(name):
                fixture_name = name.__name__
            elif isinstance(name, str):
                fixture_name = name
            
            if not fixture_name:
                pytest.fail("[Configuration Error] @pytest.mark.agent(type='chat_agent'): Missing fixture identifier. Usage: Provide the fixture name (str) or function reference as the first argument or 'name' kwarg.")
        
        elif agent_type == "foundry_agent":
            if not name or not isinstance(name, str):
                pytest.fail("[Configuration Error] @pytest.mark.agent(type='foundry_agent'): Missing agent name. Usage: Provide the agent name (str) as the first argument or 'name' kwarg.")
            
            project_endpoint = kwargs.get("project_endpoint")
            if not project_endpoint:
                pytest.fail("[Configuration Error] @pytest.mark.agent(type='foundry_agent'): Missing 'project_endpoint'. Usage: Provide 'project_endpoint' kwarg.")
            
            if not re.match(r"^https://[^/]+\.services\.ai\.azure\.com/api/projects/[^/]+$", project_endpoint):
                pytest.fail(f"[Configuration Error] @pytest.mark.agent(type='foundry_agent'): Invalid project_endpoint '{project_endpoint}'. Usage: Must match format 'https://<resource>.services.ai.azure.com/api/projects/<project>'.")

    # 2. Validate @evaluator
    for mark in item.iter_markers("evaluator"):
        args = mark.args
        kwargs = mark.kwargs
        
        name = args[0] if args else kwargs.get("name")
        if not name:
            pytest.fail("[Configuration Error] @pytest.mark.evaluator: Missing name. Usage: @pytest.mark.evaluator('name', ...).")
        
        has_prompt = "prompt" in kwargs
        has_grader = "grader" in kwargs
        
        if has_prompt and has_grader:
            pytest.fail(f"[Configuration Error] @pytest.mark.evaluator('{name}'): Conflicting arguments. Usage: Specify either 'prompt' (for LLM) or 'grader' (for code), not both.")
        
        if has_prompt:
            if "threshold" not in kwargs:
                pytest.fail(f"[Configuration Error] @pytest.mark.evaluator('{name}'): Missing 'threshold'. Usage: Custom prompt evaluators must specify a 'threshold' for pass/fail determination.")
        
        if has_grader:
            grader = kwargs.get("grader")
            if not callable(grader):
                pytest.fail(f"[Configuration Error] @pytest.mark.evaluator('{name}'): Invalid 'grader'. Usage: 'grader' must be a callable function.")

    # 3. Validate @judge_model
    judge_marker = item.get_closest_marker("judge_model")
    if judge_marker:
        if judge_marker.args:
            pytest.fail("[Configuration Error] @pytest.mark.judge_model: Positional arguments not supported. Usage: Use keyword arguments (e.g., type='azure_openai', model='...').")
        
        j_type = judge_marker.kwargs.get("type", "azure_openai") # default
        if j_type not in ("azure_openai", "openai"):
            pytest.fail(f"[Configuration Error] @pytest.mark.judge_model: Invalid type '{j_type}'. Usage: type must be 'azure_openai' or 'openai'.")
        
        if j_type == "azure_openai":
            if "endpoint" not in judge_marker.kwargs or "model" not in judge_marker.kwargs:
                pytest.fail("[Configuration Error] @pytest.mark.judge_model(type='azure_openai'): Missing required arguments. Usage: Must provide 'endpoint' and 'model'.")
        elif j_type == "openai":
            if "model" not in judge_marker.kwargs:
                pytest.fail("[Configuration Error] @pytest.mark.judge_model(type='openai'): Missing required arguments. Usage: Must provide 'model'.")
    
    # 4. Validate @dataset
    dataset_marker = item.get_closest_marker("dataset")
    if dataset_marker:
        source = None

        if dataset_marker.args:
            source = dataset_marker.args[0]
        elif "source" in dataset_marker.kwargs:
            source = dataset_marker.kwargs["source"]
        
        if source is None:
            pytest.fail("[Configuration Error] @pytest.mark.dataset: Invalid or missing source. Usage: Provide a file path (str) or a list of dicts as the first argument.")
        
        if not isinstance(source, (str, list)):
            pytest.fail(f"[Configuration Error] @pytest.mark.dataset: Invalid source type '{type(source).__name__}'. Usage: Source must be a string (path) or list (data).")

# --- 2. Response Caching & Verification ---
# AgentResponse class is imported from .models

def _convert_to_evaluator_format(response_obj) -> Union[str, list]:
    """
    Dispatcher to convert the agent response into the evaluator trace format.
    Delegates to the specific agent implementation based on response type.
    """
    if response_obj.type == "chat_agent":
        from .chat_agent import ChatAgentRunner
        return ChatAgentRunner.convert_response_for_evaluator(response_obj)
    
    elif response_obj.type == "foundry_agent":
        from .foundry_agent import FoundryAgentRunner
        return FoundryAgentRunner.convert_response_for_evaluator(response_obj)
    
    # Fallback for legacy caches or unknown types
    # Case A: Local Chat Agent (duck typing)
    if hasattr(response_obj, "raw") and response_obj.raw and hasattr(response_obj.raw, "messages"):
        from .chat_agent import ChatAgentRunner
        return ChatAgentRunner.convert_response_for_evaluator(response_obj)

    # Case B: Generic Text Fallback
    text = response_obj.output_text
    return [{
        "role": "assistant",
        "content": [{
            "type": "text",
            "text": text or ""
        }]
    }]

def pytest_sessionstart(session):
    """
    Called before the test session starts.
    We use this to clear:
    1. The agent response cache (based on mode).
    2. The result staging area (for xdist result collection).
    """

    # Only the main process (controller) should clear the cache/results.
    # Workers (xdist) simply share the directories.
    if not hasattr(session.config, "workerinput"): 
        # 1. Clear Response Cache (agent_eval_responses)
        # Note: .makedir() returns a legacy py.path.local object, convert to Path
        cache_dir = Path(session.config.cache.makedir("agent_eval_responses"))
        
        cache_mode = session.config.getoption("--cache-mode")
        
        # If mode is 'session' (default), we ensure a fresh start by clearing old responses.
        if cache_mode == "session" and cache_dir.exists():
            for item in cache_dir.iterdir():
                if item.is_file():
                    try:
                        item.unlink()
                    except Exception:
                        pass # Best effort cleanup

        # 2. Clear Results Staging Area (agent_eval_results)
        results_dir = Path(session.config.cache.makedir("agent_eval_results"))
        if results_dir.exists():
            for item in results_dir.iterdir():
                if item.is_file():
                    try:
                        item.unlink()
                    except Exception:
                        pass


@pytest.fixture
def _agent_runner(request):
    """
    Synchronous fixture to resolve the agent fixture dynamically.
    This must be synchronous to avoid 'Runner.run() cannot be called from a running event loop'
    when pytest-asyncio tries to setup the dependent async fixture.
    """
    __tracebackhide__ = True  # Hide internal frames on failure
    
    # Unified marker handling
    marker = request.node.get_closest_marker("agent")
    
    # Defaults
    agent_type = "chat_agent"
    kwargs = {}
    identifier = None

    if marker:
        kwargs = marker.kwargs
        agent_type = kwargs.get("type", "chat_agent")
        
        # Priority: Positional Argument > Keyword Argument
        if marker.args:
            identifier = marker.args[0]
        else:
            # Fallback for explicit keyword usage
            identifier = kwargs.get("name") # Common for all types

    # 1. Foundry Agent
    if agent_type == "foundry_agent":
        from .foundry_agent import FoundryAgentRunner
        project_endpoint = kwargs.get("project_endpoint")
        return FoundryAgentRunner(name=identifier, project_endpoint=project_endpoint)

    # 2. Chat Agent (Local Fixture)
    else: 
        from .chat_agent import ChatAgentRunner
        # The user can pass either the name of the fixture (str) or the fixture function itself.
        agent_instance = None
        
        # Case A: String (Fixture Name)
        # The most common usage: @pytest.mark.agent("my_agent_fixture")
        if isinstance(identifier, str):
            try:
                agent_instance = request.getfixturevalue(identifier)
            except pytest.FixtureLookupError:
                # This should be caught by validation hook, but kept as safety net
                pytest.fail(f"MISSING FIXTURE: The test class is marked with @pytest.mark.agent('{identifier}'), but that fixture is not defined.")
            except Exception as e:
                # Re-raise other exceptions (like Auth errors) so they are visible
                raise e

        # Case B: Fixture Function Reference
        # Advanced usage allowing Direct reference to the function object for better IDE support.
        # Example: @pytest.mark.agent(my_agent_fixture)
        if callable(identifier):
            # Support passing the fixture function definition directly (for IDE navigation/renaming support)
            # We resolve it by name in the request scope.
            fixture_name = identifier.__name__
            agent_instance = request.getfixturevalue(fixture_name)

        if agent_instance:
            return ChatAgentRunner(agent_instance)
        
        pytest.fail(f"Could not resolve agent runner for type: {agent_type}")

class CodeEvaluator:
    """
    Executes a custom Python function as an evaluator.
    
    The function must accept two arguments:
    1. sample (dict): Contains 'output_text', 'tool_calls', 'tool_definitions'.
    2. item (dict): Contains the input data row (e.g., 'query', 'id', 'ground_truth').
    
    It must return a float score.
    """
    def __init__(self, func_obj=None):
        self.func_obj = func_obj

    def run(self, sample, item):
        func = None
        
        if self.func_obj:
            func = self.func_obj
        else:
            raise ValueError("func_obj not provided.")
        
        # Execute the user's function
        try:
            score = func(sample, item)
            return {"result": float(score), "reason": ""}
        except Exception as e:
            return {"result": 0.0, "reason": f"Code evaluation failed: {e}"}

class PromptEvaluator:
    """
    Executes a custom LLM-based evaluator defined by a Prompty file or template.
    """
    def __init__(self, prompt_text, model_config, credential=None, is_file=False):
        self.prompt_text = prompt_text
        self.is_file = is_file
        self.model_config = model_config
        
        if not model_config:
            raise ValueError("Model configuration is required for custom evaluators.")

        if model_config.get("type") == "azure_openai":
            from agent_framework.azure import AzureOpenAIChatClient
            self.client = AzureOpenAIChatClient(
                endpoint=model_config.get("azure_endpoint"),
                deployment_name=model_config.get("azure_deployment"),
                api_key=model_config.get("api_key"),
                credential=credential if not model_config.get("api_key") else None
            )
        else:
            from agent_framework.openai import OpenAIChatClient
            self.client = OpenAIChatClient(
                model_id=model_config.get("model"),
                api_key=model_config.get("api_key"),
                base_url=model_config.get("base_url")
            )

    def _render_prompt(self, context):
        template = ""
        if self.is_file:
            with open(self.prompt_text, "r", encoding="utf-8") as f:
                template = f.read()
        else:
            template = self.prompt_text
        
        # Simple Jinja2-style replacement
        prompt = template
        for key, value in context.items():
            replacement = str(value)
            if isinstance(value, (dict, list)):
                replacement = json.dumps(value, indent=2)
            prompt = prompt.replace(f"{{{{{key}}}}}", replacement)
        
        return prompt

    async def run(self, context):
        full_prompt = self._render_prompt(context)
        
        response_obj = await self.client.get_response(full_prompt)
        
        content = str(response_obj)
        if hasattr(response_obj, "messages") and response_obj.messages:
            content = response_obj.messages[-1].text
        
        content = content.strip()
        # Strip markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        try:
            result = json.loads(content)
            
            # Validate numeric result constraints
            if "result" in result:
                val = result["result"]
                # Case 1: Boolean
                if isinstance(val, bool):
                    pass # True/False is valid
                # Case 2: Numeric (int/float)
                elif isinstance(val, (int, float)):
                    # Check for 0-1 range (float) OR 1-5 range (int rating)
                    # We allow 0.0 to 5.0 to be safe, but strictly speaking:
                    # If > 1.0 and <= 5.0 -> assumed ordinal
                    # If >= 0.0 and <= 1.0 -> assumed confidence/probability
                    pass 
                # Case 3: String that looks like boolean "true"/"false"
                elif isinstance(val, str):
                    lower = val.lower()
                    if lower in ("true", "false"):
                        result["result"] = (lower == "true")
                    else:
                        return {"result": None, "reason": f"Invalid result format: String '{val}' is not a valid boolean."}
                else:
                    return {"result": None, "reason": f"Invalid result type: {type(val)}. Expected int (1-5), float (0-1), or boolean."}

            return result
        except Exception as e:
            return {"result": None, "reason": f"Failed to parse JSON. Ensure your prompt instructs the model to output valid JSON. Error: {e}. Content: {content}"}

@pytest_asyncio.fixture
async def agent_response(_dataset_case, request, _agent_runner, _judge_model_config):
    """
    Executes the agent run (cached by case ID and test module) and returns a Verifier object.
    Requires an agent fixture to be defined (specified by @pytest.mark.agent(fixture=...)).
    Handles parallel execution via File Locking in the shared .pytest_cache dir.
    """
    agent = _agent_runner
    case = _dataset_case

    # --- Pre-Initialize Evaluation Data ---
    # This ensures that even if agent execution fails, we have the inputs recorded.
    if not hasattr(request.node, "_eval_data"):
        flat_result = {}
        # Add inputs
        flat_result["inputs.query"] = case.get("query", "")
        # Add other dataset fields
        for k, v in case.items():
            if k != "query" and not k.startswith("_"):
                flat_result[f"inputs.{k}"] = v
                
        flat_result["_case_key"] = f"{case.get('_test_id')}::{case.get('query', '')}"
        
        # Placeholder outputs to avoid missing keys in report
        flat_result["outputs.response"] = "" 
        flat_result["outputs.tool_calls"] = []
        flat_result["outputs.tool_definitions"] = []
        
        request.node._eval_data = flat_result

    # Cache Logic:
    # 1. Use explicit 'id' if available (stable per user)
    # 2. Fallback to Content Hash (stable against reordering)
    # Note: We do NOT use index-based _test_id for caching to prevent invalidation on insertion.
    cache_id = case.get("id")
    if cache_id is None:
        # Stable content hash excluding internal fields
        clean_content = {k: v for k, v in case.items() if not k.startswith("_")}
        cache_id = hashlib.md5(json.dumps(clean_content, sort_keys=True).encode("utf-8")).hexdigest()
    else:
        cache_id = str(cache_id)

    dataset = case.get("_dataset", "default")
    query = case.get("query", "")
    

    # Extract agent identifier from marker to prevents collisions between different agents running the same dataset
    agent_marker = request.node.get_closest_marker("agent")
    agent_id_str = "default"
    if agent_marker:
        # Normalize args (handle callable fixtures)
        clean_args = [arg.__name__ if callable(arg) else str(arg) for arg in agent_marker.args]
        # We use a stable string representation of the marker configuration
        agent_id_str = f"{clean_args}-{agent_marker.kwargs}"

    # Namespace the cache key by module AND dataset AND agent AND cache_id AND query
    # (Including agent_id ensures that if we run the same dataset against two different agents, we don't cache collide)
    cache_key_raw = f"{request.module.__name__}::{dataset}::{agent_id_str}::{cache_id}::{query}"
    cache_filename = hashlib.md5(cache_key_raw.encode("utf-8")).hexdigest() + ".json"
    
    # Use .pytest_cache directory
    # function-scoped request.config.cache is available
    agent_cache_dir = Path(request.config.cache.makedir("agent_eval_responses"))
    
    cache_file_path = agent_cache_dir / cache_filename
    lock_file_path = agent_cache_dir / (cache_filename + ".lock")
    
    response_obj = None
    captured_error = None

    # --- CHECK-LOCK-CHECK-RUN Pattern ---
    # This ensures thread-safety when running tests in parallel (xdist).
    # We want to avoid running the same agent query multiple times if multiple workers pick up the same case.
    
    # 1. Fast Path: Check if cache exists (Read Optimization)
    # If the file exists, we can read it immediately without acquiring the lock (avoiding contention).
    if cache_file_path.exists():
        try:
             # Read raw content first to support both string-based and dict-based deserialization
             with open(cache_file_path, "r", encoding="utf-8") as f:
                 raw_content = f.read()
            
             if raw_content.strip():
                 data = json.loads(raw_content)
                 # Handle double-encoded JSON (legacy cache fix)
                 if isinstance(data, str):
                     data = json.loads(data)
                 
                 response_obj = AgentResponse.from_json(data)
             
        except Exception:
            # If corruption or read error, ignore and fall through to re-run
            pass

    if response_obj is None:
        # 2. Acquire Lock (for Write/Double-Check)
        # If we didn't find the file (or we are forcing a run), we must acquire the lock
        # to ensure we are the only one generating the response.
        with FileLock(str(lock_file_path)):
            
            # 3. Double-Check: Check if another worker created it while we were waiting for the lock
            if cache_file_path.exists():
                try:
                    with open(cache_file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, str):
                             data = json.loads(data)
                        
                        response_obj = AgentResponse.from_json(data)
                except Exception:
                     pass
            
            # 4. Run (Miss)
            # Truly not in cache, so we execute the agent.
            if response_obj is None:
                max_retries = 5
                base_delay = 2.0

                for attempt in range(max_retries + 1):
                    try:
                        response_obj = await agent.run(case["query"])
                        
                        # 5. Write to Disk
                        with open(cache_file_path, "w", encoding="utf-8") as f:
                            json.dump(response_obj.to_json(), f)
                        
                        # Success - exit retry loop
                        break

                    except Exception as e:
                        if is_rate_limit_error(e) and attempt < max_retries:
                            # Exponential Backoff + Jitter
                            # Jitter prevents thundering herd when multiple workers retry simultaneously
                            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                            
                            # Log to stdout so user sees it in pytest output
                            print(f"\n[429 Rate Limit] Retrying agent execution in {delay:.2f}s... (Attempt {attempt+1}/{max_retries + 1})")
                            await asyncio.sleep(delay)
                            continue
                        
                        # If not rate limit, or max retries exceeded, fail hard.
                        captured_error = e
                        # Update report with error info
                        request.node._eval_data["outputs.response"] = f"Agent Execution Failed: {str(e)}"
                        break

    if captured_error:
        # Fail the test if the agent execution crashed
        pytest.fail(f"Agent execution failed: {captured_error}")

    verifier = response_obj

    # --- Update Evaluation Data with Success ---
    # Update outputs with actual response
    request.node._eval_data["outputs.response"] = verifier.output_text
    request.node._eval_data["outputs.tool_calls"] = verifier.tool_calls
    request.node._eval_data["outputs.tool_definitions"] = verifier.tool_definitions
    
    return verifier


# --- 3. Smart Evaluators (Auto-Recording) ---

def _get_evaluator_registry():
    """
    Lazy loader for evaluator registry to avoid heavy top-level imports.
    This significantly speeds up test discovery.
    """
    from azure.ai.evaluation import (
        RelevanceEvaluator,
        CoherenceEvaluator,
        FluencyEvaluator,
        GroundednessEvaluator,
        ToolCallAccuracyEvaluator,
        BleuScoreEvaluator,
        F1ScoreEvaluator,
        GleuScoreEvaluator,
        IntentResolutionEvaluator,
        MeteorScoreEvaluator,
        ResponseCompletenessEvaluator,
        RetrievalEvaluator,
        RougeScoreEvaluator,
        SimilarityEvaluator,
        TaskAdherenceEvaluator,
        DocumentRetrievalEvaluator,
    )
    from azure.ai.evaluation._evaluators._tool_input_accuracy import _ToolInputAccuracyEvaluator
    from azure.ai.evaluation._evaluators._task_completion import _TaskCompletionEvaluator
    from azure.ai.evaluation._evaluators._task_navigation_efficiency import _TaskNavigationEfficiencyEvaluator
    from azure.ai.evaluation._evaluators._tool_call_success import _ToolCallSuccessEvaluator
    from azure.ai.evaluation._evaluators._tool_output_utilization import _ToolOutputUtilizationEvaluator
    from azure.ai.evaluation._evaluators._tool_selection import _ToolSelectionEvaluator

    return {
        "coherence": CoherenceEvaluator,
        "fluency": FluencyEvaluator,
        
        "tool_call_accuracy": ToolCallAccuracyEvaluator,
        "tool_input_accuracy": _ToolInputAccuracyEvaluator,
        "task_completion": _TaskCompletionEvaluator,
        "task_navigation_efficiency": _TaskNavigationEfficiencyEvaluator,
        "tool_call_success": _ToolCallSuccessEvaluator,
        "tool_output_utilization": _ToolOutputUtilizationEvaluator,
        "tool_selection": _ToolSelectionEvaluator,

        "intent_resolution": IntentResolutionEvaluator,
        "task_adherence": TaskAdherenceEvaluator,
        
        "similarity": SimilarityEvaluator,
        "f1_score": F1ScoreEvaluator,
        "bleu_score": BleuScoreEvaluator,
        "gleu_score": GleuScoreEvaluator,
        "rouge_score": RougeScoreEvaluator,
        "meteor_score": MeteorScoreEvaluator,
        
        "relevance": RelevanceEvaluator,
        "groundedness": GroundednessEvaluator,
        "retrieval": RetrievalEvaluator,
        "response_completeness": ResponseCompletenessEvaluator,
        "document_retrieval": DocumentRetrievalEvaluator,
    }


@pytest.fixture
def _judge_model_config(request):
    """
    Internal fixture that builds the SDK configuration object.
    Configuration must be provided via @pytest.mark.judge_model.
    """
    __tracebackhide__ = True  # Hide internal frames on failure

    marker = request.node.get_closest_marker("judge_model")
    
    if not marker:
        return None

    if marker.args:
        raise pytest.UsageError(f"Error in test '{request.node.nodeid}': @pytest.mark.judge_model requires keyword arguments (type=..., model=..., endpoint=...). Positional arguments are not supported.")

    config_type = marker.kwargs.get("type", "azure_openai")
    endpoint = marker.kwargs.get("endpoint")
    model = marker.kwargs.get("model")
    api_key = marker.kwargs.get("api_key")

    if config_type == "openai":
        from azure.ai.evaluation import OpenAIModelConfiguration
        # OpenAI Configuration
        return OpenAIModelConfiguration(
            type="openai",
            model=model,
            base_url=endpoint, # Optional
            api_key=api_key
        )
    
    else:
        from azure.ai.evaluation import AzureOpenAIModelConfiguration
        # Azure OpenAI Configuration (Default)
        if api_key:
            return AzureOpenAIModelConfiguration(
                type="azure_openai",
                azure_endpoint=endpoint,
                azure_deployment=model,
                api_key=api_key
            )
        else:
            return AzureOpenAIModelConfiguration(
                type="azure_openai",
                azure_endpoint=endpoint,
                azure_deployment=model
                # No API Key, will use DefaultAzureCredential
            )

@pytest.fixture(scope="session")
def _azure_credential():
    return DefaultAzureCredential()

@pytest.fixture(autouse=True)
def _auto_run_evaluators(request):
    """
    Automatically runs evaluators if the marker is present, 
    even if the user didn't request the evaluator_results fixture.
    """
    # Only auto-run if the marker is present
    if request.node.get_closest_marker("evaluator"):
        request.getfixturevalue("evaluator_results")

@pytest_asyncio.fixture
async def evaluator_results(request, agent_response, _dataset_case, _judge_model_config, record_property):
    """
    Universal fixture that runs the evaluator specified by @pytest.mark.evaluator.
    Returns an EvaluatorResults object.
    """
    __tracebackhide__ = True  # Hide internal frames on failure
    
    case = _dataset_case
    
    marker_evaluators = list(request.node.iter_markers("evaluator"))

    if not marker_evaluators:
        pytest.fail("MISSING MARKER: Please use @pytest.mark.evaluator('name', ...) to specify which evaluator to run.")

    # --- Common Inputs Recording ---
    inputs = {
        "query": case.get("query")
    }
    
    # Automatically add other dataset fields (e.g., ground_truth, context, id)
    for k, v in case.items():
        if k != "query" and not k.startswith("_"):
            inputs[k] = v

    record_property("inputs", inputs)

    # --- Common Outputs Recording ---
    outputs = {
        "response": agent_response.output_text,
        "tool_calls": agent_response.tool_calls,
        "tool_definitions": agent_response.tool_definitions,
    }

    record_property("outputs", outputs)
    
    # --- Reporting Hook Data Init ---
    flat_result = {}
    for k, v in inputs.items():
        flat_result[f"inputs.{k}"] = v
    flat_result["outputs.response"] = outputs["response"]
    flat_result["outputs.tool_calls"] = outputs["tool_calls"]
    flat_result["outputs.tool_definitions"] = outputs["tool_definitions"]
    flat_result["_case_key"] = f"{case.get('_test_id')}::{inputs['query']}"

    # final_result_obj will now be Dict[str, Dict] -- { "relevance": { "score": 4, "reason": ... } }
    final_result_obj = {}

    # --- Unified Evaluator Execution ---
    # We iterate over every @pytest.mark.evaluator on the test function.
    # This design allows multiple evaluators (Coherence, Relevance, Custom) to run on the single agent response.
    has_execution_error = False
    first_execution_error = None

    for mark in marker_evaluators:
        try:
            # Determine the evaluator name (e.g., 'coherence')
            name = mark.args[0] if mark.args else mark.kwargs.get("name")
            kwargs = mark.kwargs

            eval_name = name

            score = -1
            reason = None
            pass_fail = "pass"
            threshold = kwargs.get("threshold")
            eval_result_raw = {}

            # --- Branch A: Custom Prompt Evaluator ---
            if kwargs.get("prompt") is not None:
                prompt_file = kwargs.get("prompt")

                # Resolve prompt file path
                # 1. Absolute Path
                # 2. Relative to Test File
                prompt_text = prompt_file # default to assuming it's text (template)
                is_file = False
                
                if prompt_file:
                    # Try path resolution via pathlib "/" operator
                    # This automatically handles both:
                    # - Absolute path: test_dir / "C:/abs/path" -> "C:/abs/path"
                    # - Relative path: test_dir / "rel/path" -> "test_dir/rel/path"
                    test_file_dir = Path(request.node.fspath).parent
                    possible_path = test_file_dir / prompt_file
                    
                    if possible_path.exists() and possible_path.is_file():
                        prompt_text = str(possible_path)
                        is_file = True
                    else:
                        # Treat as inline template
                        pass
                
                eval_credential = None
                if _judge_model_config and _judge_model_config.get("type") == "azure_openai" and not _judge_model_config.get("api_key"):
                    eval_credential = request.getfixturevalue("_azure_credential")
                
                evaluator = PromptEvaluator(prompt_text, _judge_model_config, credential=eval_credential, is_file=is_file)
                
                # Prepare context for prompt replacement
                eval_context = {}
                # 1. From Dataset (all fields except id and internal ones)
                for k, v in case.items():
                    if k not in ["id", "_dataset", "_test_id"]:
                        eval_context[k] = v
                
                # 2. From Agent Response
                eval_context["response"] = agent_response.output_text
                eval_context["tool_calls"] = agent_response.tool_calls
                eval_context["tool_definitions"] = agent_response.tool_definitions
                
                # Ensure 'query' is present (standard field)
                if "query" not in eval_context:
                    eval_context["query"] = case.get("query", "")

                # Execute (Async needs to be handled? Wait, evaluator_results is synchronous?)
                # Ah, agent_response is async, but evaluator_results is sync.
                # We need to run sync here?
                result = await evaluator.run(eval_context)
                
                score = result["result"]
                reason = result["reason"]
                eval_result_raw = result

            # --- Branch B: Custom Code Evaluator ---
            elif kwargs.get("grader") is not None:
                grader = kwargs.get("grader")
                
                evaluator = CodeEvaluator(func_obj=grader)
                
                sample_payload = {
                    "output_text": agent_response.output_text,
                    "tool_calls": agent_response.tool_calls,
                    "tool_definitions": agent_response.tool_definitions
                }
                item_payload = case.copy()

                result = await asyncio.to_thread(evaluator.run, sample_payload, item_payload)
                score = result["result"]
                reason = result["reason"]
                eval_result_raw = result

            # --- Branch C: Built-in Evaluator ---
            else:
                registry = _get_evaluator_registry()
                eval_class = registry.get(eval_name)
                
                if not eval_class:
                    raise ValueError(f"UNKNOWN EVALUATOR: '{eval_name}' is not registered. Available: {list(registry.keys())}")

                # Introspect __init__
                init_sig = inspect.signature(eval_class.__init__)
                init_kwargs = {}

                if "model_config" in init_sig.parameters:
                    if _judge_model_config:
                        init_kwargs["model_config"] = _judge_model_config
                    elif init_sig.parameters["model_config"].default == inspect.Parameter.empty:
                        raise ValueError(f"MISSING CONFIG: '{eval_name}' requires 'judge_model', but fixture returned None.")
                
                if "credential" in init_sig.parameters:
                    if _judge_model_config and "azure_endpoint" in _judge_model_config and not _judge_model_config.get("api_key"):
                        eval_credential = request.getfixturevalue("_azure_credential")
                        init_kwargs["credential"] = eval_credential

                if threshold is not None and "threshold" in init_sig.parameters:
                    init_kwargs["threshold"] = threshold

                try:
                    evaluator = eval_class(**init_kwargs)
                except Exception as e:
                    raise RuntimeError(f"Failed to instantiate evaluator '{eval_name}': {e}")
                
                COMPLEX_EVALUATORS = {
                    "tool_call_accuracy", 
                    "task_adherence", 
                    "intent_resolution",
                    "tool_input_accuracy",
                    "task_completion",
                    "task_navigation_efficiency",
                    "tool_call_success",
                    "tool_output_utilization",
                    "tool_selection",
                }

                run_kwargs = {
                    "query": case.get("query"),
                    "response": agent_response.output_text,
                    "tool_calls": agent_response.tool_calls,
                    "tool_definitions": agent_response.tool_definitions
                }
                
                if eval_name in COMPLEX_EVALUATORS:
                    run_kwargs["response"] = _convert_to_evaluator_format(agent_response)
                    query_content = case.get("query")
                    user_content = query_content
                    if isinstance(query_content, str):
                        user_content = [{"type": "text", "text": query_content}]
                     
                    complex_query = [
                        {"role": "user", "content": user_content}
                    ]
                    if agent_response.instructions:
                        complex_query.insert(0, {
                            "role": "system", 
                            "content": agent_response.instructions
                        })
                    run_kwargs["query"] = complex_query
                     
                    flat_result["inputs.query"] = complex_query
                    flat_result["outputs.response"] = _convert_to_evaluator_format(agent_response)
                
                if "context" in case:
                    run_kwargs["context"] = case["context"]
                if "ground_truth" in case:
                    run_kwargs["ground_truth"] = case["ground_truth"]
                if "retrieval_ground_truth" in case:
                    run_kwargs["retrieval_ground_truth"] = case["retrieval_ground_truth"]
                if "retrieved_documents" in case:
                    run_kwargs["retrieved_documents"] = case["retrieved_documents"]

                retries = 3
                eval_result = None
                last_error = None
                
                for attempt in range(retries + 1):
                    try:
                        run_func = partial(evaluator, **run_kwargs)
                        eval_result = await asyncio.to_thread(run_func)
                        break
                    except Exception as e:
                        last_error = e
                        
                        if is_rate_limit_error(e) and attempt < retries:
                            # Add jitter to prevent thundering herd in parallel execution
                            delay = min(2 ** attempt, 10) + random.uniform(0, 1)
                            await asyncio.sleep(delay)
                        else:
                            # Don't retry on other errors
                            break 
                
                if eval_result is None:
                    raise RuntimeError(f"Evaluator '{eval_name}' failed after {attempt + 1} attempt(s) (max retries: {retries}): {last_error}")
                
                eval_result_raw = eval_result

                # Extract threshold from result if not provided by user
                if threshold is None:
                    threshold = eval_result.get(f"{eval_name}_threshold")
                
                # Extract score
                score = eval_result.get(eval_name) or -1
                if score == -1:
                    score = eval_result.get(f"gpt_{eval_name}", -1)
                
                # Extract reason
                reason = eval_result.get(f"{eval_name}_reason")
                if not reason:
                    reason = eval_result.get(f"gpt_{eval_name}_reason")

            # --- Common Pass/Fail Logic ---
            
            is_builtin = kwargs.get("prompt") is None and kwargs.get("grader") is None

            # 1. Check for explicit result from built-in evaluator
            explicit_result = eval_result_raw.get(f"{eval_name}_result") if is_builtin else None
            
            if explicit_result is not None:
                pass_fail = explicit_result

            # 2. Fallback to Threshold Comparison
            elif threshold is not None:
                if isinstance(threshold, bool):
                    bool_score = str(score).lower() == "true" if isinstance(score, str) else bool(score)
                    if bool_score != threshold:
                        pass_fail = "fail"
                elif isinstance(threshold, (int, float)):
                    try:
                        num_score = float(score)
                        if num_score < threshold:
                            pass_fail = "fail"
                    except:
                        pass

            # --- Recording ---
            flat_result[f"outputs.{eval_name}.score"] = score
            
            # Only record raw output for built-in evaluators as custom ones are redundant (just score/reason)
            is_builtin = kwargs.get("prompt") is None and kwargs.get("grader") is None
            if is_builtin:
                flat_result[f"outputs.{eval_name}.raw"] = eval_result_raw

            if reason:
                flat_result[f"outputs.{eval_name}.reason"] = reason

            flat_result[f"outputs.{eval_name}.result"] = pass_fail
            if threshold is not None:
                flat_result[f"outputs.{eval_name}.threshold"] = threshold
                
            structured_data = {
                "score": score,
                "result": pass_fail,
                "threshold": threshold,
                "reason": reason,
            }
            
            if is_builtin:
                structured_data["raw"] = eval_result_raw
            
            final_result_obj[eval_name] = structured_data
        
        except Exception as e:
            # Catch execution errors for this specific evaluator so we can continue with others
            # or at least save the results we have.
            has_execution_error = True
            if not first_execution_error:
                first_execution_error = e
            
            eval_name = mark.args[0] if mark.args else mark.kwargs.get("name")
            
            flat_result[f"outputs.{eval_name}.result"] = "error"
            flat_result[f"outputs.{eval_name}.reason"] = str(e)
            
            final_result_obj[eval_name] = {
                "score": 0,
                "result": "error",
                "reason": str(e),
                "threshold": mark.kwargs.get("threshold")
            }

    record_property("evaluators", final_result_obj)
            
    # Merge flat results from agent_response (which includes custom eval data)
    if hasattr(request.node, "_eval_data"):
        previous_data = request.node._eval_data
        
        # Protect complex data (Lists) from being overwritten by simple data (Strings) from previous_data
        for field in ["inputs.query", "outputs.response"]:
            if field in flat_result and isinstance(flat_result[field], list):
                if field in previous_data and isinstance(previous_data[field], str):
                    del previous_data[field]
                    
        flat_result.update(previous_data)

    request.node._eval_data = flat_result

    if has_execution_error:
        pytest.fail(f"Evaluator execution failed: {first_execution_error}")

    # --- Rich Console Output (Per-test Details) ---
    print("\n" + "=" * 80)
    print(f"QUERY:    {inputs['query']}")
    print(f"RESPONSE: {textwrap.shorten(outputs['response'], width=70, placeholder='...')}")
    print("-" * 80)

    # Helper to print eval line
    def _print_eval_line(name, score, result, reason, threshold=None):
        status = result.upper() if result else "UNKNOWN"
        # Color simulation (VS Code terminal supports ANSI)
        icon = "[PASS]" if status == "PASS" else "[FAIL]"
        thresh_info = f" (Threshold: {threshold})" if threshold is not None else ""
        print(f"{icon} {name}: {score}{thresh_info}")
        if reason:
            print(f"       Reason: {textwrap.shorten(str(reason), width=70, placeholder='...')}")

    # Print results from final_result_obj (covers both built-in and custom)
    for name, data in final_result_obj.items():
        _print_eval_line(
            name, 
            data.get("score"), 
            data.get("result"), 
            data.get("reason"), 
            data.get("threshold")
        )

    print("=" * 80 + "\n")

    return EvaluatorResults(final_result_obj)

# --- 4. Reporting Hooks ---

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    
    # Save results during 'call' (execution) OR 'setup' (fixture failure) phases
    if report.when in ("call", "setup") and hasattr(item, "_eval_data"):
        # Write the result to a file in the shared cache directory
        # This works for both single process and xdist (parallel) execution
        try:
            results_dir = Path(item.config.cache.makedir("agent_eval_results"))
            # Generate a unique filename using the test nodeid hash
            filename = hashlib.md5(item.nodeid.encode("utf-8")).hexdigest() + ".json"
            
            with open(results_dir / filename, "w", encoding="utf-8") as f:
                json.dump(item._eval_data, f)
        except Exception as e:
            # Fallback (mostly for debugging, or if cache isn't available)
            pass

def pytest_sessionfinish(session, exitstatus):
    # Only the main process (controller) should aggregate and write the final report
    if hasattr(session.config, "workerinput"):
        return

    # Collect all results from the staging directory
    results = []
    
    try:
        results_dir = Path(session.config.cache.makedir("agent_eval_results"))
        if results_dir.exists():
            for result_file in results_dir.iterdir():
                if result_file.is_file() and result_file.suffix == ".json":
                    try:
                        with open(result_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            results.append(data)
                    except Exception:
                        pass
    except Exception:
        pass

    if not results:
        return
        
    # Merge results by case
    merged_results = {}
    
    for result in results:
        key = result.pop("_case_key")
        
        if key not in merged_results:
            merged_results[key] = result
        else:
            # Data Preservation Strategy:
            # Some evaluators (like 'tool_call_accuracy') might produce rich, structured data (Lists/Dicts) for inputs/outputs,
            # whereas others might default to simple string representations.
            # We want to ensure we don't overwrite a rich data structure with a simple string when merging multiple result files for the same test case.
            
            for field in ["inputs.query", "outputs.response"]:
                if field in merged_results[key] and isinstance(merged_results[key][field], list):
                    if field in result and isinstance(result[field], str):
                        # Remove the simpler string version from the new result so it doesn't overwrite the existing rich data
                        del result[field]

            # Merge the new result into the existing one
            merged_results[key].update(result)
            
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Best Practice: Store artifacts in a dedicated directory
    output_dir = Path(session.config.rootdir) / "test-results"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"evaluation_results_{timestamp}.json"
    
    # Prepare final output object
    final_output = {
        "rows": list(merged_results.values())
    }

    # Store for terminal summary
    session.config._final_evaluation_results = merged_results

    with open(output_file, "w") as f:
        json.dump(final_output, f, indent=2)

    print(f"\nEvaluation results saved to: {output_file.absolute()}")

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Print a summary table of evaluation results aggregated by Evaluator.
    """
    if not hasattr(config, "_final_evaluation_results"):
        return

    results = config._final_evaluation_results
    if not results:
        return

    terminalreporter.section("Evaluation Metrics", sep="=")
    
    # Aggregation: { "eval_name": { "scores": [], "passes": 0, "fails": 0 } }
    metrics = {}
    
    for case_id, data in results.items():
        for k, v in data.items():
            # Identify evaluator outputs by pattern "outputs.{name}.score"
            if k.startswith("outputs.") and k.endswith(".score"):
                eval_name = k.split(".")[1]
                
                if eval_name not in metrics:
                    metrics[eval_name] = {"scores": [], "passes": 0, "fails": 0}
                
                score = v
                # Ensure score is numeric for stats
                if isinstance(score, (int, float)):
                    metrics[eval_name]["scores"].append(score)
                else:
                    # Treat non-numeric scores (like 'N/A') cautiously
                    pass
                
                # Check pass/fail result
                res_key = f"outputs.{eval_name}.result"
                result_val = data.get(res_key, "pass") # Default to pass
                
                if result_val == "fail":
                    metrics[eval_name]["fails"] += 1
                else:
                    metrics[eval_name]["passes"] += 1

    if not metrics:
        terminalreporter.write_line("No evaluation metrics found.")
        return

    # Print Table
    # Evaluator (20) | Count (5) | Pass % (6) | Avg (5) | Min (5) | Max (5)
    header = f"{'Evaluator':<20} | {'Count':<5} | {'Pass %':<6} | {'Avg':<5} | {'Min':<5} | {'Max':<5}"
    terminalreporter.write_line(header)
    terminalreporter.write_line("-" * len(header))
    
    for name, stats in metrics.items():
        count = stats["passes"] + stats["fails"]
        pass_rate = (stats["passes"] / count * 100) if count > 0 else 0
        
        scores = stats["scores"]
        if scores:
            avg_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)
        else:
            avg_score = 0
            min_score = 0
            max_score = 0
            
        line = f"{name:<20} | {count:<5} | {pass_rate:5.1f}% | {avg_score:<5.2f} | {min_score:<5.2f} | {max_score:<5.2f}"
        terminalreporter.write_line(line)
    
    terminalreporter.write_line("-" * len(header))
    terminalreporter.write_line("")
