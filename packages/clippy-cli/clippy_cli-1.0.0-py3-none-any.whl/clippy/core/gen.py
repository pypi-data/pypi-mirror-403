import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from clippy.utils.ai import AIClient

def gen(prompt=None):
    console = Console()
    
    if not prompt:
        if len(sys.argv) > 1:
            prompt = " ".join(sys.argv[1:])
        else:
            console.print("[red]No prompt provided.[/red]")
            console.print("Usage: clippy gen <description of command>")
            return

    console.print(f"[bold blue]Generating command for:[/bold blue] [green]{prompt}[/green]")
    
    try:
        client = AIClient()
        stream = client.generate_command(prompt)
        full_response = ""
        
        with Live(Markdown(""), refresh_per_second=10, console=console) as live:
            for chunk in stream:
                 if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    live.update(Markdown(full_response))
                    
    except Exception as e:
        console.print(f"[red]Error during generation: {e}[/red]")

if __name__ == "__main__":
    gen()
