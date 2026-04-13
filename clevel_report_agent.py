"""
C-Level Strategic Report Agent

Lê os reports de AS-IS, GAPs e TO-BE e gera um relatório estratégico
consolidado com visão executiva, diagramas Mermaid e fallbacks ASCII.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.llm import call_llm



# ── Configuração ─────────────────────────────────────────────────────────────

INPUT_FILES = {
    "as_is": "outputs/reports/as-is.md",
    "gaps":  "outputs/reports/gaps.md",
    "to_be": "outputs/reports/to-be.md",
}

OUTPUT_DIR  = "outputs/reports"
OUTPUT_FILE = "clevel-strategic-report.md"


# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """
Você é um consultor sênior especialista em transformação digital e comunicação executiva.
Sua tarefa é analisar documentos técnicos (AS-IS, GAPs, TO-BE) e produzir um relatório
estratégico de alto impacto para audiência C-Level (CEO, CTO, CIO, CFO).

## PRINCÍPIOS DO RELATÓRIO

- **Executivo com dados técnicos**: linguagem de negócio no primeiro plano, profundidade técnica como suporte
- **Visual first**: cada seção deve ter pelo menos um diagrama; texto é complemento, não protagonista
- **Decisão-driven**: cada seção deve deixar claro o que está em jogo e o que precisa ser decidido
- **Sem jargão desnecessário**: se um termo técnico aparecer, explique em uma linha o impacto de negócio

## REGRAS PARA DIAGRAMAS MERMAID

1. Sempre gere o bloco Mermaid PRIMEIRO, depois o fallback ASCII/tabela logo abaixo
2. Para `quadrantChart`: raciocine sobre o posicionamento antes de plotar — evite aglomeração no centro. Use o espaço completo [0.1–0.9] em ambos os eixos. Distribua os itens de forma que contem uma história visual clara.
3. Para `graph LR/TD`: use subgraphs para agrupar componentes por camada ou domínio. Seja conciso nos labels — máximo 4 palavras por nó.
4. Para `gantt`: use seções por onda (Quick Wins, Fundação, Escala). Datas relativas em trimestres (Q1 2025, Q2 2025...).
5. Nunca deixe um diagrama Mermaid sem o fallback correspondente logo abaixo, separado por comentário `<!-- FALLBACK ASCII -->`.

## REGRAS PARA INFERÊNCIA

- **Maturidade por Domínio**: classifique cada domínio identificado no AS-IS em Impacto (para o negócio) × Maturidade (qualidade atual). Use evidências do texto.
- **Priorização de Iniciativas**: classifique cada iniciativa do TO-BE em Esforço × Impacto. Quick Wins = baixo esforço + alto impacto.
- **Ondas do Roadmap**: Quick Wins (0-3 meses) = menor dependência técnica + maior visibilidade; Fundação (3-9 meses) = mudanças estruturais; Escala (9-18 meses) = expansão e otimização.
- **Riscos**: extraia dos GAPs os top 5 riscos. Classifique probabilidade e impacto como Alto/Médio/Baixo.
- **Stakeholders**: infira do contexto quem é impactado e qual é a dor específica de cada grupo.

## FORMATO DE SAÍDA

Markdown estruturado, pronto para ser importado em Notion, Confluence ou convertido em apresentação.
Use `---` entre seções principais. Use badges de status onde couber: 🔴 Crítico · 🟡 Atenção · 🟢 Saudável
"""


# ── User Prompt Template ──────────────────────────────────────────────────────

REPORT_PROMPT_TEMPLATE = """
Abaixo estão os três documentos de entrada. Analise-os integralmente antes de gerar o relatório.

---
## DOCUMENTO 1 — AS-IS (Estado Atual)
{as_is_content}

---
## DOCUMENTO 2 — GAPs (Diagnóstico)
{gaps_content}

---
## DOCUMENTO 3 — TO-BE (Visão Futura)
{to_be_content}

---

Gere o relatório estratégico C-Level completo seguindo EXATAMENTE esta estrutura:

---

# 📊 Relatório Estratégico — Transformação Digital
> *Documento executivo confidencial*

---

## 1. Executive Summary

Escreva 5 a 7 bullets de alto impacto cobrindo:
- Contexto do ecossistema atual
- Principais problemas identificados (com impacto de negócio)
- Visão do estado futuro
- O que está em jogo se não agirmos
- Próximos passos críticos

---

## 2. Cenário Atual — AS-IS

### 2.1 Arquitetura High-Level

> Diagrama `graph LR` mostrando o ecossistema atual: projetos, integrações, sistemas externos, camadas.
> Use subgraphs para agrupar por domínio/camada.
> Depois do Mermaid, gere o fallback ASCII.

### 2.2 Maturidade por Domínio

> Diagrama `quadrantChart` com título "Maturidade por Domínio (AS-IS)"
> Eixo X: "Baixo Impacto" → "Alto Impacto"
> Eixo Y: "Baixa Maturidade" → "Alta Maturidade"
> Quadrantes: Q1 "Otimizar Urgente" | Q2 "Investir Agora" | Q3 "Monitorar" | Q4 "Manter"
> Depois do Mermaid, gere tabela markdown como fallback.

