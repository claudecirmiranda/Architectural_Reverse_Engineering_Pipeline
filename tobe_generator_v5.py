"""
TO-BE Generator — v4
====================
Inputs obrigatórios:
  - outputs/portfolio_structured.json   (parser determinístico)
  - outputs/Gap_Analysis_*.md           (relatório de gap — mais recente)

Input opcional:
  - outputs/Concept_NAV_360.md          (visão estratégica de negócio)

Mudanças em relação à v3:
  - Remove load_all_blueprints() e cálculo manual de portfolio_stats
  - portfolio_structured.json é a única fonte de verdade de dados do portfólio
  - Cada parte recebe apenas os sinais relevantes do JSON (não o JSON inteiro)
  - glob corrigido para Gap_Analysis_*.md (novo padrão do gap analyzer v5)
  - Geração em múltiplas chamadas (mesmo padrão do gap analyzer v5)
"""

import json
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

JSON_PATH = Path("outputs/portfolio_structured.json")

# Mapeamento de dimensão → sinais (espelha o gap analyzer)
DIM_SIGNALS = {
    "observability": ["apm", "health_check", "structured_logging"],
    "quality":       ["jest", "playwright", "supertest", "sonarqube"],
    "security":      ["azure_keyvault", "keycloak", "jwt", "passport"],
    "devops":        ["azure_devops", "github_actions", "docker", "kubernetes"],
    "architecture":  ["clean_architecture", "ddd", "event_driven", "graphql_federation", "swagger"],
    "documentation": ["swagger", "readme_documented"],
}

# Sinais relevantes por área de decisão técnica
AREA_SIGNALS = {
    "stack":         ["nodejs", "typescript", "nestjs", "express", "react", "expo", "nextjs"],
    "architecture":  ["clean_architecture", "ddd", "event_driven", "graphql_federation", "graphql"],
    "apis":          ["graphql", "graphql_federation", "swagger", "grpc"],
    "observability": ["apm", "health_check", "structured_logging", "dynatrace", "elastic_apm", "opentelemetry"],
    "security":      ["azure_keyvault", "keycloak", "jwt", "passport", "sast"],
    "cicd":          ["azure_devops", "github_actions", "docker", "kubernetes", "gitops"],
    "data":          ["postgresql", "mongodb", "redis", "mssql", "cosmosdb", "azure_eventhubs", "azure_servicebus"],
}

# =============================================================================
# Carregamento de arquivos
# =============================================================================

def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo obrigatório não encontrado: {path}\n"
            "Execute o parser determinístico antes deste agente."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def find_latest_gap_analysis(base_dir: Path = Path("outputs")) -> Path | None:
    """Encontra o relatório de gap mais recente (padrão v5: Gap_Analysis_*.md)."""
    files = list(base_dir.glob("gaps*.md"))
    if not files:
        return None
    return max(files, key=lambda p: p.stat().st_mtime)


def find_concept_nav360(base_dir: Path = Path("outputs")) -> Path | None:
    candidates = [
        base_dir / "Concept_NAV_360.md",
        base_dir / "concept_nav_360.md",
        base_dir / "Concept NAV 360.md",
        Path("Concept_NAV_360.md"),
    ]
    return next((p for p in candidates if p.exists()), None)


# =============================================================================
# Extração de contexto por área a partir do JSON
# =============================================================================

def extract_portfolio_summary(data: dict) -> str:
    """Resumo compacto do portfólio para injetar em todas as partes."""
    sc = data.get("signal_coverage", {})
    da = data.get("dimension_averages", {})

    ctx  = f"## Portfólio: {data['total_apps']} apps | {data['total_projects']} projetos\n"
    ctx += f"Repos vazios: {', '.join(data.get('empty_repos', [])) or 'nenhum'}\n\n"

    ctx += "### Scores de Dimensão\n"
    ctx += "| Dimensão | Score /5 | Cobertura % |\n"
    ctx += "|----------|----------|-------------|\n"
    for dim, v in da.items():
        ctx += f"| {dim.capitalize()} | {v['avg_score']:.2f} | {v['avg_coverage_pct']:.1f}% |\n"
    ctx += "\n"

    ctx += "### Sinais Críticos\n"
    ctx += "| Sinal | % Com | % Sem |\n"
    ctx += "|-------|-------|-------|\n"
    for sig in ["health_check", "structured_logging", "apm", "jest", "docker",
                "swagger", "azure_keyvault", "azure_devops"]:
        if sig in sc:
            v = sc[sig]
            ctx += f"| {v['label']} | {v['pct_with']}% | {v['pct_without']}% |\n"
    ctx += "\n"

    ctx += "### Top Débito Técnico (apps, excluindo repos vazios)\n"
    empty = set(data.get("empty_repos", []))
    for e in data.get("top_debt_apps", []):
        if e["app"] not in empty:
            ctx += f"- **{e['app']}**: {e['critical_gap_count']} gaps críticos ({', '.join(e['critical_gaps'])})\n"
    return ctx


