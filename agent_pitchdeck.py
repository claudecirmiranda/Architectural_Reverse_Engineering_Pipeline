"""
Agente 4 — Gerador de Pitch Deck Executivo (HTML)

Inputs:
    outputs/Gap_Analysis_Initial_20260213_143753.md
    outputs/TO_BE_Model_v3_Complete_20260218_130604.md

Output:
    tools/outputs/pitch_deck.html   (abrir direto no browser — sem dependências externas além de CDN)

Uso:
    python agents/agent_pitchdeck.py

Pré-requisitos:
    Execute agent_asis.py, agent_gap.py e agent_tobe.py antes deste agente.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.llm import call_llm
from core.file_utils import write_output, print_banner, print_success

# ─────────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────────

SYSTEM_PROMPT = """Você é um consultor estratégico sênior especializado em comunicação executiva para transformações digitais, com expertise em:
- Traduzir complexidade técnica em linguagem de negócio clara e impactante
- Construir narrativas persuasivas para C-level e Comitês de TI/Governança
- Desenvolver apresentações HTML profissionais com Tailwind CSS, Mermaid e Chart.js

Seu público: CTO/CIO, CEO/Diretoria e Comitê de TI/Governança.
Tom: Estratégico com referências técnicas — direto, executivo, sem jargão desnecessário.

## REGRA DE IDIOMA — PORTUGUÊS DO BRASIL

Escreva TODO o conteúdo em português do Brasil, sem exceções, incluindo:
títulos, subtítulos, descrições, análises, recomendações, rótulos de tabelas,
legendas de gráficos e textos de slides.

Mantenha em inglês APENAS termos técnicos que satisfaçam os dois critérios simultaneamente:
  1. Não possuem tradução consagrada em português técnico
  2. São amplamente reconhecidos e utilizados em português pelo mercado de TI brasileiro

Exemplos de termos que DEVEM permanecer em inglês:
  vendor lock-in, stack, pipeline, deploy, cluster, container, runtime,
  framework, branch, commit, merge, throughput, latency, uptime, SLA, API,
  endpoint, backend, frontend, middleware, cache, payload, token, stream

Exemplos de termos que DEVEM ser traduzidos:
  "Knowledge Transfer"       → Transferência de Conhecimento
  "Security Vulnerabilities" → Vulnerabilidades de Segurança
  "Inadequate Documentation" → Documentação Inadequada
  "Single Point of Failure"  → Ponto Único de Falha
  "High Availability"        → Alta Disponibilidade
  "Disaster Recovery"        → Recuperação de Desastres
  "Change Management"        → Gestão de Mudanças

Quando um título misturar termo técnico com palavras comuns, traduza as palavras
comuns e mantenha apenas o termo técnico em inglês:
  "Security Vulnerabilities em Nova Stack" → "Vulnerabilidades de Segurança em Nova Stack"
  "Inadequate Documentation/Knowledge Transfer" → "Documentação Inadequada / Transferência de Conhecimento"

Em caso de dúvida sobre se um termo deve ser mantido em inglês, prefira a tradução.

## DIRETRIZES DE GERAÇÃO HTML

- Gere um único arquivo HTML completo, válido e auto-contido
- Use Tailwind CSS via CDN: https://cdn.tailwindcss.com
- Use Mermaid via CDN: https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js
- Use Chart.js via CDN: https://cdn.jsdelivr.net/npm/chart.js
- Layout: scroll único com seções bem delimitadas
- Identidade visual: defina uma paleta coerente com o contexto da organização extraído dos documentos
  (ex: instituição pública → azul institucional + branco; fintech → dark + verde; indústria → dark + laranja)
- Cada seção deve ter UMA mensagem principal clara
- O HTML deve abrir corretamente em qualquer browser moderno sem servidor
- NÃO use frameworks JS além de Mermaid e Chart.js
- NÃO use imports ES6 ou fetch() — tudo inline
- Inicialize o Mermaid com: mermaid.initialize({ startOnLoad: true, theme: 'dark' })
- Todo código JavaScript deve estar em uma única tag <script> no final do <body>
- Os canvas do Chart.js devem ter IDs únicos: radarChart e barChart
"""

USER_PROMPT_TEMPLATE = """Com base nos documentos abaixo, gere um Pitch Deck executivo completo em HTML seguindo EXATAMENTE a estrutura especificada.

---
## BLUEPRINT
{blueprint}

---
## ARCHITECTURAL VISION
{architectural_vision}

---
## PDTI
{pdti}

---
## AS-IS
{as_is}

