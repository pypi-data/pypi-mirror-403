#!/usr/bin/env python3
"""
Test script for Ollama functionality

Checks:
1. Connection to Ollama server
2. Available models 
3. Currently running models
4. Test running model with "Who are you, briefly." query
"""
import sys
import os
from console import fg, fx

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ollama_client import (
    test_ollama_connection,
    get_available_models,
    get_running_models,
    chat_with_ollama
)


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
    result = result.replace('[/bold red]', f"{fx.default}{fg.default}")
    result = result.replace('[bold cyan]', f"{fx.bold}{fg.cyan}")
    result = result.replace('[/bold cyan]', f"{fx.default}{fg.default}")
    result = result.replace('[bold yellow]', f"{fx.bold}{fg.yellow}")
    result = result.replace('[/bold yellow]', f"{fx.default}{fg.default}")
    result = result.replace('[green]', f"{fg.green}")
    result = result.replace('[/green]', f"{fx.default}")
    result = result.replace('[cyan]', f"{fg.cyan}")
    result = result.replace('[/cyan]', f"{fx.default}")
    result = result.replace('[blue]', f"{fg.cyan}")
    result = result.replace('[/blue]', f"{fx.default}")
    result = result.replace('[yellow]', f"{fg.yellow}")
    result = result.replace('[/yellow]', f"{fx.default}")
    result = result.replace('[red]', f"{fg.red}")
    result = result.replace('[/red]', f"{fx.default}")
    return result


def main():
    print(format_output(f"{fx.bold}Ollama Test Suite{fx.default}"))
    print(format_output(f"{fx.dim}Testing local Ollama installation and models{fx.default}\n"))

    # 1. Test connection
    print(format_output(f"{fx.bold}[cyan]1. Testing Ollama connection...{fx.default}"))
    success, version_info, error = test_ollama_connection()
    
    if success:
        print(format_output(f"{fg.green}✓ Connected to Ollama{fg.default}"))
        if version_info:
            version = version_info.get('version', 'unknown')
            print(format_output(f"  Version: {version}"))
    else:
        print(format_output(f"{fg.red}✗ Connection failed{fg.default}"))
        print(format_output(f"  Error: {error.get('error', 'Unknown error')}"))
        print(format_output(f"\n{fg.yellow}Please ensure Ollama is running: 'ollama serve'{fg.default}"))
        sys.exit(1)
    
    print()

    # 2. Get available models
    print(format_output(f"{fx.bold}[cyan]2. Getting available models...{fx.default}"))
    success, models, error = get_available_models()
    
    if success and models:
        print(format_output(f"{fg.green}✓ Found {len(models)} available models:{fg.default}"))
        for i, model in enumerate(models, 1):
            print(format_output(f"  {i}. {model}"))
    else:
        print(format_output(f"{fg.red}✗ Failed to get available models{fg.default}"))
        if error:
            print(format_output(f"  Error: {error.get('error', 'Unknown error')}"))
    
    print()

    # 3. Get running models
    print(format_output(f"{fx.bold}[cyan]3. Getting running models...{fx.default}"))
    success, running_models, error = get_running_models()
    
    if success:
        if running_models:
            print(format_output(f"{fg.green}✓ Found {len(running_models)} running models:{fg.default}"))
            for i, model in enumerate(running_models, 1):
                name = model.get('name', 'unknown')
                size_mb = model.get('size', 0) / (1024*1024)  # Convert to MB
                status = model.get('status', 'unknown')
                print(format_output(f"  {i}. {name} ({size_mb:.1f}MB) - {status}"))
        else:
            print(format_output(f"{fg.yellow}⚠ No models currently running{fg.default}"))
    else:
        print(format_output(f"{fg.red}✗ Failed to get running models{fg.default}"))
        if error:
            print(format_output(f"  Error: {error.get('error', 'Unknown error')}"))
    
    print()

    # 4. Test running model with query
    if success and running_models:
        print(format_output(f"{fx.bold}[cyan]4. Testing running model with query...{fx.default}"))
        
        # Use the first running model
        test_model = running_models[0]['name']
        print(format_output(f"Testing model: {test_model}"))
        
        success, response, error = chat_with_ollama(
            message="Who are you, briefly.",
            timeout=15,
            model=test_model
        )
        
        if success:
            print(format_output(f"{fg.green}✓ Model responded:{fg.default}"))
            print(format_output(f"  Response: {response}"))
        else:
            print(format_output(f"{fg.red}✗ Model query failed{fg.default}"))
            if error:
                print(format_output(f"  Error: {error.get('error', 'Unknown error')}"))
    else:
        print(format_output(f"{fx.bold}[cyan]4. Skipping model test (no running models){fx.default}"))
        print(format_output(f"{fg.yellow}Run a model first: 'ollama run llama3.2'{fg.default}"))
    
    print()
    print(format_output(f"{fx.bold}[green]Test completed!{fx.default}"))


if __name__ == "__main__":
    main()