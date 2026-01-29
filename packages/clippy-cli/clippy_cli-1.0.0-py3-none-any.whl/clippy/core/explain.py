import sys
import os
from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from clippy.utils.parsing import CommandParser
from clippy.config import load_env

def explain(command: Optional[str] = None):
    """
    Explains a shell command using deterministic parsing or AI fallback.
    """
    load_env()
    console = Console()

    # 1. Determine Input
    # Check if input is coming from a pipe
    if not sys.stdin.isatty():
        # Read from stdin
        command_input = sys.stdin.read().strip()
        # If command arg is also provided, perhaps treat stdin as context? 
        # For now, following Unix conventions, if stdin is piped, it's usually the data. 
        # But if the user runs `echo "ls -la" | clippy-explain`, the command IS the stdin.
        if not command and command_input:
            command = command_input
    
    if not command:
        # If still no command, check args if called directly (though usually passed to function)
        if len(sys.argv) > 1:
             # wrapper might pass args via function call, but if run as script:
             command = " ".join(sys.argv[1:])
    
    if not command:
        console.print("[red]Error: No command provided to explain.[/red]")
        console.print("Usage: echo 'command' | python -m clippy.core.explain")
        console.print("   OR: python -m clippy.core.explain 'command'")
        sys.exit(1)

    console.print(f"[bold blue]Explain:[/bold blue] [green]{command}[/green]")
    console.print("---")

    # 2. Deterministic Parsing
    parser = CommandParser()
    explanation, confidence = parser.get_explanation(command)

    # 3. AI Fallback Logic
    # Threshold setup. If confidence is low, try AI.
    from clippy.config import load_config
    config = load_config()
    
    # Check if AI is enabled and confidence threshold
    ai_config = config.get("ai", {})
    ai_enabled = ai_config.get("enabled", False)
    threshold = ai_config.get("confidence_threshold", 0.6)
    
    
    if confidence >= threshold:
        console.print("[bold green]Deterministic Explanation:[/bold green]")
        console.print(Markdown(explanation))
    else:
        # Proposed logic: If AI is enabled, try it. If it works, great. 
        # If it fails or is disabled, show deterministic.
        
        ai_success = False
        
        if ai_enabled:
            console.print(f"[dim]Deterministic confidence low ({confidence}). Attempting AI explanation...[/dim]")
            try:
                # New centralized AI Client
                from clippy.utils.ai import AIClient
                from rich.live import Live
                client = AIClient() # Checks config internally too
                context = f"User is on {os.name} system."
                
                console.print("[bold purple]AI Explanation:[/bold purple]")
                
                stream = client.explain_command(command, context)
                full_response = ""
                
                # Create a Live display for streaming markdown
                with Live(Markdown(""), refresh_per_second=10, console=console) as live:
                    for chunk in stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_response += content
                            live.update(Markdown(full_response))
                
                ai_success = True
                            
            except Exception:
                # Silent failure as per v1.0.0 requirement
                # We will fall back to deterministic below
                pass
        
        if not ai_success:
            # Fallback to deterministic explanation
            if ai_enabled:
                # Only show this message if we actually tried AI and failed (or if we want to be explicit)
                # Requirement: "AI failures must be silent by default"
                # So we simply print the deterministic explanation without error text.
                pass
                
            console.print("[bold green]Deterministic Explanation (Best Effort):[/bold green]")
            console.print(Markdown(explanation))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        explain(" ".join(sys.argv[1:]))
    else:
        explain()