def extract_area_context(data: dict, area: str) -> str:
    """Extrai sinais e cobertura relevantes para uma área de decisão técnica."""
    sc      = data.get("signal_coverage", {})
    signals = AREA_SIGNALS.get(area, [])
    empty   = set(data.get("empty_repos", []))

    ctx = f"### Contexto de Dados — Área: {area}\n\n"
    ctx += "| Sinal | % Com | Apps COM | Apps SEM |\n"
    ctx += "|-------|-------|----------|----------|\n"

    for sig in signals:
        if sig not in sc:
            continue
        v = sc[sig]
        apps_with = ", ".join(a["app"] for a in v.get("apps_with", [])) or "—"
        apps_wo   = ", ".join(
            (a if isinstance(a, str) else a.get("app", ""))
            for a in v.get("apps_without", [])
            if (a if isinstance(a, str) else a.get("app", "")) not in empty
        ) or "—"
        ctx += f"| {v['label']} | {v['pct_with']}% | {apps_with} | {apps_wo} |\n"

    # Dimensão correspondente se houver
    dim_map = {
        "observability": "observability",
        "security":      "security",
        "cicd":          "devops",
        "architecture":  "architecture",
        "apis":          "architecture",
        "stack":         None,
        "data":          None,
    }
    dim = dim_map.get(area)
    if dim and dim in data.get("dimension_averages", {}):
        v = data["dimension_averages"][dim]
        ctx += f"\n**Score da dimensão '{dim}':** {v['avg_score']:.2f}/5 ({v['avg_coverage_pct']:.1f}%) — {v['calc']}\n"

    return ctx


def extract_dimension_context(data: dict, dim: str) -> str:
    """Extrai contexto completo de uma dimensão com evidências por app."""
    sc     = data.get("signal_coverage", {})
    da     = data.get("dimension_averages", {})
    empty  = set(data.get("empty_repos", []))
    sigs   = DIM_SIGNALS.get(dim, [])

    ctx  = f"### Dimensão: {dim.capitalize()}\n"
    if dim in da:
        v = da[dim]
        ctx += f"Score: {v['avg_score']:.2f}/5 | Cobertura: {v['avg_coverage_pct']:.1f}% | Cálculo: {v['calc']}\n\n"

    for sig in sigs:
        if sig not in sc:
            continue
        v = sc[sig]
        ctx += f"**{v['label']}** — {v['pct_with']}% ({v['count_with']}/{v['total']})\n"
        ctx += "  Com: " + ", ".join(a["app"] for a in v.get("apps_with", [])) + "\n"
        wo = [
            (a if isinstance(a, str) else a.get("app", ""))
            for a in v.get("apps_without", [])
            if (a if isinstance(a, str) else a.get("app", "")) not in empty
        ]
        ctx += "  Sem: " + ", ".join(wo) + "\n\n"
    return ctx


# =============================================================================
# Chamada ao modelo com retry
# =============================================================================

def call_model(client: anthropic.Anthropic, prompt: str, label: str) -> str:
    for attempt in range(1, 4):
        try:
            print(f"      → {label} (tentativa {attempt})...")
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
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
# Prompts por parte
# =============================================================================

