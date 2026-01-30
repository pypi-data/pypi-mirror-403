#!/usr/bin/env python3
"""
CLI interface for AI message classifier
"""
import sys
import os
import logging
import click
from console import fg, fx
import datetime as dt
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai_classifier import classify_message
from calendar_extractor import extract_calendar_details, add2calendar
from task_extractor import extract_task_details, add2task
from memo_extractor import extract_memo_details, add2keep
from provider import (
    chat_with_provider, 
    PROVIDER_OPENROUTER, 
    PROVIDER_OLLAMA, 
    get_default_model,
    validate_provider
)
from openrouter_client import OPENROUTER_MODEL
from smol_translator import translate_srt, MODELS_FREE as TRANSLATOR_MODELS
from smol_qrpayment import generate_payment_qr, MODELS_FREE as QRPAYMENT_MODELS
from smol_codeagent import run_codeagent, MODELS_FREE as CODEAGENT_MODELS

LOG_FILE = os.path.expanduser('~/agentgog.log')


def setup_logger():
    """Configure file logger for agentgog"""
    logger = logging.getLogger('agentgog')
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(LOG_FILE)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    return logger


logger = setup_logger()


def colorize(text, color):
    """Add color to text"""
    colors = {
        'green': fg.green,
        'blue': fg.cyan,
        'yellow': fg.yellow,
        'red': fg.red,
        'white': fg.default
    }
    color_func = colors.get(color, fg.default)
    return color_func + text + fg.default


def format_output(text):
    """Format text with basic styling"""
    result = text
    result = result.replace('[bold]', f"{fx.bold}")
    result = result.replace('[/bold]', f"{fx.default}")
    result = result.replace('[dim]', f"{fx.dim}")
    result = result.replace('[/dim]', f"{fx.default}")
    result = result.replace('[bold green]', f"{fx.bold}{fg.green}")
    result = result.replace('[/bold green]', f"{fx.default}{fg.default}")
    result = result.replace('[bold red]', f"{fx.bold}{fg.red}")
    result = result.replace('[/bold red]', f"{fx.default}{fx.default}")
    result = result.replace('[bold cyan]', f"{fx.bold}{fg.cyan}")
    result = result.replace('[/bold cyan]', f"{fx.default}{fg.default}")
    result = result.replace('[bold yellow]', f"{fx.bold}{fg.yellow}")
    result = result.replace('[/bold yellow]', f"{fx.default}{fx.default}")
    result = result.replace('[green]', f"{fg.green}")
    result = result.replace('[/green]', f"{fx.default}")
    result = result.replace('[cyan]', f"{fg.cyan}")
    result = result.replace('[/cyan]', f"{fx.default}")
    result = result.replace('[blue]', f"{fg.cyan}")
    result = result.replace('[/blue]', f"{fx.default}")
    result = result.replace('[yellow]', f"{fg.yellow}")
    result = result.replace('[/yellow]', f"{fx.default}")
    result = result.replace('[red]', f"{fg.red}")
    result = result.replace('[/red]', f"{fg.default}")
    return result


@click.group()
def cli():
    """AI message classifier and chat assistant"""
    pass