---
## ANÁLISE DE GAPS
{gap_analysis}

---
## TO-BE
{to_be}

---

## ESTRUTURA OBRIGATÓRIA DO HTML

Gere o arquivo HTML completo com as seguintes seções nesta ordem.
IMPORTANTE: retorne APENAS o HTML — sem markdown, sem blocos de código, sem explicações.
Comece com <!DOCTYPE html> e termine com </html>.

### SEÇÃO 1 — HERO (tela cheia, min-h-screen)
- H1: nome da iniciativa (extrair do blueprint ou PDTI)
- Subtítulo: síntese do objetivo da transformação em 1 frase
- Caixa de destaque: "ponto de inflexão" — frase executiva que resume o diagnóstico central
- Rodapé do hero: barra com 3-4 métricas de contexto
  (ex: total de GAPs, total de iniciativas PDTI afetadas, dimensões analisadas)

### SEÇÃO 2 — CONTEXTO ESTRATÉGICO
- Título: "Por que agir agora?"
- Grid 2 colunas:
  - Esquerda: 3-4 objetivos estratégicos do PDTI que motivam a transformação
  - Direita: card com a citação ou síntese mais impactante do PDTI sobre urgência

### SEÇÃO 3 — DIAGNÓSTICO ATUAL
- Título: "Onde estamos hoje"
- Placeholder de diagrama AS-IS estilizado com instruções de substituição
- Grid de 4-6 cards de problemas extraídos do gap_analysis.md:
  - Cor do título: vermelho = crítico, laranja = alto, amarelo = médio
  - Nome do GAP traduzido para português
  - Impacto no negócio em 2 linhas (sem jargão técnico)
  - Badge com ID do GAP (ex: GAP-ARQ-01)

### SEÇÃO 4 — ARQUITETURA FUTURA
- Título: "Para onde vamos"
- Placeholder de diagrama TO-BE estilizado com instruções de substituição
- Grid 3 colunas com os principais novos componentes do to_be.md:
  - Nome do componente, tecnologia adotada, benefício direto

### SEÇÃO 5 — RACIONAL DAS DECISÕES
- Título: "Por que essa solução?"
- Tabela: Decisão | Alternativas Avaliadas | Por que escolhemos
  (3-4 linhas com dados reais do to_be.md e architectural_vision.md)
- Caixa com 3-4 princípios arquiteturais que guiaram a solução

### SEÇÃO 6 — GANHOS ESPERADOS
- Título: "O que vamos conquistar"
- 3 métricas de impacto em destaque (números grandes, cor verde)
- Gráfico Radar Chart.js (id="radarChart"):
  - 7 dimensões: Arquitetura, Tecnologia, Infraestrutura, Observabilidade, Segurança, Processos, Pessoas
  - Dataset AS-IS: valores reais do Score Atual do gap_analysis.md, cor vermelha semitransparente
  - Dataset TO-BE: valores reais do Score Alvo do gap_analysis.md, cor verde semitransparente
- Gráfico de Barras Chart.js (id="barChart"):
  - Mesmas 7 dimensões e mesmos valores, barras lado a lado, mesmas cores

### SEÇÃO 7 — ADERÊNCIA AO PDTI E RESOLUÇÃO DE GAPS
- Título: "Aderência ao PDTI e resolução de GAPs"
- Contador em destaque: "X de Y GAPs endereçados no TO-BE"
- Tabela: GAP | Criticidade | Iniciativa PDTI | Status no TO-BE
  - Badges coloridos: verde = Endereçado, amarelo = Parcial, azul = Roadmap
  - Cruzar gap_analysis.md com to_be.md para determinar o status de cada GAP

### SEÇÃO 8 — ROADMAP
- Título: "Como chegamos lá"
- Diagrama Gantt Mermaid com fases e iniciativas REAIS do to_be.md
  Usar datas relativas a partir de 2025-01 se não houver datas nos documentos
- 3-4 marcos principais abaixo do Gantt

### SEÇÃO 9 — DECISÃO EXECUTIVA
- Título: "O que precisamos decidir"
- Tabela de decisões necessárias com responsável e prazo
- Tabela de próximas ações imediatas
- Caixa vermelha: "Custo de inação" — 2-3 riscos de manter o AS-IS
- Caixa verde: call-to-action — "A equipe está pronta para iniciar a Fase 1 mediante aprovação"

### SCRIPT (único bloco no final do body)
- mermaid.initialize({{ startOnLoad: true, theme: 'dark' }})
- document.addEventListener('DOMContentLoaded', function() {{ ... }}) com os dois gráficos Chart.js
- Dados dos gráficos: valores REAIS extraídos dos scores do gap_analysis.md