PREAMBLE = """Você é um Arquiteto de Soluções Sênior criando um Modelo TO-BE.

REGRAS:
- Baseie decisões nos gaps e dados reais fornecidos — não invente tecnologias ausentes
- Toda decisão técnica deve referenciar o gap que resolve e os apps afetados
- Use os nomes reais dos apps do portfólio ao listar impactos
- Não quantifique ROI ou custos — isso está em documento separado
"""


def prompt_part1(portfolio_summary: str, gap_analysis: str, concept: str | None, data: dict) -> str:
    concept_section = f"\n### Concept NAV 360 (primeiros 6000 chars)\n{concept[:6000]}" if concept else ""
    return f"""{PREAMBLE}

# DADOS DO PORTFÓLIO
{portfolio_summary}

# GAP ANALYSIS (primeiros 8000 chars)
{gap_analysis[:8000]}
{concept_section}

---

# INSTRUÇÃO

Gere APENAS as seções abaixo. Não gere nada além delas. Não inclua índice.

---

# 🎯 MODELO TO-BE — Arquitetura Futura

**Versão:** 2.0
**Data:** {datetime.now().strftime("%d/%m/%Y")}
**Baseado em:** Análise de Gaps | portfolio_structured.json | Concept NAV 360

---

## 📊 SUMÁRIO EXECUTIVO

### Propósito do TO-BE

[2-3 parágrafos: por que foi criado, principais transformações, valor esperado]

### Perfil Atual do Portfólio

[Use os dados reais do JSON acima. Organize por camadas:
- Runtime & Linguagem: [% real]
- Frameworks: [% real]  
- Containerização: [% real]
- Maturidade por dimensão: [scores reais]]

### Top 5 Gaps que o TO-BE Resolve

[Liste com: nome do gap | severidade | apps afetadas (contagem real) | impacto]

### Funcionalidades Estratégicas Habilitadas

[Se Concept NAV 360 disponível: liste as principais funcionalidades viabilizadas.
Se não disponível: liste capacidades técnicas habilitadas pelos gaps resolvidos.]

---

## 🎯 PRINCÍPIOS NORTEADORES

[5-7 princípios. Para cada um:]

### [N]. [Nome do Princípio]

**Gap que motivou:** [referência ao gap real]
**Descrição:** [o que significa]
**Aplicação:** [como será implementado no portfólio]

---

## 📊 VISÃO GERAL DA TRANSFORMAÇÃO

| Dimensão | AS-IS (dados reais) | TO-BE | Gap Resolvido | Benefício |
|----------|---------------------|-------|---------------|-----------|
[Use os scores e % reais do JSON para a coluna AS-IS.
8 linhas: Arquitetura, Stack, Cloud-Native, APIs, Observabilidade, Segurança, CI/CD, Dados]

---

[PARE AQUI.]
"""


def prompt_part2(portfolio_summary: str, gap_analysis: str, concept: str | None) -> str:
    concept_section = f"\n### Concept NAV 360\n{concept[:4000]}" if concept else ""
    return f"""{PREAMBLE}

# DADOS DO PORTFÓLIO
{portfolio_summary}

# GAP ANALYSIS (arquitetura e cloud — primeiros 6000 chars)
{gap_analysis[:6000]}
{concept_section}

---

# INSTRUÇÃO

Gere APENAS as seções abaixo.

---

## 🏗️ ARQUITETURA DE REFERÊNCIA TO-BE

### Visão Arquitetural

```mermaid
graph TB
    subgraph "Camada de Experiência"
        A[Web App]
        B[Mobile App]
    end
    subgraph "API Gateway / BFF"
        C[API Gateway]
        D[BFF Web]
        E[BFF Mobile]
    end
    subgraph "Serviços de Negócio"
        F[Serviços Core]
        G[Serviços de Suporte]
    end
    subgraph "Dados"
        H[PostgreSQL]
        I[Redis]
        J[Event Bus]
    end
    subgraph "Observabilidade"
        K[APM]
        L[Logs Estruturados]
        M[Health Checks]
    end
    A --> C
    B --> C
    C --> D & E
    D & E --> F
    F --> G
    F --> H & I & J
```

[Adapte o diagrama à realidade do portfólio — use os padrões reais identificados
(GraphQL Federation, NestJS BFFs, etc.)]

### Descrição das Camadas

[Para cada camada: responsabilidades, tecnologias TO-BE, gap que resolve]

---

## 🔧 DECISÕES TÉCNICAS — Stack e Frameworks

[Use os dados reais de nodejs/nestjs/express/react do JSON]

### Decisão: [Nome]

**Gap(s) que resolve:** [referência real]
**Apps afetadas:** [nomes reais]

**Especificação TO-BE:** [descrição técnica]
**Tecnologias:** [lista]
**Rationale:** [justificativa baseada nos gaps]

**Benefícios:**
- Técnico: [qualitativo]
- Operacional: [qualitativo]

**Trade-offs:** [limitações e riscos]

**Esforço de migração:** S/M/L/XL | **Prioridade:** P0/P1/P2

[3-4 decisões para esta área]

---

[PARE AQUI.]
"""


