import os
import io
import datetime as dt
from pathlib import Path

import qrcode
from smolagents import OpenAIModel, CodeAgent, tool

from smol_common import setup_logger, log_event, get_model_idshort


setup_logger(name="smol_qrpayment")

MODELS_FREE = [
    "google/gemma-3-27b-it:free",
    "xiaomi/mimo-v2-flash:free",
    "nex-agi/deepseek-v3.1-nex-n1:free"
]


SYSTEM_PROMPT = """You are a QR payment coordinator specializing in extracting payment details from user-provided text. Analyze the given text to identify key payment coordinates such as account number, amount, currency, variable symbol (VS), constant symbol (KS), specific symbol (SS), date, and message. Ensure the account is in the format full account (e.g., "1234567890/0300"). If any details are missing, use defaults: amount=0, currency='CZK', vs='', ks='', ss='', date=None, message=''.

To solve the task, you must plan forward to proceed in a series of steps, in a cycle of Thought, Code, and Observation sequences.

At each step, in the 'Thought:' sequence, you should first explain your reasoning for extracting the payment details.
Then in the Code sequence you should use the `generate_qr` tool to create the QR code for the payment with the extracted details. The code sequence must be opened with '<code>', and closed with '</code>'.
During intermediate steps - if any -  you can use 'print()' to save important information for the next step.
These print outputs will appear in the 'Observation:' field as input for the next step.
In the end, you have to return a final answer using the `final_answer` tool, providing the path to the generated QR code file.

Here is an example using final_answer tool:
---
Task: "Transfer 500 CZK to account 1234567890/0300 with message 'Invoice payment'."
Thought: I need to extract payment details: account='1234567890/0300', amount=500, currency='CZK', message='Invoice payment'. Then use generate_qr to create the QR code.
<code>
img_filename = generate_qr(account="1234567890/0300", amount=500, currency="CZK", message="Invoice payment")
final_answer(f"{img_filename}")
</code>

---
Task: "Pay 100 to 0987654321/0800 with VS 123456 on 2023-10-15."
Thought: Extract details: account='0987654321/0800', amount=100, vs='123456', date='2023-10-15'.
<code>
img_filename = generate_qr(account="0987654321/0800", amount=100, vs="123456", date="2023-10-15")
final_answer(f"{img_filename}")
</code>
"""


ALPHA2NUM = {
    'A': 10, 'B': 11, 'C': 12, 'D': 13, 'E': 14, 'F': 15,
    'G': 16, 'H': 17, 'I': 18, 'J': 19, 'K': 20, 'L': 21,
    'M': 22, 'N': 23, 'O': 24, 'P': 25, 'Q': 26, 'R': 27,
    'S': 28, 'T': 29, 'U': 30, 'V': 31, 'W': 32, 'X': 33,
    'Y': 34, 'Z': 35
}


def mod_97_10(number_str: str) -> str:
    remainder = int(number_str) % 97
    res = 98 - remainder
    res = str(res)
    if len(res) < 2:
        res = f"0{res}"
    return res


def alphanum_to_num(iban2: str, mapping: dict) -> str:
    result = []
    for ch in iban2:
        if ch.isdigit():
            result.append(ch)
        elif ch.isalpha() and ch.isupper():
            result.append(str(mapping[ch]))
        else:
            raise ValueError("Invalid character in input")
    return ''.join(result)


def verify_iban(iban: str) -> bool:
    iban2 = f"{iban[4:]}{iban[:4]}"
    iban3 = alphanum_to_num(iban2, ALPHA2NUM)
    res = int(iban3) % 97
    return res == 1


def calc_iban(bban: str = "300497813/0300", ccode: str = "CZ") -> str:
    bb1 = bban
    if ccode == "CZ":
        acc, bank = bban.split("/")
        pref = ""
        numb = acc
        if "-" in acc:
            pref, numb = acc.split("-")
        if len(numb) < 10:
            nul = 10 - len(numb)
            numb = f"{"0"*nul}{numb}"
        if len(pref) < 6:
            nul = 6 - len(pref)
            pref = f"{"0"*nul}{pref}"
        bb1 = f"{bank}{pref}{numb}"
    bb1 = bb1.replace("/", "").replace(" ","").replace("-", "")
    aiban3 = f"{bb1}{ALPHA2NUM[ccode[0]]}{ALPHA2NUM[ccode[1]]}00"
    if not aiban3.isdigit():
        raise ValueError("Input must be a string of digits.")
    check = mod_97_10(aiban3)
    aiban4 = f"{ccode}{check}{bb1}"
    if verify_iban(aiban4):
        return aiban4
    else:
        raise ValueError("Invalid IBAN")


@tool
def generate_qr(account: str, amount: float = 0, currency: str = "CZK", vs: str = "", ks: str = "", ss: str = "", date: str = "", message: str = "") -> str:
    """
    Generate a QR code for payment based on given parameters. Generates a unique filename for the QR code PNG.
    
    Args:
        account: The account number (e.g., "1234567890/0300")
        amount: The amount to transfer
        currency: Currency code (default CZK)
        vs: Variable symbol
        ks: Constant symbol
        ss: Specific symbol
        date: Date in YYYY-MM-DD format
        message: Payment message
    
    Returns:
        The unique filename of the generated QR code PNG.
    """
    log_event(EVENT="TOOL_CALL", TOOL="generate_qr", ACCOUNT=account, AMOUNT=str(amount), CURRENCY=currency, VS=vs, KS=ks, SS=ss, DATE=date, MESSAGE=message)

    unique_id = f"{account}_{amount}".replace("/", "_").replace(",", "_").replace(".", "_")
    temp_filename = f"payment_qr_{unique_id}.png"
    temp_path = Path(temp_filename)

    date_str = ''
    if date:
        try:
            date_obj = dt.datetime.strptime(date, '%Y-%m-%d')
            date_str = date_obj.strftime('%Y%m%d')
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

    iban = calc_iban(account, ccode="CZ")

    spayd_parts = [
        f"SPD*1.0",
        f"ACC:{iban}",
        f"AM:{amount:.2f}",
        f"CC:{currency}"
    ]

    if vs:
        spayd_parts.append(f"X-VS:{vs}")
    if ks:
        spayd_parts.append(f"X-KS:{ks}")
    if ss:
        spayd_parts.append(f"X-SS:{ss}")
    if message:
        spayd_parts.append(f"MSG:{message}")
    if date_str:
        spayd_parts.append(f"DT:{date_str}")

    spayd_string = '*'.join(spayd_parts)

    qr = qrcode.QRCode()
    qr.add_data(spayd_string)

    f = io.StringIO()
    qr.print_ascii(out=f)
    f.seek(0)
    print(f.read())

    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    with open(str(temp_path), 'wb') as f:
        img.save(f)

    log_event(EVENT="QR_GENERATED", OUTPUT_FILE=str(temp_path))

    return str(temp_path)


def generate_payment_qr(model_id: str, prompt: str) -> str:
    """
    Generate QR code for payment based on text prompt
    
    Args:
        model_id: Model identifier to use
        prompt: Text prompt describing the payment
    
    Returns:
        Path to generated QR code file
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
        tools=[generate_qr],
        model=model
    ) as agent:
        agent.prompt_templates["system_prompt"] = SYSTEM_PROMPT
        result = agent.run(prompt, reset=True, max_steps=3)

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
