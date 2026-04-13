"""
C-Level Strategic Report Agent — v2
=====================================
Lê os relatórios gerados pelos agentes anteriores e produz um relatório
estratégico consolidado com visão executiva, diagramas Mermaid e fallbacks.

Inputs (encontrados automaticamente por glob — mais recente de cada):
  - outputs/Gap_Analysis_*.md        (gap_analyzer.py)
  - outputs/TO_BE_Model_v4_*.md      (to_be_generator.py)

Outputs:
  - outputs/CLevel_Report_*.md

Mudanças em relação à v1:
  - Remove dependência de core/llm (chama anthropic diretamente)
  - Geração em múltiplas chamadas para evitar truncamento
  - Caminhos alinhados com os outros agentes do pipeline
  - Slicing de contexto por seção para não estourar janela
  - find_latest_* para encontrar arquivos mais recentes por glob
"""

import os
import time
from pathlib import Path
from datetime import datetime

import anthropic

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# =============================================================================
# Configuração
# =============================================================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL      = "claude-sonnet-4-20250514"
MAX_TOKENS = 8000

OUTPUT_DIR = Path("outputs/reports")

# =============================================================================
# System prompt — mantido da v1, é bom
# =============================================================================
SYSTEM_PROMPT = """
Você é um consultor sênior especialista em transformação digital e comunicação executiva.
Sua tarefa é analisar documentos técnicos (GAPs, TO-BE) e produzir seções de um relatório
estratégico de alto impacto para audiência C-Level (CEO, CTO, CIO, CFO).

## PRINCÍPIOS

- Linguagem de negócio no primeiro plano; profundidade técnica como suporte
- Cada seção deve ter pelo menos um diagrama Mermaid seguido de fallback
- Cada seção deve deixar claro o que está em jogo e o que precisa ser decidido
- Se um termo técnico aparecer, explique em uma linha o impacto de negócio

## REGRAS PARA DIAGRAMAS MERMAID

1. Gere o bloco Mermaid PRIMEIRO, depois o fallback logo abaixo
2. quadrantChart: distribua itens no espaço completo [0.1–0.9] em ambos os eixos.
   Evite aglomeração no centro. Conte uma história visual clara.
3. graph LR/TD: subgraphs por camada/domínio. Labels com máximo 4 palavras por nó.
4. gantt: seções por onda. Datas em formato YYYY-MM.
5. Todo diagrama Mermaid deve ter fallback em tabela ou lista logo abaixo,
   separado por comentário <!-- FALLBACK -->.

## REGRAS PARA INFERÊNCIA

- Maturidade por Domínio: Impacto (negócio) × Maturidade (qualidade atual)
- Priorização: Esforço × Impacto. Quick Wins = baixo esforço + alto impacto
- Ondas: Quick Wins (0-3m) | Fundação (3-9m) | Escala (9-18m)
- Riscos: extraia dos GAPs. Classifique probabilidade e impacto: Alto/Médio/Baixo
- Use badges: 🔴 Crítico · 🟡 Atenção · 🟢 Saudável

## FORMATO

Markdown estruturado, pronto para Notion/Confluence ou conversão em apresentação.
Use `---` entre seções principais.
"""

# =============================================================================
# Localização de arquivos
# =============================================================================