def prompt_part3(area_ctx: str, gap_analysis: str, area_name: str, concept: str | None) -> str:
    concept_hint = f"\nContexto NAV 360 relevante para {area_name}:\n{concept[:2000]}" if concept else ""
    return f"""{PREAMBLE}

# DADOS DO PORTFÓLIO — ÁREA: {area_name.upper()}
{area_ctx}

# GAP ANALYSIS — TRECHO RELEVANTE
{gap_analysis[2000:8000]}
{concept_hint}

---

# INSTRUÇÃO

Gere APENAS as decisões técnicas para a área **{area_name}**.
Use a estrutura abaixo para cada decisão.

---

## 🔧 DECISÕES TÉCNICAS — {area_name.upper()}

### Decisão: [Nome específico]

**Gap(s) que resolve:**
- [gap real com contagem de apps]

**Apps afetadas:** [nomes reais do portfólio]

**Especificação TO-BE:**
[Descrição técnica detalhada]

**Tecnologias/Ferramentas:** [lista]

**Exemplo de implementação:**
```typescript
// exemplo concreto se aplicável
```

**Rationale:** [por que esta decisão resolve os gaps]

**Benefícios:**
- Técnico: [qualitativo]
- Operacional: [qualitativo]

**Trade-offs e restrições:** [limitações reais]

**Esforço:** S/M/L/XL | **Prioridade:** P0/P1/P2 | **Dependências:** [outras decisões]

[3-5 decisões para esta área]

---

[PARE AQUI.]
"""


def prompt_part4(portfolio_summary: str, gap_analysis: str, concept: str | None) -> str:
    concept_section = f"\n### Concept NAV 360\n{concept[:5000]}" if concept else ""
    return f"""{PREAMBLE}

# DADOS DO PORTFÓLIO
{portfolio_summary}

# GAP ANALYSIS
{gap_analysis[4000:10000]}
{concept_section}

---

# INSTRUÇÃO

Gere APENAS as seções abaixo.

---

## 🎨 PADRÕES E GUIDELINES

### Estrutura de Código Padrão

```
app/
├── src/
│   ├── modules/        # módulos de negócio
│   ├── shared/         # código compartilhado
│   ├── infrastructure/ # integrações externas
│   └── main.ts
├── test/
└── docs/
```

[Justifique com os gaps de arquitetura identificados]

### Convenções de Nomenclatura
[Padrões concretos para o portfólio]

### Gestão de Configurações e Secrets
[Baseado no gap de Azure KeyVault — use dados reais do JSON]

---

## 🔌 INTEGRAÇÕES TO-BE

### Mapa de Integrações

| Sistema | Propósito | Protocolo | Habilita | Criticidade |
|---------|-----------|-----------|----------|-------------|
[Liste integrações reais identificadas nos blueprints/gaps + novas necessárias para o Concept]

### Padrões de Integração

[Circuit breaker, retry, cache — com exemplos TypeScript/NestJS concretos]

---

## 📊 MODELO DE DADOS TO-BE

### Entidades Core

[Defina as entidades principais com interfaces TypeScript.
Base nas entidades reais identificadas nos blueprints.]

```typescript
interface [EntidadeCore] {{
  // campos reais + novos campos habilitados pelo TO-BE
}}
```

[3-5 entidades principais]

---

[PARE AQUI.]
"""