### 2.3 Stakeholders e Impactos

> Diagrama `graph TD` mostrando stakeholders afetados e suas dores específicas.
> Depois do Mermaid, gere o fallback em lista indentada.

---

## 3. Diagnóstico de GAPs

### 3.1 Matriz de GAPs

> Diagrama `quadrantChart` com título "GAPs por Impacto × Criticidade"
> Eixo X: "Baixa Criticidade" → "Alta Criticidade"
> Eixo Y: "Baixo Impacto" → "Alto Impacto"
> Quadrantes: Q1 "Resolver Agora" | Q2 "Planejar" | Q3 "Backlog" | Q4 "Monitorar"
> Depois do Mermaid, gere tabela markdown como fallback.

### 3.2 Detalhamento dos GAPs Críticos

Tabela com colunas: GAP | Domínio | Impacto no Negócio | Status
Use badges 🔴 🟡 🟢 na coluna Status.

---

## 4. Visão Futura — TO-BE

### 4.1 Arquitetura High-Level

> Diagrama `graph LR` mostrando o ecossistema futuro.
> Destaque com comentários ou labels o que é NOVO vs EVOLUÍDO vs MANTIDO.
> Use subgraphs por domínio/camada.
> Depois do Mermaid, gere o fallback ASCII.

### 4.2 Priorização de Iniciativas

> Diagrama `quadrantChart` com título "Priorização de Iniciativas (TO-BE)"
> Eixo X: "Alto Esforço" → "Baixo Esforço"
> Eixo Y: "Baixo Impacto" → "Alto Impacto"
> Quadrantes: Q1 "Quick Wins" | Q2 "Projetos Estratégicos" | Q3 "Baixa Prioridade" | Q4 "Cuidado: Custo Oculto"
> Depois do Mermaid, gere tabela markdown como fallback.

### 4.3 Princípios da Arquitetura TO-BE

> Diagrama `graph LR` mostrando os princípios arquiteturais e suas implementações práticas.
> Depois do Mermaid, gere o fallback em lista indentada.

---

## 5. Roadmap de Transformação

### 5.1 Timeline por Ondas

> Diagrama `gantt` com 3 seções: Quick Wins (0-3m), Fundação (3-9m), Escala (9-18m).
> Cada iniciativa deve referenciar qual GAP resolve.
> Depois do Mermaid, gere tabela markdown como fallback com colunas: Iniciativa | Onda | Prazo | GAP Resolvido.

### 5.2 Dependências Críticas

Liste em texto as dependências entre iniciativas que podem travar o roadmap.

---

## 6. Riscos e Mitigações

Tabela com os top 5 riscos:
| Risco | Probabilidade | Impacto | Mitigação | Responsável Sugerido |

---

## 7. Governança e Call to Action

### 7.1 Modelo de Governança

> Diagrama `graph TD` mostrando o comitê de transformação, responsabilidades e cadências.
> Depois do Mermaid, gere o fallback em lista indentada.

### 7.2 Decisões Necessárias

Liste de forma direta o que o C-Level precisa aprovar, priorizar ou desbloquear.
Use o formato: **[DECISÃO]** Descrição — *Impacto se não decidido*

### 7.3 Próximos 30 dias

Liste as 3 a 5 ações concretas que devem começar imediatamente.

---
*Autor: Claudecir Miranda · Arquiteto de Soluções/IA · Versão 1.0*
"""


# ── Funções auxiliares ────────────────────────────────────────────────────────

def load_report(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
    print(f"  ✅ {filepath} ({len(content):,} chars)")
    return content


def save_output(content: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path


# ── Agent principal ───────────────────────────────────────────────────────────

def run_clevel_report_agent():
    print("\n🚀 C-Level Strategic Report Agent\n")

    # 1. Carregar inputs
    print("📂 Carregando reports...")
    try:
        as_is_content = load_report(INPUT_FILES["as_is"])
        gaps_content  = load_report(INPUT_FILES["gaps"])
        to_be_content = load_report(INPUT_FILES["to_be"])
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        return

    # 2. Montar prompt
    print("\n🔧 Preparando prompt...")
    user_prompt = REPORT_PROMPT_TEMPLATE.format(
        as_is_content=as_is_content,
        gaps_content=gaps_content,
        to_be_content=to_be_content,
    )
    print(f"  📏 Tamanho do prompt: {len(user_prompt):,} chars")

    # 3. Chamar LLM
    print("\n🤖 Gerando relatório C-Level via LLM...")
    result = call_llm(SYSTEM_PROMPT, user_prompt)

    if not result:
        print("❌ O LLM não retornou resultado.")
        return

    # 4. Salvar
    print("\n💾 Salvando relatório...")
    output_path = save_output(result)

    print(f"\n✅ Relatório C-Level gerado com sucesso!")
    print(f"📄 Arquivo : {output_path}")
    print(f"📏 Tamanho : {len(result):,} caracteres")
    print(f"\n📋 Seções geradas:")
    for line in result.split("\n"):
        if line.startswith("## "):
            print(f"   {line.strip()}")

    return output_path


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_clevel_report_agent()