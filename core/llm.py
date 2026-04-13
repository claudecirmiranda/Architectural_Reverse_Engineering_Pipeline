"""
Cliente Anthropic centralizado.
Lê ANTHROPIC_API_KEY do ambiente ou do arquivo .env
"""

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 16000


def get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY não encontrada. "
            "Defina no arquivo .env ou como variável de ambiente."
        )
    return anthropic.Anthropic(api_key=api_key)


def call_llm(system_prompt: str, user_prompt: str, max_tokens: int = MAX_TOKENS) -> str:
    """
    Faz uma chamada à API Anthropic e retorna o texto da resposta.
    Exibe progresso via streaming no terminal.
    """
    client = get_client()
    full_response = []

    print("\n🤖 Gerando resposta", end="", flush=True)

    with client.messages.stream(
        model=MODEL,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for text in stream.text_stream:
            full_response.append(text)
            print(".", end="", flush=True)

    print(" ✓\n")
    return "".join(full_response)