def prompt_part5(portfolio_summary: str, gap_analysis: str, concept: str | None, data: dict) -> str:
    concept_section = f"\n### Concept NAV 360\n{concept[:5000]}" if concept else ""
    empty = set(data.get("empty_repos", []))
    top_debt = [
        e for e in data.get("top_debt_apps", [])
        if not e.get("is_empty_repo") and e["app"] not in empty
    ][:5]
    top_debt_str = "\n".join(
        f"- {e['app']}: {e['critical_gap_count']} gaps ({', '.join(e['critical_gaps'])})"
        for e in top_debt
    )

    return f"""{PREAMBLE}

# DADOS DO PORTFÓLIO
{portfolio_summary}

# TOP APPS COM MAIOR DÉBITO (para priorizar ondas)
{top_debt_str}

# GAP ANALYSIS
{gap_analysis[6000:12000]}
{concept_section}

---

# INSTRUÇÃO

Gere APENAS as seções abaixo.

---

## 🎯 CAPACIDADES HABILITADAS

### Mapa: Decisões TO-BE → Capacidades

| Capacidade | Decisões TO-BE | Status | Dependências |
|-----------|----------------|--------|--------------|
[✅ Plenamente viabilizado / ⚠️ Depende de integração externa / ❌ Requer análise]

---

## 🚀 ESTRATÉGIA DE EVOLUÇÃO

### Abordagem: Evolução Incremental

[Justifique por que não é Big Bang — baseado na realidade do portfólio]

### Ondas de Migração

```mermaid
gantt
    title Evolução AS-IS → TO-BE
    dateFormat YYYY-MM
    section Onda 1 — Fundação
    [item real] :2026-04, 2M
    section Onda 2 — Capacidades Core
    [item real] :2026-06, 2M
    section Onda 3 — Integrações
    [item real] :2026-08, 3M
    section Onda 4 — Arquitetura
    [item real] :2026-11, 4M
```

### Onda 1 — Fundação (Meses 1-3)

**Objetivo:** Quick wins — gaps críticos de baixo esforço
**Apps prioritárias:** [use top_debt_apps do JSON acima — priorize não-libs]

**Entregas:**
1. [entrega real baseada nos gaps]
2. [entrega real]
3. [entrega real]

**Critérios de sucesso:**
- [métrica concreta]

[Repita para Ondas 2, 3 e 4]

---

## 📏 MÉTRICAS DE SUCESSO

### Métricas Técnicas

| Métrica | AS-IS Estimado | TO-BE Meta | Prazo |
|---------|---------------|------------|-------|
[Use os scores reais do JSON como baseline — ex: Observabilidade 2.28/5 → meta 4.0/5]

### Métricas de Negócio

[Se Concept disponível: métricas de negócio relacionadas às capacidades habilitadas]

---

## ⚠️ RISCOS E MITIGAÇÕES

[Top 4-5 riscos reais baseados no portfólio — use dados do JSON para embasar]

### Risco [N]: [Nome]

**Probabilidade:** Alta/Média/Baixa | **Impacto:** Alto/Médio/Baixo
**Descrição:** [baseado em evidências reais]
**Mitigação:** [ação concreta]

---

## 📋 GOVERNANÇA

### Decisões Tomadas neste TO-BE

[Liste as principais decisões como checklist]

### Decisões Pendentes

[O que ainda precisa ser definido antes da implementação]

### Próximos Passos (30 dias)

1. [ação concreta]
2. [ação concreta]
3. [ação concreta]

---

## 🎯 CONCLUSÃO

[2-3 parágrafos finais conectando gaps → decisões TO-BE → valor esperado.
Use números reais do portfólio. Não invente métricas de ROI.]

---

> ⚠️ **Rastreabilidade**: Este TO-BE foi construído com base em
> `portfolio_structured.json` (parser determinístico) e no relatório de Gap Analysis.
> Todas as decisões referenciam gaps reais identificados no portfólio.

---

[PARE AQUI.]
"""


# =============================================================================
# Gerador principal
# =============================================================================