@cli.command()
@click.argument('message', nargs=-1, type=click.STRING)
@click.option('--interactive', '-i', is_flag=True, help='Enter interactive classification mode')
@click.option('--provider', '-p', default=PROVIDER_OPENROUTER, help='Provider to use (openrouter or ollama)')
def classify(message, interactive, provider):
    """
    Classify messages into categories: CALENDAR, TASK, MEMO

    For CALENDAR events, recursively extracts details and calls add2calendar() tool

    Examples:
        agentgog classify "Meeting tomorrow at 10am"
        agentgog classify "Buy groceries"
        agentgog classify -i
        agentgog classify "Meeting tomorrow" -p ollama
    """
    logger.info(f"Agentgog classification started with provider: {provider}")
    
    # Validate provider
    is_valid, error_msg = validate_provider(provider)
    if not is_valid:
        output = f"{fx.bold}{fg.red}Error:{fx.default} {error_msg}"
        print(format_output(output))
        sys.exit(1)
    
    try:
        if interactive:
            interactive_classification_mode(provider)
            return

        if not message:
            click.echo("Error: Please provide a message to classify", err=True)
            click.echo("Use 'agentgog classify --help' for usage information", err=True)
            sys.exit(1)

        message_text = ' '.join(message)
        success, classification, raw_response = classify_message(message_text, provider=provider)

        if success:
            colors = {
                'CALENDAR': 'green',
                'TASK': 'blue',
                'MEMO': 'cyan'
            }
            color = colors.get(classification or 'MEMO', 'white')
            output = f"{fx.bold}Classification:{fx.default} {colorize(classification, color)}"
            print(format_output(output))

            if classification == 'CALENDAR':
                logger.info("Calendar")
                print(format_output(f"{fx.bold}[cyan]Extracting calendar details...[/cyan]{fx.default}"))
                extract_success, calendar_details, extract_response = extract_calendar_details(message_text, provider=provider)
                #logger.info(f"Response: {extract_response}")

                if extract_success and calendar_details:
                    print(format_output(f"{fx.bold}[cyan]Calling add2calendar() tool...[/cyan]{fx.default}"))
                    result = add2calendar(
                        date=calendar_details.get('date'),
                        time=calendar_details.get('time'),
                        event_name=calendar_details.get('event_name'),
                        details=calendar_details.get('details'),
                        timezone='Europe/Prague'
                    )
                else:
                    error_msg = (extract_response.get('error') if extract_response else 'Failed to extract calendar details')
                    output = f"{fx.bold}{fg.red}Error extracting calendar details:{fx.default} {error_msg}"
                    print(format_output(output))
                    sys.exit(1)

            elif classification == 'TASK':
                logger.info("Task")
                print(format_output(f"{fx.bold}[cyan]Extracting task details...[/cyan]{fx.default}"))
                extract_success, task_details, extract_response = extract_task_details(message_text, provider=provider)
                #logger.info(f"Response: {extract_response}")

                if extract_success and task_details:
                    print(format_output(f"{fx.bold}[cyan]Calling add2task() tool...[/cyan]{fx.default}"))
                    result = add2task(
                        task_name=task_details.get('task_name'),
                        due_date=task_details.get('due_date'),
                        priority=task_details.get('priority'),
                        details=task_details.get('details')
                    )
                else:
                    error_msg = (extract_response.get('error') if extract_response else 'Failed to extract task details')
                    output = f"{fx.bold}{fg.red}Error extracting task details:{fx.default} {error_msg}"
                    print(format_output(output))
                    sys.exit(1)

            elif classification == 'MEMO':
                logger.info("Memo")
                print(format_output(f"{fx.bold}[cyan]Extracting memo details...[/cyan]{fx.default}"))
                extract_success, memo_details, extract_response = extract_memo_details(message_text, provider=provider)
                #logger.info(f"Response: {extract_response}")

                if extract_success and memo_details:
                    print(format_output(f"{fx.bold}[cyan]Calling add2keep() tool...[/cyan]{fx.default}"))
                    result = add2keep(
                        title=memo_details.get('title'),
                        content=memo_details.get('content'),
                        labels=memo_details.get('labels')
                    )
                else:
                    logger.error(extract_response)
                    error_msg = (extract_response.get('error') if extract_response else 'Failed to extract memo details')
                    output = f"{fx.bold}{fg.red}Error extracting memo details:{fx.default} {error_msg}"
                    print(format_output(output))
                    sys.exit(1)
        else:
            error_msg = (raw_response.get('error') if raw_response else 'Unknown error')
            output = f"{fx.bold}{fg.red}Error:{fx.default} {error_msg}"
            print(format_output(output))
            sys.exit(1)
    finally:
        logger.info("Agentgog classification ended")


