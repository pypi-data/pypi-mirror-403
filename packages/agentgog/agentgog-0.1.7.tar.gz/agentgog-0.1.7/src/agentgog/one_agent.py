import os
from smolagents import OpenAIModel

from smolagents import CodeAgent,  InferenceClientModel, DuckDuckGoSearchTool, WebSearchTool
from smolagents import tool

import datetime as dt
import sympy, pandas, numpy
import click
from console import fg, bg


models_free = [ "nex-agi/deepseek-v3.1-nex-n1:free" # c03 refaktoroval; c05 all API KEYs;  !!!ONLY THIS ONE TRANASLATED C09
#              "z-ai/glm-4.5-air:free", # volal c04 erf! ; On c05 - got stuck-slow
#              "allenai/olmo-3.1-32b-think:free",
#              "google/gemma-3-27b-it:free", # ZPRASILA C03 odpoved! ; chce scpiy-jinak obycejne secte delty!
#              "openai/gpt-oss-20b:free", # limit
#               "meta-llama/llama-3.3-70b-instruct:free", # c04 chce scipy jinak SUMdh-erf; c05 dal, ale nema faktory jen34km
#              "nousresearch/hermes-3-llama-3.1-405b:free", # missed answer c03 - tries to interpolate!; c04 chce scipy.integrate
#              "meta-llama/llama-3.1-405b-instruct:free", #f ; - ocural vysl 4 x nevi evalf; API googlemaps - pak 10x nesmysl
#              "openai/gpt-oss-120b:free"
              ]


# ================================================================================
# SYSTEM_PROMPTS
# --------------------------------------------------------------------------------

SYSTEM_PROMPT_TRANSLATOR = '''You are a Czech-English professional translator with specialization on subtitles. You understand the strict SRT format with segment number, formated timing information, text and an empty line. It is crucial to keep the exact format with segment number and timing information and empty lines! Translate the given prompt - SRT subtitles - from English to Czech and keep the EXACT SRT information, do not add nor explanations neither comments. Pay extra attention to empty lines, they must be repeated in the same place as they are in the input.
To solve the task, you must plan forward to proceed in a series of steps, in a cycle of Thought, Code, and Observation sequences.

At each step, in the 'Thought:' sequence, you should first explain your reasoning for the translation - it is trivial here.
Then in the Code sequence you should write the code in simple Python to pass the translation to the next stage, it is a simple print() function. The code sequence must be opened with '<code>', and closed with '</code>'.
During intermediate step - though not expected for translations - you can use 'print()' to save whatever important information you will then need.
These print outputs will then appear in the 'Observation:' field, which will be available as input for the next step.
In the end you have to return a final answer using the `final_answer` tool.

Here is an example using final_answer tool:
---
Task: "35
00:04:09,080 --> 00:04:10,400                                                                                                                             There is a

36
00:04:10,400 --> 00:04:12,080
 significant portion

"
Thought: I will translate from English to Czech keeping the exact SRT structure.
<code>
final_answer("""35
00:04:09,080 --> 00:04:10,400                                                                                                                             Je to

36
00:04:10,400 --> 00:04:12,080
 významná část

""")
<code>

---
Task: "This is a test."
Thought: I will translate from English to Czech keeping the exact SRT structure.
<code>
final_answer("Toto je test.")
<code>
'''



# ================================================================================
#  TOOL definition
# --------------------------------------------------------------------------------

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


# ================================================================================
# split model name
# --------------------------------------------------------------------------------

def log_event(**kwargs):
    """Log an event in a bash-parseable format."""
    timestamp = dt.datetime.now().isoformat()
    log_line = f"[LOG] TIMESTAMP={timestamp}"
    for key, value in kwargs.items():
        if value is not None:
            log_line += f"|{key}={value}"
    with open("log_translator.txt", "a") as f:
        f.write(log_line + "\n")


def get_model_idshort(model_id):
    """
    Return short model  name
    """
    return model_id.split("/")[-1].split(":")[0]

# ================================================================================
# RUn task
# --------------------------------------------------------------------------------

def run_task( model_id, question ):
    """
    run one task, write to filename CXY_*.txt
    """
    ts_start = dt.datetime.now()
    model_idshort = get_model_idshort(model_id)
    filename = f"log_translator.txt"

    log_event(
        MODEL=model_id,
        MODEL_SHORT=model_idshort,
        EVENT="TASK_START",
        DURATION_SEC=None,
        INPUT_FILE=None,
        OUTPUT_FILE=None,
        STATUS="SUCCESS"
    )

    model = OpenAIModel(
        model_id= model_id,
        api_base="https://openrouter.ai/api/v1", # Leave this blank to query OpenAI servers.
        api_key=os.environ["OPENROUTER_API_KEY"], # Switch to the API key for the server you're targeting.
    )
    # Create an agent with no tools         # tools=[DuckDuckGoSearchTool()],
    result = ""

    with CodeAgent(    tools=[read_file],
# #        tools=[WebSearchTool()],
# #        additional_authorized_imports=["sympy", "numpy", "pandas"],
# #        executor_type="modal",  # doesnt work, do not use
        model=model) as agent:

        agent.prompt_templates["system_prompt"] =  SYSTEM_PROMPT_TRANSLATOR
        # print(agent.system_prompt) # save the prompt to the disk

        # Run the agent with a task
        result = agent.run(question)
        # print(result) # DEBUG

    ts_end = dt.datetime.now()
    duration = (ts_end - ts_start).total_seconds()
    log_event(
        MODEL=model_id,
        MODEL_SHORT=model_idshort,
        EVENT="TASK_END",
        DURATION_SEC=f"{duration:.3f}",
        INPUT_FILE=None,
        OUTPUT_FILE=None,
        STATUS="SUCCESS"
    )

    # ---------------------- return the result
    return result

# ==============================================  MAIN ===========================
# ==============================================  MAIN ===========================
# ==============================================  MAIN ===========================
@click.group()
def cli():
    pass

@cli.command("translator")
@click.option("--input", "-i", "inputfile", required=True, help="Input SRT file to translate")
@click.option("--model", default=models_free[0], help="Model to use for translation")
def translator(inputfile, model):
    """Translate SRT subtitles from English to Czech."""
    OUTPUTFILE_a, OUTPUTFILE_ext = os.path.splitext(inputfile)
    srt = ""
    with open(inputfile) as f:
        srt = f.read()

    PROMPT = f"{srt}"
    print(f"i... {bg.green}{fg.white} MODEL {model} {bg.default}{fg.default}")
    ans = run_task(model, PROMPT)
    output_path = f"{OUTPUTFILE_a}_cs{OUTPUTFILE_ext}"
    with open(output_path, "w") as f:
        f.write(f"{ans}")

    log_event(
        MODEL=model,
        MODEL_SHORT=get_model_idshort(model),
        EVENT="OUTPUT_WRITE",
        DURATION_SEC=None,
        INPUT_FILE=inputfile,
        OUTPUT_FILE=output_path,
        STATUS="SUCCESS"
    )

    print(f"i... FINISHED {inputfile}")

# ======================================================================================
if __name__ == "__main__":
    cli()