class ToBeGeneratorV4:

    def __init__(self, api_key: str = None):
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY não encontrada.")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        print("=" * 70)
        print("🎯 TO-BE GENERATOR v4")
        print("   Fonte: portfolio_structured.json + gaps*.md")
        print("=" * 70)

        # ── 1. Carrega inputs ────────────────────────────────────────────────
        print("\n📂 Carregando inputs...")

        data = load_json(JSON_PATH)
        print(f"   ✅ JSON: {data['total_apps']} apps / {data['total_projects']} projetos")

        gap_file = find_latest_gap_analysis()
        if not gap_file:
            raise FileNotFoundError(
                "Nenhum Gap_Analysis_*.md encontrado em outputs/.\n"
                "Execute gap_analyzer.py antes deste agente."
            )
        with open(gap_file, "r", encoding="utf-8") as f:
            gap_analysis = f.read()
        print(f"   ✅ Gap Analysis: {gap_file.name} ({len(gap_analysis):,} chars)")

        concept_file = find_concept_nav360()
        concept: str | None = None
        if concept_file:
            with open(concept_file, "r", encoding="utf-8") as f:
                concept = f.read()
            print(f"   ✅ Concept NAV 360: {concept_file.name} ({len(concept):,} chars)")
        else:
            print("   ⚠️  Concept NAV 360 não encontrado — continuando sem ele")

        # ── 2. Prepara contextos ─────────────────────────────────────────────
        print("\n📝 Preparando contextos...")
        portfolio_summary = extract_portfolio_summary(data)

        area_contexts = {
            area: extract_area_context(data, area)
            for area in AREA_SIGNALS
        }
        print(f"   ✅ {len(area_contexts)} contextos de área preparados")

        # ── 3. Geração em múltiplas chamadas ─────────────────────────────────
        print("\n🤖 Gerando TO-BE em partes...")
        parts: list[str] = []

        parts.append(call_model(
            self.client,
            prompt_part1(portfolio_summary, gap_analysis, concept, data),
            "Parte 1 — Sumário Executivo + Princípios + Visão Geral",
        ))

        parts.append(call_model(
            self.client,
            prompt_part2(portfolio_summary, gap_analysis, concept),
            "Parte 2 — Arquitetura de Referência + Stack",
        ))

        # Decisões técnicas por área (uma chamada por área)
        area_labels = {
            "architecture":  "Padrões Arquiteturais",
            "apis":          "APIs e Contratos",
            "observability": "Observabilidade",
            "security":      "Segurança",
            "cicd":          "CI/CD e DevOps",
            "data":          "Dados e Persistência",
        }
        for area, label in area_labels.items():
            parts.append(call_model(
                self.client,
                prompt_part3(area_contexts[area], gap_analysis, label, concept),
                f"Parte 3.x — Decisões: {label}",
            ))

        parts.append(call_model(
            self.client,
            prompt_part4(portfolio_summary, gap_analysis, concept),
            "Parte 4 — Padrões, Integrações e Modelo de Dados",
        ))

        parts.append(call_model(
            self.client,
            prompt_part5(portfolio_summary, gap_analysis, concept, data),
            "Parte 5 — Capacidades, Roadmap, Métricas e Conclusão",
        ))

        # ── 4. Consolida ─────────────────────────────────────────────────────
        print("\n📦 Consolidando documento final...")

        # Remove marcadores internos de fim de parte
        cleaned = [
            p.replace("**FIM DA PARTE", "<!-- FIM DA PARTE")
             .replace("[PARE AQUI.]", "")
             .strip()
            for p in parts
            if p.strip()
        ]

        full_doc = "\n\n---\n\n".join(cleaned)

        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        out_file = output_dir / f"TO_BE_Model_v4_{timestamp}.md"

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(full_doc)

        print(f"\n✅ TO-BE gerado!")
        print(f"📄 {out_file}")
        print(f"📊 {len(full_doc):,} chars | {len(parts)} partes")
        print(f"📏 ~{full_doc.count(chr(10) + '## ')} seções de nível 2")

        print("\n" + "=" * 70)
        print("✅ PRÓXIMOS PASSOS")
        print("=" * 70)
        print("   1. Revisar documento gerado")
        print("   2. Validar decisões técnicas com os times")
        print("   3. Executar roadmap_generator.py")
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
        ToBeGeneratorV4().generate()
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()