def find_latest(pattern: str, base: Path = OUTPUT_DIR) -> Path | None:
    files = list(base.glob(pattern))
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def load_file(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

# =============================================================================
# Chamada ao modelo com retry
# =============================================================================

def call_model(client: anthropic.Anthropic, user_prompt: str, label: str) -> str:
    for attempt in range(1, 4):
        try:
            print(f"      → {label} (tentativa {attempt})...")
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=0.3,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            text = resp.content[0].text
            print(f"         ✅ {len(text):,} chars")
            return text
        except Exception as e:
            print(f"         ⚠️  Erro: {e}")
            if attempt < 3:
                time.sleep(5 * attempt)
            else:
                raise
    return ""

# =============================================================================
# Prompts por seção
# =============================================================================

def prompt_section1_executive_summary(gaps: str, to_be: str) -> str:
    return f"""
# INPUTS

## Gap Analysis (primeiros 6000 chars)
{gaps[:6000]}

## TO-BE (primeiros 4000 chars)
{to_be[:4000]}

---

# INSTRUÇÃO

Gere APENAS as seções abaixo. Não gere nada além delas.

---

# 📊 Relatório Estratégico — Transformação Digital
> *Documento executivo confidencial · {datetime.now().strftime("%d/%m/%Y")}*

---

## 1. Executive Summary

Escreva 6-8 bullets de alto impacto cobrindo:
- Contexto do ecossistema atual (dados reais dos inputs)
- Principais problemas identificados com impacto de negócio
- Visão do estado futuro
- O que está em jogo se não agirmos
- Próximos passos críticos

**Use números reais dos documentos. Não invente métricas.**

---

[PARE AQUI.]
"""


def prompt_section2_as_is(gaps: str) -> str:
    return f"""
# INPUTS

## Gap Analysis — Sumário e Dimensões
{gaps[:10000]}

---

# INSTRUÇÃO

Gere APENAS as seções abaixo.

---

## 2. Cenário Atual — AS-IS

### 2.1 Arquitetura High-Level

```mermaid
graph LR
    subgraph "Experiência"
        A[Web/Mobile]
    end
    subgraph "APIs"
        B[BFFs]
        C[Serviços]
    end
    subgraph "Infra"
        D[Azure DevOps]
        E[Kubernetes]
    end
    A --> B --> C --> D & E
```

[Adapte o diagrama ao ecossistema real descrito nos inputs.
Use subgraphs por camada. Labels curtos.]

<!-- FALLBACK -->
**Fallback — Camadas do ecossistema atual:**
[Lista indentada com as camadas e componentes reais]

---

### 2.2 Maturidade por Domínio

```mermaid
quadrantChart
    title Maturidade por Domínio (AS-IS)
    x-axis Baixo Impacto --> Alto Impacto
    y-axis Baixa Maturidade --> Alta Maturidade
    quadrant-1 Investir Agora
    quadrant-2 Manter
    quadrant-3 Monitorar
    quadrant-4 Otimizar Urgente
    [posicione cada domínio usando dados reais dos scores do gap analysis]
    [ex: DevOps está em score 3.09/5 — posicione com maturidade ~0.62]
    [use o espaço completo 0.1–0.9 em ambos os eixos]
```

<!-- FALLBACK -->
| Domínio | Score /5 | Impacto no Negócio | Quadrante |
|---------|----------|--------------------|-----------|
[use scores reais do gap analysis]

---

### 2.3 Stakeholders e Impactos

```mermaid
graph TD
    [diagrama de stakeholders com suas dores específicas]
```

<!-- FALLBACK -->
[Lista indentada de stakeholders e impactos]

---

[PARE AQUI.]
"""


def prompt_section3_gaps(gaps: str) -> str:
    return f"""
# INPUTS

## Gap Analysis Completo
{gaps[:12000]}

---

# INSTRUÇÃO

Gere APENAS as seções abaixo. Use dados reais e números exatos dos inputs.

---

## 3. Diagnóstico de GAPs

### 3.1 Matriz de GAPs

```mermaid
quadrantChart
    title GAPs por Impacto × Criticidade
    x-axis Baixa Criticidade --> Alta Criticidade
    y-axis Baixo Impacto --> Alto Impacto
    quadrant-1 Resolver Agora
    quadrant-2 Planejar
    quadrant-3 Backlog
    quadrant-4 Monitorar
    [posicione cada gap principal usando os dados reais]
    [gaps com score < 2/5 E muitos apps afetados = alta criticidade + alto impacto]
    [distribua no espaço 0.1–0.9 — não aglomere no centro]
```

<!-- FALLBACK -->
| GAP | Criticidade | Impacto | Cuadrante |
|-----|------------|---------|-----------|
[use os gaps reais do gap analysis]

---

### 3.2 Detalhamento dos GAPs Críticos

Tabela com os gaps mais críticos:

| GAP | Domínio | Apps Afetadas | Impacto no Negócio | Status |
|-----|---------|--------------|-------------------|--------|
[use dados reais — contagens exatas de apps afetadas]
[🔴 score < 2/5 · 🟡 score 2–3/5 · 🟢 score > 3/5]

---

[PARE AQUI.]
"""


def prompt_section4_to_be(to_be: str, gaps: str) -> str:
    return f"""
# INPUTS

## TO-BE Model
{to_be[:10000]}

## Gap Analysis (resumo)
{gaps[:3000]}

---

# INSTRUÇÃO

Gere APENAS as seções abaixo.

---

## 4. Visão Futura — TO-BE

### 4.1 Arquitetura High-Level

```mermaid
graph LR
    [diagrama do ecossistema futuro]
    [use subgraphs por camada/domínio]
    [labels: NOVO vs EVOLUÍDO vs MANTIDO]
```

<!-- FALLBACK -->
[Lista das camadas futuras com o que muda]

---

### 4.2 Priorização de Iniciativas

```mermaid
quadrantChart
    title Priorização de Iniciativas (TO-BE)
    x-axis Alto Esforço --> Baixo Esforço
    y-axis Baixo Impacto --> Alto Impacto
    quadrant-1 Quick Wins
    quadrant-2 Projetos Estratégicos
    quadrant-3 Baixa Prioridade
    quadrant-4 Cuidado: Custo Oculto
    [posicione as iniciativas reais do TO-BE]
    [use o espaço completo 0.1–0.9 — distribua bem]
```

<!-- FALLBACK -->
| Iniciativa | Esforço | Impacto | Quadrante |
|-----------|---------|---------|-----------|
[iniciativas reais do TO-BE]

---

### 4.3 Princípios da Arquitetura TO-BE

```mermaid
graph LR
    [diagrama dos princípios arquiteturais e suas implementações práticas]
```

<!-- FALLBACK -->
[Lista dos princípios com implementação prática]

---

[PARE AQUI.]
"""


def prompt_section5_roadmap(to_be: str, gaps: str) -> str:
    return f"""
# INPUTS

## TO-BE — Estratégia de Evolução e Ondas
{to_be[8000:18000]}

## Gap Analysis — ROI por Ondas
{gaps[20000:30000]}

---

# INSTRUÇÃO

Gere APENAS as seções abaixo. Use os itens reais dos documentos.

---

## 5. Roadmap de Transformação

### 5.1 Timeline por Ondas

```mermaid
gantt
    title Roadmap de Transformação
    dateFormat YYYY-MM
    section Onda 1 — Quick Wins (0-3m)
    [iniciativas reais] :2026-04, 1M
    section Onda 2 — Fundação (3-9m)
    [iniciativas reais] :2026-07, 3M
    section Onda 3 — Escala (9-18m)
    [iniciativas reais] :2026-10, 6M
```

<!-- FALLBACK -->
| Iniciativa | Onda | Prazo | GAP Resolvido | Esforço |
|-----------|------|-------|---------------|---------|
[itens reais dos documentos]

---

### 5.2 Dependências Críticas

[Liste as dependências entre iniciativas que podem travar o roadmap.
Baseie-se nas dependências reais identificadas no TO-BE.]

---

[PARE AQUI.]
"""


def prompt_section6_risks_governance(gaps: str, to_be: str) -> str:
    return f"""
# INPUTS

## Gap Analysis — Riscos e Gaps Críticos
{gaps[10000:20000]}

## TO-BE — Governança e Riscos
{to_be[15000:22000]}

---

# INSTRUÇÃO

Gere APENAS as seções abaixo.

---

## 6. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação | Responsável Sugerido |
|-------|--------------|---------|-----------|---------------------|
[top 5 riscos reais extraídos dos documentos]
[baseie probabilidade e impacto nos dados reais — ex: Azure KeyVault em 2.6% = risco de segurança Alto]

---

## 7. Governança e Call to Action

### 7.1 Modelo de Governança

```mermaid
graph TD
    [diagrama do comitê de transformação, responsabilidades e cadências]
```

<!-- FALLBACK -->
[Lista indentada de papéis, responsabilidades e cadências]

---

### 7.2 Decisões Necessárias

[Liste o que o C-Level precisa aprovar, priorizar ou desbloquear.]
Use o formato: **[DECISÃO N]** Descrição — *Impacto se não decidido*

---

### 7.3 Próximos 30 Dias

[3-5 ações concretas que devem começar imediatamente.
Baseie nos quick wins reais identificados nos documentos.]

---

*Arquiteto de Soluções/IA · {datetime.now().strftime("%d/%m/%Y")} · Versão 2.0*

---

[PARE AQUI.]
"""

# =============================================================================
# Agente principal
# =============================================================================

class CLevelReportAgent:

    def __init__(self, api_key: str = None):
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY não encontrada.")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def run(self):
        print("=" * 70)
        print("📊 C-LEVEL STRATEGIC REPORT AGENT v2")
        print("   Geração em múltiplas chamadas")
        print("=" * 70)

        # ── 1. Localiza inputs ───────────────────────────────────────────────
        print("\n📂 Localizando inputs...")

        gap_file = find_latest("gaps*.md")
        if not gap_file:
            raise FileNotFoundError(
                "Nenhum Gap_Analysis_*.md encontrado em outputs/.\n"
                "Execute gap_analyzer.py antes deste agente."
            )
        gaps = load_file(gap_file)
        print(f"   ✅ Gap Analysis : {gap_file.name} ({len(gaps):,} chars)")

        to_be_file = find_latest("to-be*.md")
        if not to_be_file:
            raise FileNotFoundError(
                "Nenhum TO_BE_Model_v4_*.md encontrado em outputs/.\n"
                "Execute to_be_generator.py antes deste agente."
            )
        to_be = load_file(to_be_file)
        print(f"   ✅ TO-BE Model  : {to_be_file.name} ({len(to_be):,} chars)")

        # ── 2. Geração em múltiplas chamadas ─────────────────────────────────
        print("\n🤖 Gerando relatório C-Level em 6 chamadas...")

        sections: list[str] = []

        sections.append(call_model(
            self.client,
            prompt_section1_executive_summary(gaps, to_be),
            "Seção 1 — Executive Summary",
        ))

        sections.append(call_model(
            self.client,
            prompt_section2_as_is(gaps),
            "Seção 2 — Cenário Atual (AS-IS)",
        ))

        sections.append(call_model(
            self.client,
            prompt_section3_gaps(gaps),
            "Seção 3 — Diagnóstico de GAPs",
        ))

        sections.append(call_model(
            self.client,
            prompt_section4_to_be(to_be, gaps),
            "Seção 4 — Visão Futura (TO-BE)",
        ))

        sections.append(call_model(
            self.client,
            prompt_section5_roadmap(to_be, gaps),
            "Seção 5 — Roadmap de Transformação",
        ))

        sections.append(call_model(
            self.client,
            prompt_section6_risks_governance(gaps, to_be),
            "Seção 6 — Riscos e Governança",
        ))

        # ── 3. Consolida e salva ─────────────────────────────────────────────
        full_report = "\n\n---\n\n".join(s.strip() for s in sections if s.strip())

        OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file  = OUTPUT_DIR / f"CLevel_Report_{timestamp}.md"

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(full_report)

        print(f"\n✅ Relatório C-Level gerado!")
        print(f"📄 {out_file}")
        print(f"📊 {len(full_report):,} chars | {len(sections)} seções")

        print("\n" + "=" * 70)
        print("✅ PIPELINE COMPLETO")
        print("=" * 70)
        print("   gap_analyzer.py      → ✅ concluído")
        print("   to_be_generator.py   → ✅ concluído")
        print("   clevel_report_agent.py → ✅ concluído")
        print("=" * 70)

        return out_file


# =============================================================================
# Entry point
# =============================================================================

def main():
    if not ANTHROPIC_API_KEY:
        print("❌ ANTHROPIC_API_KEY não configurada.")
        return
    try:
        CLevelReportAgent().run()
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()