import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from clippy.utils.ai import AIClient

def note(topic=None):
    console = Console()
    
    if not topic:
        if len(sys.argv) > 1:
            topic = " ".join(sys.argv[1:])
        else:
            console.print("[red]No topic provided.[/red]")
            console.print("Usage: clippy note <topic>")
            return

    console.print(f"[bold blue]Generating notes for:[/bold blue] [green]{topic}[/green]")
    
    try:
        client = AIClient()
        stream = client.generate_note(topic)
        full_response = ""
        
        with Live(Markdown(""), refresh_per_second=10, console=console) as live:
            for chunk in stream:
                 if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    live.update(Markdown(full_response))
                    
    except Exception as e:
        console.print(f"[red]Error during note generation: {e}[/red]")

if __name__ == "__main__":
    note()