def interactive_classification_mode(provider=PROVIDER_OPENROUTER):
    """Interactive mode for classifying multiple messages"""
    print(format_output(f"{fx.bold}AI Message Classifier - Interactive Mode (Provider: {provider}){fx.default}"))
    print(format_output(f"{fx.dim}Type 'quit' or 'exit' to leave{fx.default}\n"))

    while True:
        try:
            message = input(format_output(f"{fx.bold}Enter message:{fx.default} ")).strip()

            if message.lower() in ('quit', 'exit'):
                print(format_output(f"{fx.dim}Goodbye!{fx.default}"))
                break

            if not message:
                continue

            success, classification, raw_response = classify_message(message, provider=provider)

            if success:
                colors = {
                    'CALENDAR': 'green',
                    'TASK': 'blue',
                    'MEMO': 'cyan'
                }
                color = colors.get(classification or 'MEMO', 'white')
                output = f"  → {fx.bold}Classification:{fx.default} {colorize(classification, color)}"
                print(format_output(output))
            else:
                error_msg = (raw_response.get('error') if raw_response else 'Unknown error')
                output = f"  → {fx.bold}{fg.red}Error:{fx.default} {error_msg}"
                print(format_output(output))

        except KeyboardInterrupt:
            print(format_output(f"\n{fx.dim}Goodbye!{fx.default}"))
            break


@cli.command()
@click.argument('message', nargs=-1, type=click.STRING, required=False)
@click.option('--interactive', '-i', is_flag=True, help='Enter interactive chat mode')
@click.option('--model', '-m', default=None, help='Model to use for chat')
@click.option('--provider', '-p', default=PROVIDER_OPENROUTER, help='Provider to use (openrouter or ollama)')
@click.option('--timeout', '-t', type=int, default=None, help='Timeout in seconds (provider defaults: ollama=90, openrouter=10)')
def chat(message, interactive, model, provider, timeout):
    """
    Chat with AI assistant

    Examples:
        agentgog chat "What's the capital of France?"
        agentgog chat -i
        agentgog chat "Explain quantum physics" --model x-ai/grok-4.1-fast
        agentgog chat "Hello" -p ollama
        agentgog chat "Hi" -p ollama -m llama2
        agentgog chat "Complex question" -p ollama --timeout 120
    """
    logger.info(f"Agentgog chat started with provider: {provider}")
    
    # Validate provider
    is_valid, error_msg = validate_provider(provider)
    if not is_valid:
        output = f"{fx.bold}{fg.red}Error:{fx.default} {error_msg}"
        print(format_output(output))
        sys.exit(1)
    
    # Use provider-specific default model if not specified
    if model is None:
        model = get_default_model(provider)
    
    system_prompt = f"I am your useful and efficient assistant and it is {dt.datetime.now()} now."

    try:
        if interactive:
            interactive_chat_mode(system_prompt, model, provider, timeout)
            return

        if not message:
            click.echo("Error: Please provide a message or use --interactive mode", err=True)
            click.echo("Use 'agentgog chat --help' for usage information", err=True)
            sys.exit(1)

        message_text = ' '.join(message)
        success, response, raw_response = chat_with_provider(
            provider=provider,
            message=message_text,
            system_prompt=system_prompt,
            model=model,
            timeout=timeout
        )

        if success:
            print(format_output(f"{fx.bold}{fg.green}AI:{fx.default} {response}"))
        else:
            error_msg = (raw_response.get('error') if raw_response else 'Unknown error')
            output = f"{fx.bold}{fg.red}Error:{fx.default} {error_msg}"
            print(format_output(output))
            sys.exit(1)
    finally:
        logger.info("Agentgog chat ended")


