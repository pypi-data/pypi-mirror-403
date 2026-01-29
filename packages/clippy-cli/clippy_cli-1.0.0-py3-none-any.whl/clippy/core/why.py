import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from clippy.utils.ai import AIClient

def why(command=None, error_output=None):
    console = Console()
    
    # Read from stdin if available (piped error)
    if not sys.stdin.isatty():
        stdin_content = sys.stdin.read().strip()
        if stdin_content:
            # Heuristic: assume stdin is the error/output
            error_output = stdin_content
            
    if not error_output:
        if len(sys.argv) > 1:
            # Maybe passed as args?
            error_output = " ".join(sys.argv[1:])
        else:
            console.print("[red]No input provided.[/red]")
            console.print("Usage: <command> 2>&1 | clippy why")
            return

    console.print("[bold red]Diagnosing Error...[/bold red]")
    
    try:
        client = AIClient()
        # If we don't know the command, we just say "Unknown command" or similar in prompt
        cmd_context = command if command else "Unknown command (piped input)"
        
        stream = client.explain_error(cmd_context, error_output)
        full_response = ""
        
        with Live(Markdown(""), refresh_per_second=10, console=console) as live:
            for chunk in stream:
                 if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    live.update(Markdown(full_response))
                    
    except Exception as e:
        console.print(f"[red]Error during diagnosis: {e}[/red]")

if __name__ == "__main__":
    why()
