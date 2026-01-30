import os
import datetime as dt

from smolagents import OpenAIModel, LiteLLMModel, CodeAgent, tool
from smolagents import DuckDuckGoSearchTool, WebSearchTool

from smol_common import setup_logger, log_event, get_model_idshort

import pandas, numpy, sympy
import matplotlib, matplotlib.pyplot

setup_logger(name="smol_codeagent")

MODELS_FREE = [
    "google/gemma-3-27b-it:free",
    "xiaomi/mimo-v2-flash:free",
    "nex-agi/deepseek-v3.1-nex-n1:free"
]


def run_codeagent(model_id: str, prompt: str, max_steps: int = 10, provider: str = "openrouter") -> str:
    """
    Run vanilla CodeAgent with built-in prompt

    Args:
        model_id: Model identifier to use
        prompt: User prompt/task description
        max_steps: Maximum number of steps (default: 10)
        provider: Provider to use ('openrouter' or 'ollama')

    Returns:
        Result from CodeAgent execution
    """
    ts_start = dt.datetime.now()
    model_idshort = get_model_idshort(model_id)

    log_event(
        MODEL=model_id,
        EVENT="TASK_START",
        DURATION_SEC=None,
        INPUT_FILE=None,
        OUTPUT_FILE=None,
        STATUS="SUCCESS"
    )

    # Select model based on provider
    if provider == "ollama":
        # Use LiteLLMModel for Ollama
        model = LiteLLMModel(
            model_id=f"ollama/{model_id}",
            api_base="http://localhost:11434",
            api_key="ollama"  # LiteLLM requires an api_key even for Ollama
        )
    else:
        # Use OpenAIModel for OpenRouter
        model = OpenAIModel(
            model_id=model_id,
            api_base="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
        )

    result = ""

    with CodeAgent(
        tools=[WebSearchTool()],  # No additional tools - use default CodeAgent tools
            additional_authorized_imports=["sympy", "numpy", "pandas", "matplotlib", "matplotlib.pyplot"],
        model=model
    ) as agent:
        # Use built-in system prompt - no custom prompt override
        result = agent.run(prompt,
                           reset=True,
                           max_steps=max_steps)

    ts_end = dt.datetime.now()
    duration = (ts_end - ts_start).total_seconds()
    log_event(
        MODEL=model_id,
        EVENT="TASK_END",
        DURATION_SEC=f"{duration:.1f}",
        INPUT_FILE=None,
        OUTPUT_FILE=None,
        STATUS="SUCCESS"
    )

    return result
