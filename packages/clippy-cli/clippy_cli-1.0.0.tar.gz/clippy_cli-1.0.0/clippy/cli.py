import sys
from rich.console import Console

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    command = sys.argv[1]
    args = sys.argv[2:]

    # Dispatch to core modules
    if command == "explain":
        from clippy.core.explain import explain
        # Reconstruct command string from args
        cmd_str = " ".join(args) if args else None
        explain(cmd_str)
        
    elif command == "why":
        from clippy.core.why import why
        # why handles its own args/stdin
        # We need to pass args carefully. 
        # If piped, sys.stdin is handled in why().
        # If args, pass them.
        why(command=" ".join(args) if args else None)
        
    elif command == "gen":
        from clippy.core.gen import gen
        gen(prompt=" ".join(args) if args else None)
        
    elif command == "note":
        from clippy.core.note import note
        note(topic=" ".join(args) if args else None)
        
    elif command == "lab":
        from clippy.core.lab import lab
        lab()
        
    else:
        print_help()
        sys.exit(1)

def print_help():
    console = Console()
    console.print("[bold blue]Clippy - Your CLI Assistant[/bold blue]")
    console.print("")
    console.print("[bold]Usage:[/bold]")
    console.print("  clippy explain <command>   Explain a shell command")
    console.print("  clippy why <args>          Diagnose an error (use pipes!)")
    console.print("  clippy gen <prompt>        Generate a shell command")
    console.print("  clippy note <topic>        Generate concise notes")
    console.print("  clippy lab                 Interactive Mode")
    console.print("")

if __name__ == "__main__":
    main()