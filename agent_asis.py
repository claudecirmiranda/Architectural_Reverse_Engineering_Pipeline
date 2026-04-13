"""
AS IS Consolidation Agent

Lê os blueprints gerados dos projetos do ecossistema e consolida
tudo em um documento AS IS unificado.
"""

import os
import glob
from pathlib import Path
from core.llm import call_llm


# ── Configuração dos projetos ────────────────────────────────────────────────

BLUEPRINT_PATHS = [
    "outputs/nav-paciente-agendamento-exames/blueprints/*_blueprint.md",
    "outputs/nav-paciente-servicos/blueprints/*_blueprint.md",
]

OUTPUT_DIR = "outputs/as-is"
OUTPUT_FILE = "as_is_consolidado.md"


# ── Prompts ──────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Você é um arquiteto de sistemas especialista em análise e documentação de software.
Sua tarefa é analisar blueprints de múltiplos projetos de um ecossistema e consolidar
as informações em um documento AS IS completo, claro e estruturado.

O documento AS IS deve:
- Descrever o estado atual do ecossistema como um todo
- Identificar os principais domínios e subdomínios
- Mapear os fluxos de dados e integrações entre os projetos
- Destacar responsabilidades de cada projeto/serviço
- Identificar dependências e pontos de integração
- Usar linguagem técnica mas acessível
- Ser organizado com seções claras e hierarquia lógica

Formato de saída: Markdown bem estruturado com headers, tabelas e diagramas textuais
onde necessário.
"""

CONSOLIDATION_PROMPT_TEMPLATE = """
Abaixo estão os blueprints de {num_projects} projetos do ecossistema.
Analise-os e gere um documento AS IS consolidado que represente o estado atual
do ecossistema como um todo.

{blueprints_content}

---

Gere o documento AS IS consolidado seguindo esta estrutura:

# AS IS — Ecossistema [Nome do Ecossistema]

## 1. Visão Geral
Resumo executivo do ecossistema atual.

## 2. Projetos do Ecossistema
Descrição de cada projeto e seu papel.

## 3. Domínios e Responsabilidades
Mapeamento de domínios de negócio e quem os cobre.

## 4. Fluxos Principais
Descrição dos fluxos de negócio ponta a ponta.

## 5. Integrações e Dependências
Como os projetos se comunicam e dependem entre si.

## 6. Componentes Técnicos
Principais componentes, APIs, e tecnologias identificadas.

## 7. Gaps e Observações
Lacunas, inconsistências ou pontos de atenção identificados nos blueprints.
"""


# ── Funções auxiliares ───────────────────────────────────────────────────────

def load_blueprints(blueprint_patterns: list[str]) -> dict[str, str]:
    """
    Carrega todos os blueprints encontrados nos padrões de caminho fornecidos.
    Retorna um dict: {caminho_relativo: conteúdo}
    """
    blueprints = {}

    for pattern in blueprint_patterns:
        files = glob.glob(pattern, recursive=True)

        if not files:
            print(f"⚠️  Nenhum blueprint encontrado para: {pattern}")
            continue

        for filepath in sorted(files):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                blueprints[filepath] = content
                print(f"✅ Blueprint carregado: {filepath}")
            except Exception as e:
                print(f"❌ Erro ao ler {filepath}: {e}")

    return blueprints


def format_blueprints_for_prompt(blueprints: dict[str, str]) -> str:
    """
    Formata os blueprints carregados em uma string estruturada para o prompt.
    """
    sections = []

    for filepath, content in blueprints.items():
        project = Path(filepath).parts[1] if len(Path(filepath).parts) > 1 else filepath
        filename = Path(filepath).stem

        section = f"""
### Blueprint: `{filename}`
**Projeto:** `{project}`
**Arquivo:** `{filepath}`

{content}
"""
        sections.append(section)

    return "\n---\n".join(sections)


def save_output(content: str, output_dir: str, output_file: str) -> str:
    """
    Salva o documento AS IS gerado no diretório de saída.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, output_file)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


# ── Agent principal ──────────────────────────────────────────────────────────

def run_as_is_agent():
    print("\n🚀 Iniciando AS IS Consolidation Agent\n")

    # 1. Carregar blueprints
    print("📂 Carregando blueprints...")
    blueprints = load_blueprints(BLUEPRINT_PATHS)

    if not blueprints:
        print("❌ Nenhum blueprint encontrado. Verifique os caminhos configurados.")
        return

    print(f"\n📋 Total de blueprints carregados: {len(blueprints)}\n")

    # 2. Montar prompt
    print("🔧 Preparando prompt para o LLM...")
    blueprints_content = format_blueprints_for_prompt(blueprints)

    user_prompt = CONSOLIDATION_PROMPT_TEMPLATE.format(
        num_projects=len(set(
            Path(fp).parts[1]
            for fp in blueprints.keys()
            if len(Path(fp).parts) > 1
        )),
        blueprints_content=blueprints_content,
    )

    # 3. Chamar LLM
    print("🤖 Gerando documento AS IS consolidado via LLM...")
    result = call_llm(SYSTEM_PROMPT, user_prompt)

    if not result:
        print("❌ O LLM não retornou resultado.")
        return

    # 4. Salvar output
    print("\n💾 Salvando documento AS IS...")
    output_path = save_output(result, OUTPUT_DIR, OUTPUT_FILE)

    print(f"\n✅ Documento AS IS gerado com sucesso!")
    print(f"📄 Arquivo: {output_path}")
    print(f"📏 Tamanho: {len(result):,} caracteres")

    return output_path


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_as_is_agent()