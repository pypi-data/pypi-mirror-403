import os
import datetime as dt

from smolagents import OpenAIModel, CodeAgent, tool

from smol_common import setup_logger, log_event, get_model_idshort


setup_logger(name="smol_translator")

MODELS_FREE = [
    "google/gemma-3-27b-it:free",
    "xiaomi/mimo-v2-flash:free",
    "nex-agi/deepseek-v3.1-nex-n1:free"
]


TIMESTAMP_EXAMPLE_1 = "00:04:09,080 --> 00:04:10,400"
TIMESTAMP_EXAMPLE_2 = "00:04:10,400 --> 00:04:12,080"

SYSTEM_PROMPT = f"""You are a Czech-English professional translator with specialization on subtitles. You understand the strict SRT format with segment number, formatted timing information, text, and an empty line. It is crucial to keep the exact format with segment number and timing information along with empty lines! Translate the given prompt - SRT subtitles - from English to Czech and keep the EXACT SRT information; do not add any explanations or comments. Pay extra attention to empty lines; they must appear in the same positions as the input.
To solve the task, you must plan forward to proceed in a series of steps, in a cycle of Thought, Code, and Observation sequences.

At each step, in the 'Thought:' sequence, you should first explain your reasoning for the translation - it is trivial here.
Then in the Code sequence you should write the code in simple Python to pass the translation to the next stage, usually a simple print() function. The code sequence must be opened with '<code>', and closed with '</code>'.
During an intermediate step - though not expected for translations - you can use 'print()' to save whatever important information you will then need.
These print outputs will then appear in the 'Observation:' field, which will be available as input for the next step.
In the end you have to return a final answer using the `final_answer` tool.

Here is an example using final_answer tool:
---
Task: "35
{TIMESTAMP_EXAMPLE_1}                                                                                                                             There is a

36
{TIMESTAMP_EXAMPLE_2}
  significant portion

"
Thought: I will translate from English to Czech keeping the exact SRT structure.
<code>
final_answer('''35
{TIMESTAMP_EXAMPLE_1}                                                                                                                             Je to

36
{TIMESTAMP_EXAMPLE_2}
  významná část

''')
</code>

---
Task: "This is a test."
Thought: I will translate from English to Czech keeping the exact SRT structure.
<code>
final_answer("Toto je test.")
</code>
"""


@tool
def read_file(filename: str) -> str | None:
    """
    This is a tool that returns a content of the filename
    
    Args:
        filename: The filename
    
    Returns:
        A string containing the content of the file.
    """
    content = None
    try:
        with open(filename) as f:
            content = f.read()
    except:
        return None
    return content


def translate_srt(model_id: str, srt_content: str) -> str:
    """
    Translate SRT subtitles from English to Czech
    
    Args:
        model_id: Model identifier to use
        srt_content: SRT content to translate
    
    Returns:
        Translated SRT content
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

    model = OpenAIModel(
        model_id=model_id,
        api_base="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    result = ""

    with CodeAgent(
        tools=[read_file],
        model=model
    ) as agent:
        agent.prompt_templates["system_prompt"] = SYSTEM_PROMPT
        result = agent.run(srt_content, reset=True, max_steps=3)

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
