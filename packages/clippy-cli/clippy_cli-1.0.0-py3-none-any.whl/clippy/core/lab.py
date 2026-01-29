import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.prompt import Prompt
from azure.ai.inference.models import UserMessage, SystemMessage
from clippy.utils.ai import AIClient

def lab():
    console = Console()
    console.print("[bold green]Welcome to Clippy Lab (Interactive Mode)[/bold green]")
    console.print("Type 'exit' or 'quit' to leave.")
    
    try:
        client = AIClient()
        history = [
            SystemMessage(content="You are Clippy, an interactive CLI assistant. Be concise and helpful.")
        ]
        
        while True:
            user_input = Prompt.ask("\n[bold blue]You[/bold blue]")
            
            if user_input.lower() in ("exit", "quit"):
                break
            
            if not user_input.strip():
                continue
                
            history.append(UserMessage(content=user_input))
            
            console.print("[bold purple]Clippy:[/bold purple]")
            
            full_response = ""
            stream = client.chat(history, stream=True)
            
            with Live(Markdown(""), refresh_per_second=10, console=console) as live:
                for chunk in stream:
                     if chunk.choices and chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        live.update(Markdown(full_response))
            
            # Append assistant response to history
            # Note: Azure AI Inference SDK models might need strictly alternating roles or just list?
            # ideally we should append assistant message, but specific SDK class for AssistantMessage import needed?
            # For simplicity in this loop, we just re-send user messages or use context if supported.
            # actually Azure AI Inference client is stateless usually unless we pass history.
            # We need to append the ASSISTANT response to history to maintain context.
            from azure.ai.inference.models import AssistantMessage
            history.append(AssistantMessage(content=full_response))
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Exiting...[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in Lab: {e}[/red]")

if __name__ == "__main__":
    lab()