def interactive_chat_mode(system_prompt, model, provider=PROVIDER_OPENROUTER, timeout=None):
    """Interactive mode for chatting with AI"""
    messages = [{"role": "system", "content": system_prompt}]
    history_file = os.path.expanduser('~/.agentgog_history')

    session = PromptSession(history=FileHistory(history_file))

    print(format_output(f"{fx.bold}AI Chat Assistant - Interactive Mode (Provider: {provider}){fx.default}"))
    print(format_output(f"{fx.dim}Commands: /q /quit /exit - quit, /c /clear /reset /r - clear history{fx.default}"))
    print(format_output(f"{fx.dim}Use arrow keys to navigate history, Ctrl+C to quit\n"))

    while True:
        try:
            user_message = session.prompt("You: ").strip()

            if user_message.lower() in ('/q', '/quit', 'quit', 'exit', '/exit'):
                print(format_output(f"{fx.dim}Goodbye!{fx.default}"))
                break

            if user_message.lower() in ('/c', '/clear', '/reset', '/r'):
                messages = [{"role": "system", "content": system_prompt}]
                print(format_output(f"{fx.dim}Conversation history cleared.\n{fx.default}"))
                continue

            if not user_message:
                continue

            messages.append({"role": "user", "content": user_message})

            success, response, raw_response = chat_with_provider(
                provider=provider,
                messages=messages,
                model=model,
                timeout=timeout
            )

            if success:
                messages.append({"role": "assistant", "content": response})
                print(format_output(f"{fx.bold}{fg.green}AI:{fx.default} {response}\n"))
            else:
                error_msg = (raw_response.get('error') if raw_response else 'Unknown error')
                output = f"  → {fx.bold}{fg.red}Error:{fx.default} {error_msg}\n"
                print(format_output(output))

        except KeyboardInterrupt:
            print(format_output(f"\n{fx.dim}Goodbye!{fx.default}"))
            break


@cli.command("translator")
@click.option("--srt-file", "-s", "inputfile", required=True, type=click.Path(exists=True), help="Input SRT file to translate")
@click.option("--model", "-m", required=True, help="Model to use for translation")
@click.option("--provider", "-p", default=PROVIDER_OPENROUTER, help='Provider (currently only openrouter supported)')
def translator(inputfile, model, provider):
    """
    Translate SRT subtitles from English to Czech using smolagents.

    Examples:
        agentgog translator -s subtitles.srt --model google/gemma-3-27b-it:free
        agentgog translator -s subtitles.srt --model google/gemma-3-27b-it:free -p openrouter
    """
    logger.info(f"Translator command started with file: {inputfile}, model: {model}, provider: {provider}")
    
    # Validate provider
    is_valid, error_msg = validate_provider(provider)
    if not is_valid:
        output = f"{fx.bold}{fg.red}Error:{fx.default} {error_msg}"
        print(format_output(output))
        sys.exit(1)
    
    # Note: translator currently only supports OpenRouter
    if provider != PROVIDER_OPENROUTER:
        output = f"{fx.bold}{fg.yellow}Warning:{fx.default} Translator currently only supports OpenRouter provider"
        print(format_output(output))

    try:
        OUTPUTFILE_a, OUTPUTFILE_ext = os.path.splitext(inputfile)

        with open(inputfile) as f:
            srt_content = f.read()

        print(format_output(f"{fx.bold}[cyan]Using model:{fx.default}{fx.default} {model}"))

        translated = translate_srt(model, srt_content)

        output_path = f"{OUTPUTFILE_a}_cs{OUTPUTFILE_ext}"
        with open(output_path, "w") as f:
            f.write(f"{translated}")

        logger.info(f"Translation completed. Output saved to: {output_path}")

        print(format_output(f"{fx.bold}[green]Translation complete!{fx.default}{fx.default}"))
        print(format_output(f"{fx.dim}Output saved to:{fx.default} {output_path}"))
    except Exception as e:
        logger.error(f"Translator command failed: {e}")
        print(format_output(f"{fx.bold}[red]Error:{fx.default}{fx.default} {e}"))
        sys.exit(1)