## REGRAS FINAIS
1. Arquivo único, completo, do <!DOCTYPE html> ao </html>
2. NÃO inclua markdown, blocos ```, explicações ou qualquer texto fora do HTML
3. Todos os dados (cards, tabelas, gráficos, gantt) devem ser REAIS — extraídos dos documentos
4. Comece com <!DOCTYPE html> — sem nenhum caractere antes disso
"""


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def load_required_file(path: Path, label: str) -> str:
    """Carrega um arquivo obrigatório; encerra com erro claro se não existir."""
    if not path.exists():
        print(f"❌ ERRO: {label} não encontrado em: {path}")
        sys.exit(1)
    content = path.read_text(encoding="utf-8")
    print(f"  ✓ {label:<30} ({len(content):>10,} chars)")
    return content


def clean_html_output(raw: str) -> str:
    """
    Remove blocos de código markdown caso o LLM embrulhe o HTML.
    Garante que o output começa com <!DOCTYPE html>.
    """
    html = raw.strip()

    # Remove wrapper ```html ... ``` ou ``` ... ```
    if html.startswith("```"):
        lines = html.splitlines()
        # Remove primeira linha (```html ou ```) e última (```)
        end = len(lines) - 1
        while end > 0 and lines[end].strip() in ("```", ""):
            end -= 1
        html = "\n".join(lines[1:end + 1]).strip()

    # Garante que começa com doctype
    lower = html.lower()
    doctype_pos = lower.find("<!doctype html>")
    if doctype_pos > 0:
        html = html[doctype_pos:]

    return html


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    print_banner("AGENTE 4 — Pitch Deck Executivo (HTML)")

    root        = Path(__file__).resolve().parent.parent
    inputs_dir  = root / "inputs"
    outputs_dir = root / "outputs"

    # ── Verificar pré-requisitos ──────────────────────────────────────────────
    prereqs = {
        "as_is.md":        ("agent_asis.py",  outputs_dir / "as_is.md"),
        "gap_analysis.md": ("agent_gap.py",   outputs_dir / "gap_analysis.md"),
        "to_be.md":        ("agent_tobe.py",  outputs_dir / "to_be.md"),
    }

    missing = [
        (label, agent, path)
        for label, (agent, path) in prereqs.items()
        if not path.exists()
    ]

    if missing:
        print("\n❌ ERRO: Os seguintes outputs de agentes anteriores estão faltando:\n")
        for label, agent, path in missing:
            print(f"   • {label:<25} → Execute primeiro: python agents/{agent}")
        print()
        sys.exit(1)

    # ── Carregar inputs ───────────────────────────────────────────────────────
    print("\n📂 Carregando arquivos de input...\n")

    blueprint            = load_required_file(inputs_dir  / "blueprint.md",            "blueprint.md")
    architectural_vision = load_required_file(inputs_dir  / "architectural_vision.md", "architectural_vision.md")
    pdti                 = load_required_file(inputs_dir  / "pdti.md",                 "pdti.md")
    as_is                = load_required_file(outputs_dir / "as_is.md",                "as_is.md")
    gap_analysis         = load_required_file(outputs_dir / "gap_analysis.md",         "gap_analysis.md")
    to_be                = load_required_file(outputs_dir / "to_be.md",                "to_be.md")

    total_chars = sum(len(x) for x in [blueprint, architectural_vision, pdti, as_is, gap_analysis, to_be])
    print(f"\n  📊 Total de contexto: {total_chars:,} caracteres")

    # ── Montar prompt e chamar LLM ────────────────────────────────────────────
    user_prompt = USER_PROMPT_TEMPLATE.format(
        blueprint=blueprint,
        architectural_vision=architectural_vision,
        pdti=pdti,
        as_is=as_is,
        gap_analysis=gap_analysis,
        to_be=to_be,
    )

    print("\n📡 Chamando API Anthropic...")
    result = call_llm(SYSTEM_PROMPT, user_prompt)

    # ── Limpar e salvar output ────────────────────────────────────────────────
    html = clean_html_output(result)
    output_path = write_output("pitch_deck.html", html)
    print_success(output_path)

    print("\n💡 Como abrir o pitch deck:\n")
    print("   Browser  →  Abra tools/outputs/pitch_deck.html diretamente no browser")
    print("   PDF      →  No browser: Ctrl+P → Salvar como PDF")
    print()


if __name__ == "__main__":
    main()