import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from azure.core.credentials import AzureKeyCredential
from clippy.config import load_env, load_config

class AIClient:
    def __init__(self, model: str = "microsoft/Phi-4"):
        # Check configuration first
        config = load_config()
        if not config.get("ai", {}).get("enabled", False):
            raise ValueError("AI is disabled in configuration. Enable it in ~/.config/clippy/config.yml")

        load_env()
        self.token = os.environ.get("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable not found. Please check your .env file.")
        
        self.endpoint = "https://models.github.ai/inference"
        self.model_name = model
        
        self.client = ChatCompletionsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.token),
        )

    def chat(self, messages: list, temperature: float = 1.0, max_tokens: int = 1000, stream: bool = False):
        """
        Generic chat completion method.
        """
        try:
            response = self.client.complete(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                model=self.model_name,
                stream=stream
            )
            if stream:
                return response
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"AI Chat completion failed: {e}")

    def explain_command(self, command: str, context: str) -> object:
        """
        Specialized method to explain a shell command. Returns a stream.
        """
        return self._streaming_chat(
            system_prompt=(
                "You are a helpful command line assistant named Clippy. "
                "Explain the command in one or two short sentences. "
                "Be extremely concise. Do not use markdown headers."
            ),
            user_prompt=f"Explain: `{command}`\nContext: {context}"
        )

    def explain_error(self, command: str, error: str) -> object:
        """
        Explains why a command failed. Returns a stream.
        """
        return self._streaming_chat(
            system_prompt=(
                "You are a helpful command line assistant named Clippy. "
                "Explain the error in one simple sentence. "
                "Then provide the corrected command if possible. "
                "Be extremely concise."
            ),
            user_prompt=f"Command: `{command}`\nError: `{error}`"
        )

    def generate_command(self, prompt: str) -> object:
        """
        Generates a shell command. Returns a stream.
        """
        return self._streaming_chat(
            system_prompt=(
                "You are a helpful command line assistant named Clippy. "
                "Generate the requested shell command. "
                "Output ONLY the command in a markdown code block. "
                "No explanation."
            ),
            user_prompt=f"Generate command: {prompt}"
        )

    def generate_note(self, topic: str) -> object:
        """
        Generates a cheat sheet or note. Returns a stream.
        """
        return self._streaming_chat(
            system_prompt=(
                "You are a helpful command line assistant named Clippy. "
                "Create a concise cheat sheet for the topic. "
                "Use bullet points and code blocks. "
                "Keep it short and practical."
            ),
            user_prompt=f"Topic: {topic}"
        )

    def _streaming_chat(self, system_prompt: str, user_prompt: str, max_tokens: int = 400) -> object:
        """
        Helper for streaming chat completions with shared context rules.
        """
        # Inject core rules from context
        core_rules = (
            "Rules:\n"
            "1. Follow Unix CLI conventions.\n"
            "2. Be concise and direct.\n"
            "3. No fluff.\n"
        )
        
        messages = [
            SystemMessage(content=core_rules + system_prompt),
            UserMessage(content=user_prompt)
        ]
        
        return self.chat(messages, temperature=0.3, max_tokens=max_tokens, stream=True)