@cli.command("qrpayment")
@click.argument("prompt")
@click.option("--model", "-m", required=True, help="Model to use for QR payment generation")
@click.option("--provider", "-p", default=PROVIDER_OPENROUTER, help='Provider (currently only openrouter supported)')
def qrpayment(prompt, model, provider):
    """
    Generate QR code for payment based on the given prompt using smolagents.

    Examples:
        agentgog qrpayment "Transfer 500 CZK to account 1234567890/0300" --model google/gemma-3-27b-it:free
        agentgog qrpayment "Pay 100 to 0987654321/0800 with VS 123456" -p openrouter
    """
    logger.info(f"QR payment command started with prompt: {prompt}, model: {model}, provider: {provider}")
    
    # Validate provider
    is_valid, error_msg = validate_provider(provider)
    if not is_valid:
        output = f"{fx.bold}{fg.red}Error:{fx.default} {error_msg}"
        print(format_output(output))
        sys.exit(1)
    
    # Note: qrpayment currently only supports OpenRouter
    if provider != PROVIDER_OPENROUTER:
        output = f"{fx.bold}{fg.yellow}Warning:{fx.default} QR payment generation currently only supports OpenRouter provider"
        print(format_output(output))

    try:
        print(format_output(f"{fx.bold}[cyan]Using model:{fx.default}{fx.default} {model}"))
        print(format_output(f"{fx.dim}Analyzing payment details...{fx.default}"))

        output_path = generate_payment_qr(model, prompt)

        logger.info(f"QR code generated and saved to: {output_path}")

        print(format_output(f"{fx.bold}[green]QR code generated!{fx.default}{fx.default}"))
        print(format_output(f"{fx.dim}QR code saved to:{fx.default} {output_path}"))
    except Exception as e:
        logger.error(f"QR payment command failed: {e}")
        print(format_output(f"{fx.bold}[red]Error:{fx.default}{fx.default} {e}"))
        sys.exit(1)


@cli.command("codeagent")
@click.argument("prompt")
@click.option("--model", "-m", required=True, help="Model to use for codeagent")
@click.option("--max-steps", "-x", default=10, help="Maximum number of steps for CodeAgent")
@click.option("--provider", "-p", default=PROVIDER_OPENROUTER, help='Provider to use (openrouter or ollama)')
def codeagent(prompt, model, max_steps, provider):
    """
    Run vanilla CodeAgent with built-in prompt for general AI tasks.

    Examples:
        agentgog codeagent "Write a Python function to calculate fibonacci" --model google/gemma-3-27b-it:free
        agentgog codeagent "Explain how neural networks work" --model google/gemma-3-27b-it:free
        agentgog codeagent "Create a simple web scraper" --max-steps 20 -p openrouter
        agentgog codeagent "Calculate 5 factorial" -p ollama --model llama3.2
    """
    logger.info(f"Codeagent command started with prompt: {prompt}, model: {model}, max_steps: {max_steps}, provider: {provider}")
    
    # Validate provider
    is_valid, error_msg = validate_provider(provider)
    if not is_valid:
        output = f"{fx.bold}{fg.red}Error:{fx.default} {error_msg}"
        print(format_output(output))
        sys.exit(1)

    try:
        print(format_output(f"{fx.bold}[cyan]Using model:{fx.default}{fx.default} {model}"))
        print(format_output(f"{fx.bold}[cyan]Provider:{fx.default}{fx.default} {provider}"))
        print(format_output(f"{fx.dim}Running CodeAgent...{fx.default}"))

        result = run_codeagent(model, prompt, max_steps, provider=provider)

        logger.info(f"Codeagent completed successfully")

        print(format_output(f"{fx.bold}[green]CodeAgent result:{fx.default}{fx.default}"))
        print(format_output(f"{result}"))
    except Exception as e:
        logger.error(f"Codeagent command failed: {e}")
        print(format_output(f"{fx.bold}[red]Error:{fx.default}{fx.default} {e}"))
        sys.exit(1)


def main():
    """Main entry point for backward compatibility"""
    cli(prog_name='agentgog')


if __name__ == '__main__':
    main()
