"""
Utilitários para leitura de inputs e escrita de outputs.
"""

import os
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
INPUTS_DIR = BASE_DIR / "inputs"
OUTPUTS_DIR = BASE_DIR / "outputs"


def read_input(filename: str) -> str:
    """Lê um arquivo da pasta inputs/."""
    path = INPUTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo de input não encontrado: {path}\n"
            f"Certifique-se de que '{filename}' está em tools/inputs/"
        )
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"Arquivo '{filename}' está vazio.")
    return content


def write_output(filename: str, content: str) -> Path:
    """Salva conteúdo na pasta outputs/ e retorna o caminho do arquivo."""
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUTS_DIR / filename
    path.write_text(content, encoding="utf-8")
    return path


def load_inputs(*filenames: str) -> dict[str, str]:
    """
    Carrega múltiplos inputs de uma vez.
    Retorna dict {filename: conteudo}.
    """
    return {name: read_input(name) for name in filenames}


def print_banner(title: str) -> None:
    """Exibe banner formatado no terminal."""
    width = 60
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)
    print(f"  Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * width + "\n")


def print_success(output_path: Path) -> None:
    """Exibe mensagem de sucesso com caminho do arquivo gerado."""
    print("\n" + "✅ " + "=" * 56)
    print(f"  Arquivo gerado com sucesso!")
    print(f"  📄 {output_path}")
    print("=" * 58 + "\n")