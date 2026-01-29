import shlex

class CommandParser:
    """
    A deterministic parser for common shell commands.
    """
    
    # A small knowledge base of common commands
    KNOWN_COMMANDS = {
        "ls": "List directory contents",
        "cd": "Change the current working directory",
        "pwd": "Print name of current/working directory",
        "echo": "Display a line of text",
        "cat": "Concatenate files and print on the standard output",
        "grep": "Print lines that match patterns",
        "git": "Distributed version control system",
        "docker": "Containerization platform",
        "mkdir": "Make directories",
        "rm": "Remove files or directories",
        "cp": "Copy files and directories",
        "mv": "Move (rename) files",
    }

    def parse(self, command: str) -> dict:
        """
        Parses a command string into its components.
        """
        try:
            parts = shlex.split(command)
        except ValueError:
             # Handle unclosed quotes or parse errors
            parts = command.split()
            
        if not parts:
            return {"program": "", "args": []}
            
        return {
            "program": parts[0],
            "args": parts[1:]
        }

    def get_explanation(self, command: str) -> tuple[str, float]:
        """
        Returns an explanation and a confidence score (0.0 to 1.0).
        """
        parsed = self.parse(command)
        program = parsed["program"]
        
        if not program:
            return "Empty command provided.", 0.0

        if program in self.KNOWN_COMMANDS:
            # Basic deterministic explanation
            base_desc = self.KNOWN_COMMANDS[program]
            explanation = f"**{program}**: {base_desc}\n\n"
            
            if parsed["args"]:
                explanation += "Arguments parsing is limited in deterministic mode.\n"
                explanation += f"Arguments provided: `{' '.join(parsed['args'])}`"
                # Moderate confidence for known command with args (we know the tool, but maybe not flags)
                return explanation, 0.6 
            else:
                # High confidence for simple known command
                return explanation, 0.9

        # Fallback for unknown commands
        return f"Command `{program}` is not in the local database.", 0.1
