"""Pretty Print for ReAct Agent Messages"""
from rich.console import Console, Group
from rich.panel import Panel
from rich.markdown import Markdown as M
from rich.text import Text
from rich.syntax import Syntax
from typing import Optional, Dict, Any, List
import json
from ..models import TokenUsage


console = Console(width=None, soft_wrap=True)


def print_system_prompt(content: str):
    """Print system prompt"""
    panel = Panel(
        M(content),
        title="[bold blue]System Prompt[/bold blue]",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


def print_user_message(content: str):
    """Print user message"""
    panel = Panel(
        M(content),
        title="[bold green]User[/bold green]",
        border_style="green",
        padding=(1, 2)
    )
    console.print(panel)


def print_assistant_message(content: str, tool_calls: Optional[List[Dict[str, Any]]] = None, token_usage: Optional[TokenUsage] = None):
    """Print assistant message (with or without tool calls)"""
    if tool_calls:
        # Assistant with tool calls
        text_content = Text()
        if content:
            text_content.append(content + "\n\n", style="white")
        
        text_content.append("Tool Calls:\n", style="yellow")
        for i, tool_call in enumerate(tool_calls, 1):
            func = tool_call.get("function", {})
            func_name = func.get("name", "unknown")
            func_args_str = func.get("arguments", "{}")
            
            # Try to parse and format the arguments
            try:
                func_args_dict = json.loads(func_args_str)
                func_args_formatted = json.dumps(func_args_dict, ensure_ascii=False, indent=2)
            except (json.JSONDecodeError, TypeError):
                func_args_formatted = func_args_str
            
            text_content.append(f"  {i}. ", style="dim")
            text_content.append(f"{func_name}", style="bold cyan")
            text_content.append("(\n", style="dim")
            # Add formatted arguments with indentation
            for line in func_args_formatted.split('\n'):
                text_content.append(f"    {line}\n", style="dim")
            text_content.append("  )\n", style="dim")
        
        panel = Panel(
            text_content,
            title="[bold yellow]Assistant (with tools)[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
            expand=False
        )
    else:
        # Assistant without tool calls (final response)
        panel = Panel(
            M(content) if content else Text("(empty response)", style="dim"),
            title="[bold magenta]Assistant[/bold magenta]",
            border_style="magenta",
            padding=(1, 2),
            expand=False
        )
    
    console.print(panel)
    
    # Print token usage for this round if provided
    if token_usage:
        print_round_token_usage(token_usage)


def print_tool_result(tool_call_id: str, content: str):
    """Print tool execution result"""
    text_content = Text()
    
    # Add tool call ID
    text_content.append(f"Tool Call ID: ", style="dim")
    text_content.append(f"{tool_call_id}\n\n", style="bold dim")
    
    # Try to parse and format the content as JSON
    try:
        result_dict = json.loads(content)
        formatted_content = json.dumps(result_dict, ensure_ascii=False, indent=2)
        
        # Check if it's an error
        if isinstance(result_dict, dict) and "error" in result_dict:
            # Error result - use red styling
            text_content.append("Result:\n", style="red")
            for line in formatted_content.split('\n'):
                text_content.append(f"  {line}\n", style="red")
            border_style = "red"
            title_style = "[bold red]Tool Result (Error)[/bold red]"
        else:
            # Success result - use green/cyan styling
            text_content.append("Result:\n", style="cyan")
            for line in formatted_content.split('\n'):
                text_content.append(f"  {line}\n", style="white")
            border_style = "cyan"
            title_style = "[bold cyan]Tool Result[/bold cyan]"
    except (json.JSONDecodeError, TypeError):
        # Not valid JSON, display as plain text
        text_content.append("Result:\n", style="cyan")
        text_content.append(f"  {content}\n", style="white")
        border_style = "cyan"
        title_style = "[bold cyan]Tool Result[/bold cyan]"
    
    panel = Panel(
        text_content,
        title=title_style,
        border_style=border_style,
        padding=(1, 2),
        expand=False
    )
    console.print(panel)


def print_round_token_usage(usage: TokenUsage):
    """Print token usage for a single round (compact format)"""
    text_content = Text()
    text_content.append("Prompt: ", style="dim")
    text_content.append(f"{usage.prompt_tokens:,}", style="cyan")
    text_content.append(" | Completion: ", style="dim")
    text_content.append(f"{usage.completion_tokens:,}", style="cyan")
    text_content.append(" | Total: ", style="dim")
    text_content.append(f"{usage.total_tokens:,}", style="bold cyan")
    
    panel = Panel(
        text_content,
        title="[dim]Token Usage (This Round)[/dim]",
        border_style="dim",
        padding=(0, 2),
        expand=False
    )
    console.print(panel)


def print_token_usage(usage: TokenUsage):
    """Print token usage statistics (total/cumulative)"""
    text_content = Text()
    text_content.append("Token Usage Statistics\n\n", style="bold")
    text_content.append(f"Prompt Tokens: ", style="dim")
    text_content.append(f"{usage.prompt_tokens:,}\n", style="cyan")
    text_content.append(f"Completion Tokens: ", style="dim")
    text_content.append(f"{usage.completion_tokens:,}\n", style="cyan")
    text_content.append(f"Total Tokens: ", style="dim")
    text_content.append(f"{usage.total_tokens:,}\n", style="bold cyan")
    
    panel = Panel(
        text_content,
        title="[bold blue]Token Usage (Total)[/bold blue]",
        border_style="blue",
        padding=(1, 2),
        expand=False
    )
    console.print(panel)