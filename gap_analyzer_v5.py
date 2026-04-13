"""
Gap Analyzer — v5
=================
Fonte de verdade : outputs/portfolio_structured.json  (obrigatório)
Contexto narrativo: outputs/portfolio_summary.md      (opcional)

v5 — Geração em múltiplas chamadas para evitar truncamento.
     Cada seção do relatório é gerada em uma chamada separada e
     o resultado final é concatenado em Python.

     Seções geradas:
       1. Sumário Executivo + TOP 10 Gaps
       2. Análise Detalhada por Dimensão (Obs, Seg, Cloud, APIs, Qualidade)
       3. Análise Detalhada por Dimensão (CI/CD, Arq, Docs) + Padrões
       4. Distribuição Quantitativa + Heatmap + Matriz de Priorização
       5. Débito Técnico + Recomendações + Roadmap + Conclusão
       6. ROI e Dimensionamento de Esforço (seção separada com benchmarks)

     Referências de ROI:
       - DORA State of DevOps 2022/2023
       - NIST SP 800-64 Rev.2
       - Accelerate (Forsgren, Humble, Kim — 2018)
       - CISQ Cost of Poor Software Quality (2022)
       - Verizon DBIR 2023 / GitGuardian 2023
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
MAX_TOKENS = 8000   # por chamada — confortavelmente abaixo do limite

JSON_PATH = Path("outputs/portfolio_structured.json")
MD_PATH   = Path("outputs/portfolio_summary.md")

# =============================================================================
# Benchmarks de mercado (injetados apenas na chamada de ROI)
# =============================================================================
MARKET_BENCHMARKS = """
## BENCHMARKS DE MERCADO (use SOMENTE nesta seção — cite a fonte a cada uso)

### DORA — State of DevOps (Google/DORA, 2022/2023)
- Elite: deploy múltiplas vezes/dia; MTTR < 1 hora.
- Baixa performance: deploy 1×/mês–1×/6m; MTTR > 1 semana.
- APM + structured logging: reduz MTTR ~12 min por ponto % de cobertura
  adicional (DORA 2022, correlação Tabela B-3).
- CI/CD completo: reduz lead time ~60% (DORA 2023, p. 28).
- Fonte: https://dora.dev/research/

### NIST SP 800-64 Rev.2 — Custo relativo de correção por fase
- Design: 1× | Código: 6× | Teste: 15× | Produção: 30–100×
- Vulnerabilidade crítica não detectada em dev: USD 80k–120k em produção
  (Ponemon/IBM Cost of Data Breach 2023).
- Fonte: https://csrc.nist.gov/publications/detail/sp/800-64/rev-2/final

### CISQ — Cost of Poor Software Quality (2022)
- Apps sem testes: 40–80% mais tempo em regressões manuais.
- Débito técnico médio: USD 3,61/linha de código.
- Fonte: https://www.it-cisq.org/

### Accelerate (Forsgren, Humble, Kim — 2018)
- Alta cobertura de testes: equipes entregam 440× mais frequentemente.
- Padronização de stack: reduz onboarding ~35% (cap. 4).
- Fonte: https://itrevolution.com/accelerate-book/

### Verizon DBIR 2023 / GitGuardian 2023
- 1 em cada 4 repos públicos contém credenciais expostas.
- Custo médio por credencial exposta: USD 150k–250k.
- Secrets management: reduz risco ~90%.
- Fonte: https://www.verizon.com/business/resources/reports/dbir/
         https://www.gitguardian.com/state-of-secrets-sprawl

### Referência de Esforço por Gap (Node.js/TS, 2-4 devs — média de mercado)
1 sprint = 2 semanas × 1 dev sênior. Variação esperada: ±50% por app.

| Gap                | Esforço/App  | Complexidade |
|--------------------|-------------|--------------|
| structured_logging | 0.75 sprint | Baixa        |
| health_check       | 0.50 sprint | Baixa        |
| apm                | 1.50 sprint | Média        |
| azure_keyvault     | 2.00 sprint | Média-Alta   |
| docker (retrofit)  | 1.50 sprint | Média        |
| swagger / OpenAPI  | 1.50 sprint | Média        |
| azure_devops       | 1.50 sprint | Média        |
| jest (retrofit)    | 3.50 sprint | Alta         |
| sonarqube          | 0.75 sprint | Baixa        |
| supertest          | 1.50 sprint | Média        |
| readme_documented  | 0.50 sprint | Baixa        |
| adr                | 1.00 sprint | Baixa        |

Fonte: ThoughtWorks Tech Radar, InfoQ Engineering Benchmarks 2023,
Stack Overflow Developer Survey 2023.
"""

# =============================================================================
# Regras de escopo (injetadas em todas as chamadas)
# =============================================================================
SCOPE_RULES = """
## REGRAS DE ESCOPO OBRIGATÓRIAS

1. Apps `-lib-`: `health_check`, `swagger`, `docker` são NÃO-APLICÁVEIS. Não reporte como gap.
2. Apps `-front`, `-app`, `expo`: `swagger` REST e `apm` são NÃO-APLICÁVEIS. Não reporte.
3. Repos vazios: seção separada com aviso "dados incompletos". Nunca no total de gaps.
4. GraphQL vs Swagger: apps com `graphql/graphql_federation = true` e `swagger = false`
   NÃO têm gap de documentação — usam schema GraphQL. Classifique como "padrão diferente".
5. ROI na análise principal: somente qualitativo (Alto/Médio/Baixo).
   Quantificações APENAS na seção ROI com fonte citada.
6. Rastreabilidade: toda afirmação de app específico cita o campo `evidence` do JSON.
7. Scores: use EXCLUSIVAMENTE os valores de `dimension_averages` e `signal_coverage` do JSON.
"""

# =============================================================================
# Carregamento de dados
# =============================================================================

def load_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo obrigatório não encontrado: {path}\n"
            "Execute o parser determinístico antes deste agente."
        )
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_md(path: Path) -> str | None:
    if not path.exists():
        print(f"   ⚠️  {path} não encontrado — sem contexto narrativo.")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# =============================================================================
# Pré-cálculo de esforço (Python determinístico — não vai para o LLM calcular)
# =============================================================================

GAP_EFFORT_SPRINTS: dict[str, float] = {
    "structured_logging": 0.75,
    "health_check":       0.50,
    "apm":                1.50,
    "azure_keyvault":     2.00,
    "docker":             1.50,
    "swagger":            1.50,
    "azure_devops":       1.50,
    "jest":               3.50,
    "sonarqube":          0.75,
    "supertest":          1.50,
    "readme_documented":  0.50,
    "adr":                1.00,
}

GAP_EXCLUSIONS: dict[str, set] = {
    "health_check": {"lib"},
    "swagger":      {"lib", "front", "app", "expo"},
    "docker":       {"lib"},
    "apm":          {"lib", "front", "app", "expo"},
}


def _app_categories(name: str) -> set:
    cats: set[str] = set()
    if "-lib-" in name:           cats.add("lib")
    if "-front" in name:          cats.add("front")
    if "-app" in name or name.endswith("-app"): cats.add("app")
    if "expo" in name:            cats.add("expo")
    return cats


def compute_effort(data: dict) -> tuple[str, list[dict], float]:
    """
    Calcula esforço por gap. Retorna:
      - tabela Markdown pré-calculada para injetar no prompt de ROI
      - lista de dicts com detalhes por gap
      - total de sprints-pessoa
    """
    sc          = data.get("signal_coverage", {})
    empty_repos = set(data.get("empty_repos", []))
    rows: list[dict] = []
    total = 0.0

    for gap, effort_per_app in GAP_EFFORT_SPRINTS.items():
        if gap not in sc:
            continue
        excluded = GAP_EXCLUSIONS.get(gap, set())
        affected = [
            item if isinstance(item, str) else item.get("app", "")
            for item in sc[gap].get("apps_without", [])
        ]
        affected = [
            a for a in affected
            if a and a not in empty_repos and not (_app_categories(a) & excluded)
        ]
        if not affected:
            continue

        gap_total = round(len(affected) * effort_per_app, 1)
        total += gap_total
        rows.append({
            "gap": gap,
            "n": len(affected),
            "effort_each": effort_per_app,
            "total": gap_total,
            "apps": affected,
        })

    rows.sort(key=lambda r: r["total"], reverse=True)
    total = round(total, 1)

    md  = "### Esforço por Gap — Pré-calculado (Python, determinístico)\n\n"
    md += "> 1 sprint = 2 semanas × 1 dev sênior. Variação esperada: ±50% por app.\n"
    md += "> Repos vazios e apps fora de escopo de cada gap foram excluídos.\n\n"
    md += "| Gap | Apps (escopo) | Esforço/App | Total | Apps principais |\n"
    md += "|-----|--------------|-------------|-------|-----------------|\n"
    for r in rows:
        sample = ", ".join(r["apps"][:4])
        if len(r["apps"]) > 4:
            sample += f" +{len(r['apps'])-4}"
        md += f"| {r['gap']} | {r['n']} | {r['effort_each']} spr | {r['total']} spr | {sample} |\n"

    md += f"\n**Total portfólio:** {total} sprints-pessoa  \n"
    md += f"**Time 2 devs:** ~{round(total/2,1)} sprints (~{round(total/2*2)} semanas)  \n"
    md += f"**Time 4 devs:** ~{round(total/4,1)} sprints (~{round(total/4*2)} semanas)\n"

    return md, rows, total


# =============================================================================
# Construção do contexto estruturado
# =============================================================================

def build_portfolio_context(data: dict) -> str:
    """Serializa o JSON em tabelas Markdown compactas para injetar no prompt."""

    ctx  = "# DADOS DO PORTFÓLIO (fonte: parser determinístico)\n\n"
    ctx += f"Gerado em: {data.get('generated_at','N/A')} | "
    ctx += f"Apps: {data['total_apps']} | Projetos: {data['total_projects']} | "
    ctx += f"Repos vazios: {', '.join(data.get('empty_repos',[])) or 'nenhum'}\n\n"

    # Projetos
    ctx += "## Projetos\n\n"
    for proj, apps in data.get("projects", {}).items():
        ctx += f"- **{proj}** ({len(apps)}): {', '.join(apps)}\n"
    ctx += "\n"

    # Scores consolidados
    ctx += "## Scores de Dimensão — Portfólio\n\n"
    ctx += "| Dimensão | Score /5 | Cobertura % | Cálculo |\n"
    ctx += "|----------|----------|-------------|--------|\n"
    for dim, v in data.get("dimension_averages", {}).items():
        ctx += f"| {dim.capitalize()} | {v['avg_score']:.2f} | {v['avg_coverage_pct']:.1f}% | {v['calc']} |\n"
    ctx += "\n"

    # Sinais críticos
    CRITICAL = ["health_check","structured_logging","apm","jest","docker","swagger","azure_keyvault","azure_devops"]
    sc = data.get("signal_coverage", {})

    ctx += "## Cobertura de Sinais Críticos\n\n"
    ctx += "| Sinal | ✅ | ❌ | Total | % | Apps COM |\n"
    ctx += "|-------|----|----|-------|---|----------|\n"
    for sig in CRITICAL:
        if sig not in sc: continue
        v = sc[sig]
        apps_with = ", ".join(a["app"] for a in v.get("apps_with", [])) or "—"
        ctx += f"| {v['label']} | {v['count_with']} | {v['count_without']} | {v['total']} | {v['pct_with']}% | {apps_with} |\n"
    ctx += "\n"

    # Cobertura completa
    ctx += "## Cobertura Completa de Sinais\n\n"
    ctx += "| Sinal | % Com | Apps COM | Apps SEM |\n"
    ctx += "|-------|-------|----------|----------|\n"
    for sig, v in sc.items():
        apps_with = ", ".join(a["app"] for a in v.get("apps_with", [])) or "—"
        raw_wo = v.get("apps_without", [])
        apps_wo = ", ".join((a if isinstance(a,str) else a.get("app","")) for a in raw_wo) or "—"
        ctx += f"| {v['label']} | {v['pct_with']}% | {apps_with} | {apps_wo} |\n"
    ctx += "\n"

    # Top débito
    ctx += "## Top Apps — Maior Débito Técnico\n\n"
    ctx += "| App | Projeto | Nº Gaps | Gaps | Repo Vazio? |\n"
    ctx += "|-----|---------|---------|------|-------------|\n"
    for e in data.get("top_debt_apps", []):
        ctx += f"| {e['app']} | {e['project']} | {e['critical_gap_count']} | {', '.join(e['critical_gaps'])} | {'Sim ⚠️' if e['is_empty_repo'] else 'Não'} |\n"
    ctx += "\n"

    # Detalhe por app
    ctx += "## Detalhe por App\n\n"
    for app in data.get("apps", []):
        name    = app["app"]
        proj    = app["project"]
        ds      = app.get("dimension_scores", {})
        cg      = app.get("critical_gaps", [])
        empty   = app.get("is_empty_repo", False)
        scanner = app.get("scanner", {})

        ctx += f"### {name} ({proj}){' ⚠️ REPO VAZIO' if empty else ''}\n"
        ctx += f"Sizing: {scanner.get('size_kb','?')} KB | {scanner.get('total_files','?')} arquivos | "
        ctx += f"{', '.join(scanner.get('frameworks',[])) or '—'} | {', '.join(scanner.get('project_types',[])) or '—'}\n"

        scores = " | ".join(f"{d.capitalize()}: {v['score']:.2f}/5 [{v['calc']}]" for d,v in ds.items())
        ctx += f"Scores: {scores}\n"

        found = {s:sv for s,sv in app.get("signals",{}).items() if sv.get("found")}
        if found:
            ctx += "Sinais: " + " | ".join(f"`{s}` ({sv['evidence'][:60]})" for s,sv in found.items()) + "\n"

        if cg:
            ctx += f"Gaps críticos: {', '.join(cg)}\n"
        ctx += "\n"

    return ctx


# =============================================================================
# Chamada ao modelo com retry simples
# =============================================================================

def call_model(client: anthropic.Anthropic, prompt: str, label: str) -> str:
    """Faz uma chamada ao modelo com retry em caso de erro transitório."""
    for attempt in range(1, 4):
        try:
            print(f"      → {label} (tentativa {attempt})...")
            resp = client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            text = resp.content[0].text
            print(f"         ✅ {len(text):,} chars gerados")
            return text
        except Exception as e:
            print(f"         ⚠️  Erro: {e}")
            if attempt < 3:
                time.sleep(5 * attempt)
            else:
                raise
    return ""  # nunca alcançado


# =============================================================================
# Prompts por seção
# =============================================================================

SYSTEM_PREAMBLE = lambda ctx, scope: f"""Você é um Arquiteto de Soluções Sênior especializado em Modernização de Portfólios.

Esta análise será apresentada a stakeholders executivos.
- Todos os números vêm do JSON de entrada — nunca recalcule.
- Toda afirmação de app cita o campo `evidence` do JSON.
- Sem estimativas financeiras em R$ ou USD fora da seção ROI.

{scope}

---

{ctx}

---
"""


def prompt_section_1(ctx: str, data: dict, md: str | None) -> str:
    """Sumário executivo + TOP 10 gaps."""
    md_hint = f"\nContexto narrativo adicional (use para enriquecer linguagem, NÃO seus números):\n{md[:4000]}\n" if md else ""
    return SYSTEM_PREAMBLE(ctx, SCOPE_RULES) + f"""
{md_hint}

# INSTRUÇÃO

Ao descrever arquitetura no sumário executivo, distingua:
- Padrões de integração/comunicação (GraphQL Federation, BFF, REST):
  reflita o que está em `signal_coverage` — GraphQL Federation, graphql, swagger.
- Padrões de organização interna (Clean Architecture, DDD, Event Driven):
  reflita o score de `dimension_averages.architecture` (1.00/5).
Nunca use evidência do primeiro plano para qualificar o segundo como "moderno" ou "maduro".

Gere APENAS as seções abaixo. Não gere nada além delas.

---

# ANÁLISE DE GAPS — AS-IS vs BOAS PRÁTICAS

**Data:** {datetime.now().strftime("%d/%m/%Y")}
**Portfólio:** {data['total_apps']} aplicações | {data['total_projects']} projetos
**Fonte:** parser determinístico — portfolio_structured.json

---

## SUMÁRIO EXECUTIVO

### Visão Geral do Portfólio

[3-4 parágrafos. Cite % reais do JSON.
Cubra: perfil técnico predominante, consistência, principais gaps, oportunidades.]

### Métricas de Maturidade

[Use EXCLUSIVAMENTE os valores de `dimension_averages` do JSON:]

| Dimensão | Score /5 | Cobertura % | Sinais da Dimensão | Gaps Críticos |
|----------|----------|-------------|-------------------|---------------|
[preencha com avg_score, avg_coverage_pct, lista de sinais, sinais ausentes — tudo do JSON]

> Nota metodológica: Score = (média de % de cobertura dos sinais) / 100 × 5.
> Cálculos completos no campo `calc` de cada dimensão.

---

## TOP 10 GAPS PRIORITÁRIOS

| # | Gap | Apps Afetadas | Severidade | Categoria | Impacto |
|---|-----|---------------|------------|-----------|---------|
[10 gaps mais críticos. Contagens EXATAS do signal_coverage.
🔴 Crítica / 🟠 Alta / 🟡 Média / 🟢 Baixa. Impacto: qualitativo.]

---

[PARE AQUI. Não gere mais nenhuma seção.]
"""


def prompt_section_2(ctx: str) -> str:
    """Análise detalhada — dimensões 1 a 5."""
    return SYSTEM_PREAMBLE(ctx, SCOPE_RULES) + """
# INSTRUÇÃO

Gere APENAS a seção abaixo. Não gere sumário, não gere outras seções.

---

## ANÁLISE DETALHADA POR DIMENSÃO (Parte 1 de 2)

Para cada dimensão, use EXATAMENTE esta estrutura:

### [N]️⃣ [Nome]

**Score atual:** [avg_score do JSON] /5 | **Cobertura:** [%] | **Cálculo:** [campo calc]

#### Gap [N.M]: [Nome descritivo]

**Evidências AS-IS:**
- Apps COM o sinal ([contagem exata]): [lista do apps_with]
- Apps SEM o sinal ([contagem exata]): [lista do apps_without]
- Exceções de escopo: [libs/fronts/repos vazios excluídos, se houver]

** Boa Prática de Mercado:** [padrão moderno e por que importa]

** Gap:** [diferença atual vs desejado | Impacto: Alto/Médio/Baixo]

** Severidade:** [Crítica/Alta/Média/Baixa] | **⏱️ Esforço:** [S/M/L/XL por app]

**💡 Oportunidade:** [benefício acionável]

---

Gere as dimensões:

### 1. Observabilidade
### 2. Segurança e Gestão de Secrets
### 3. Cloud-Native e Containerização
### 4. APIs e Contratos de Interface
### 5. Qualidade e Testes Automatizados

[PARE AQUI. Não gere mais nenhuma seção.]
"""


def prompt_section_3(ctx: str) -> str:
    """Análise detalhada — dimensões 6 a 8 + Padrões."""
    return SYSTEM_PREAMBLE(ctx, SCOPE_RULES) + """
# INSTRUÇÃO

Gere APENAS as seções abaixo. Use a mesma estrutura de gap da parte anterior.

---

## ANÁLISE DETALHADA POR DIMENSÃO (Parte 2 de 2)

### 6. CI/CD e DevOps
### 7. Arquitetura e Design
### 8. Documentação

---

## PADRÕES DO PORTFÓLIO

### ✅ Padrões Positivos Identificados

[Para cada padrão bom encontrado — apps reais + evidência do JSON.
Inclua: onde foi encontrado, impacto observado, recomendação de expansão.]

### ❌ Anti-Patterns Identificados

[Para cada anti-pattern — apps reais + evidência do JSON.
Inclua: onde, risco concreto, prioridade de correção.]

### ⚠️ Inconsistências Críticas

[Áreas sem padronização. Contagens reais do JSON. Impacto operacional.]

---

[PARE AQUI.]
"""


def prompt_section_4(ctx: str) -> str:
    """Distribuição quantitativa + Heatmap + Repos vazios + Matriz de priorização."""
    return SYSTEM_PREAMBLE(ctx, SCOPE_RULES) + """
# INSTRUÇÃO

Gere APENAS as seções abaixo.

---

## DISTRIBUIÇÃO QUANTITATIVA

### Por Severidade

| Severidade | Nº Gaps | Apps Mais Afetadas |
|------------|---------|-------------------|
| 🔴 Crítica | [N] | [lista] |
| 🟠 Alta    | [N] | [lista] |
| 🟡 Média   | [N] | [lista] |
| 🟢 Baixa   | [N] | [lista] |

### Heatmap de Gaps por App

Somente apps que NÃO são repos vazios.
🔴 score < 2.5 | 🟡 2.5–3.5 | 🟢 > 3.5

| App | Obs | Seg | DevOps | Qualidade | Arq | Doc | Score Médio |
|-----|-----|-----|--------|-----------|-----|-----|-------------|
[Use os dimension_scores de cada app. Score médio = média das 6 dimensões.]

---

## ⚠️ REPOS VAZIOS

Dados incompletos — gaps podem estar sub-reportados. **Validação manual necessária.**

| Repo | Projeto | Observação |
|------|---------|-----------|
[Lista de empty_repos do JSON]

---

## MATRIZ DE PRIORIZAÇÃO

### Quick Wins — Alto Impacto, Baixo Esforço (S/M)
[Gaps com muitos apps afetados e esforço S ou M. Liste com contagens reais.]

### Grandes Apostas — Alto Impacto, Alto Esforço (L/XL)
[Gaps estratégicos com esforço L ou XL.]

### Fill-ins — Baixo Impacto, Baixo Esforço
[Melhorias menores quando houver capacidade.]

---

[PARE AQUI.]
"""


def prompt_section_5(ctx: str, data: dict) -> str:
    """Top apps por débito + Recomendações + Roadmap + Conclusão."""
    return SYSTEM_PREAMBLE(ctx, SCOPE_RULES) + f"""
# INSTRUÇÃO

Gere APENAS as seções abaixo.

---

## TOP APPS COM MAIOR DÉBITO TÉCNICO

Use EXCLUSIVAMENTE `top_debt_apps` do JSON. Repos vazios em nota separada.

| # | App | Projeto | Nº Gaps | Gaps | Ação Recomendada |
|---|-----|---------|---------|------|-----------------|
[Dados exatos do JSON. Ação qualitativa e específica.]

> Repos vazios excluídos do ranking: [{', '.join(data.get('empty_repos', []))}]
> Dados incompletos — validação manual necessária.

---

## RECOMENDAÇÕES ESTRATÉGICAS

Para cada recomendação (5-7 no total), use:

### Recomendação [N]: [Título acionável]

**Resolve:** [gaps + nº de apps afetadas]
**Apps prioritárias:** [lista do JSON — maior debt]

**Ações:**
1. [Passo concreto]
2. [Passo concreto]

**Benefícios:** Técnico: [qualit.] | Operacional: [qualit.]
**Esforço:** [S/M/L/XL] | **Prazo:** Curto (0-3m) / Médio (3-6m) / Longo (6-12m)

---

## ROADMAP MACRO SUGERIDO

```mermaid
gantt
    title Roadmap de Resolução de Gaps (Macro)
    dateFormat YYYY-MM
    section Fase 1 — Quick Wins
    Structured Logging + Health Check  :2026-04, 1M
    SonarQube                          :2026-04, 1M
    section Fase 2 — Fundação
    APM (Dynatrace/OTEL)               :2026-05, 2M
    Azure Key Vault                    :2026-06, 2M
    Docker retrofit                    :2026-06, 3M
    section Fase 3 — Qualidade
    Testes automatizados (Jest)        :2026-09, 4M
    section Fase 4 — Arquitetura
    Documentação e contratos           :2026-11, 3M
```

Ajuste datas e itens com base nos gaps reais identificados.

---

## CONCLUSÃO

### Principais Descobertas

[5 descobertas com dados concretos — números reais do JSON]

### Score Consolidado do Portfólio

**Média geral:** [some os avg_score e divida pelo nº de dimensões — mostre o cálculo]

| Dimensão | Score /5 | Equivalente DORA |
|----------|----------|-----------------|
[Tabela com scores do JSON + benchmark qualitativo: Elite/Alto/Médio/Baixo]

### Direcionamento para o TO-BE

[2-3 parágrafos sobre o que o TO-BE deve endereçar,
baseado nos gaps de maior severidade.]

---

> ⚠️ **Rastreabilidade**: Scores e percentuais extraídos de `portfolio_structured.json`
> gerado em {data.get('generated_at','N/A')}.
> Gaps identificados com base exclusivamente nos dados de entrada.

---

[PARE AQUI.]
"""


def prompt_section_roi(ctx_minimal: str, effort_table: str, effort_rows: list, total_sprints: float, data: dict) -> str:
    """Seção de ROI — chamada separada, usa benchmarks de mercado."""

    effort_by_gap = "\n".join(
        f"- **{r['gap']}**: {r['n']} apps × {r['effort_each']} spr = **{r['total']} spr** "
        f"| apps: {', '.join(r['apps'][:3])}" + (f" +{len(r['apps'])-3} mais" if len(r['apps']) > 3 else "")
        for r in effort_rows
    )

    # App-level effort: soma dos gaps críticos de cada app
    top_debt = [e for e in data.get("top_debt_apps", []) if not e.get("is_empty_repo")]

    app_effort_lines = []
    for entry in top_debt[:10]:
        app_sprints = sum(GAP_EFFORT_SPRINTS.get(g, 0) for g in entry["critical_gaps"])
        calc = " + ".join(
            f"{g}({GAP_EFFORT_SPRINTS.get(g,0)})" for g in entry["critical_gaps"]
        )
        app_effort_lines.append(
            f"- **{entry['app']}**: {calc} = **{round(app_sprints,2)} sprints**"
        )
    app_effort_str = "\n".join(app_effort_lines)

    # Totais por onda (determinístico)
    onda1_gaps = ["structured_logging", "health_check", "sonarqube"]
    onda2_gaps = ["azure_keyvault", "apm"]
    onda3_gaps = ["jest", "supertest", "docker", "azure_devops"]

    def onda_total(gaps: list[str]) -> float:
        return round(sum(r["total"] for r in effort_rows if r["gap"] in gaps), 1)

    o1 = onda_total(onda1_gaps)
    o2 = onda_total(onda2_gaps)
    o3 = onda_total(onda3_gaps)

    return f"""Você é um Arquiteto de Soluções Sênior.
Esta é a seção de ROI e Dimensionamento de Esforço do relatório de gap analysis.
É uma seção SEPARADA das análises de gaps — tem metodologia própria e aviso explícito.

{MARKET_BENCHMARKS}

---

Os dados de esforço abaixo foram calculados DETERMINISTICAMENTE em Python.
NÃO recalcule. Use os valores como estão.

{effort_table}

**Por app (gaps críticos somados):**
{app_effort_str}

**Totais por onda:**
- Onda 1 (structured_logging, health_check, sonarqube): {o1} sprints-pessoa
- Onda 2 (azure_keyvault, apm): {o2} sprints-pessoa
- Onda 3 (jest, supertest, docker, azure_devops): {o3} sprints-pessoa
- **Total geral:** {total_sprints} sprints-pessoa

---

Contexto mínimo do portfólio:
{ctx_minimal}

---

# INSTRUÇÃO

Gere APENAS a seção abaixo, completa. Não gere outras seções.

---

## ROI E DIMENSIONAMENTO DE ESFORÇO

> ⚠️ **Nota Metodológica**
>
> As estimativas apresentadas nesta análise foram elaboradas a partir de **benchmarks de mercado, boas práticas de engenharia de software e referências públicas de produtividade em iniciativas de modernização tecnológica**.
>
> Os valores indicados representam **ordens de grandeza destinadas a apoiar a priorização e o planejamento das iniciativas**, não devendo ser interpretados como estimativas orçamentárias definitivas.
>
> O esforço foi estimado em **sprints-pessoa**, uma vez que custos financeiros variam conforme o modelo de equipe, estrutura organizacional e contexto de execução.
>
> Como em qualquer processo de estimativa inicial, **variações são esperadas**, especialmente em função da complexidade das aplicações, qualidade do código existente, dependências externas e maturidade das práticas de engenharia.

---

### Fontes de Referência

| Fonte | Uso nesta seção | URL |
|-------|----------------|-----|
| DORA State of DevOps 2023 | MTTR, lead time, frequência de deploy | https://dora.dev/research/ |
| NIST SP 800-64 Rev.2 | Custo relativo de correção por fase | https://csrc.nist.gov/publications/detail/sp/800-64/rev-2/final |
| CISQ Cost of Poor Software Quality 2022 | Débito técnico, custo de regressão | https://www.it-cisq.org/ |
| Accelerate (Forsgren et al., 2018) | Frequência de entrega, onboarding | https://itrevolution.com/accelerate-book/ |
| Verizon DBIR 2023 | Custo médio por credencial exposta | https://www.verizon.com/business/resources/reports/dbir/ |
| GitGuardian 2023 | Prevalência de credenciais em repos | https://www.gitguardian.com/state-of-secrets-sprawl |

---

### Esforço por Gap (pré-calculado)

[Apresente os dados da tabela pré-calculada acima. NÃO modifique os números.
Adicione apenas uma linha de contexto qualitativo por gap se relevante.]

**Total portfólio:** {total_sprints} sprints-pessoa
**Time 2 devs sênior:** ~{round(total_sprints/2,1)} sprints (~{round(total_sprints/2*2)} semanas)
**Time 4 devs sênior:** ~{round(total_sprints/4,1)} sprints (~{round(total_sprints/4*2)} semanas)

---

### Top 10 Apps por Esforço Total Estimado

[Apresente os dados de app_effort calculados acima. NÃO modifique os valores.
Adicione contexto: se o app é crítico para o negócio, se já tem parte do stack, etc.]

---

### Impacto por Dimensão (baseado em benchmarks)

Para cada dimensão abaixo, aplique os benchmarks fornecidos e descreva
o impacto esperado APÓS resolução. **Cite a fonte a cada afirmação.**

#### Observabilidade (APM + Structured Logging + Health Check)
[Aplique DORA 2022/2023: MTTR, frequência de deploy. Cite Tabela B-3 se usar o dado de ~12 min.]

#### Segurança (Azure Key Vault)
[Aplique NIST SP 800-64 fator 30–100×. Aplique Verizon DBIR e GitGuardian para secrets.]

#### Qualidade e Testes (Jest + Supertest + SonarQube)
[Aplique CISQ 40–80% de regressões. Aplique Accelerate 440×.]

#### CI/CD e DevOps (Azure DevOps + Docker)
[Aplique DORA 2023: ~60% de redução em lead time.]

---

### ROI por Ondas de Investimento

#### Onda 1 — Quick Wins (Meses 1-3)
**Gaps:** structured_logging, health_check, sonarqube
**Esforço total:** {o1} sprints-pessoa (calculado acima — NÃO modifique)
**Impacto esperado:**
- [DORA: redução de MTTR com structured logging + health check — cite fonte]
- [CISQ: redução de regressões com SonarQube — cite fonte]

#### Onda 2 — Fundação de Segurança (Meses 3-6)
**Gaps:** azure_keyvault, apm
**Esforço total:** {o2} sprints-pessoa (calculado acima — NÃO modifique)
**Impacto esperado:**
- [NIST: custo de correção em produção vs design — cite fator 30-100× — cite fonte]
- [GitGuardian/Verizon: risco de credenciais expostas — cite fonte]
- [DORA: melhoria de MTTR com APM — cite fonte]

#### Onda 3 — Qualidade Estrutural (Meses 6-12)
**Gaps:** jest, supertest, docker, azure_devops
**Esforço total:** {o3} sprints-pessoa (calculado acima — NÃO modifique)
**Impacto esperado:**
- [Accelerate: frequência de entrega — cite 440× — cite fonte]
- [CISQ: redução de débito técnico — cite fonte]
- [DORA: lead time com CI/CD — cite ~60% — cite fonte]

---

[PARE AQUI.]
"""


# =============================================================================
# Normalização de dados
# =============================================================================

def normalize_data(raw: dict) -> dict:
    sc = raw.get("signal_coverage", {})

    # Normaliza apps_without para lista de str
    for v in sc.values():
        v["apps_without"] = [
            (a if isinstance(a, str) else a.get("app", ""))
            for a in v.get("apps_without", [])
            if a
        ]

    # Mapa projeto e empty_repos
    project_map: dict[str,str] = {
        app: proj
        for proj, apps in raw.get("projects", {}).items()
        for app in apps
    }
    empty_repos = set(raw.get("empty_repos", []))

    # Scanner por app
    scanner_map: dict[str,dict] = {
        e.get("app_name",""): e.get("scanner", {})
        for e in raw.get("apps", [])
        if e.get("app_name")
    }

    # Reconstrói apps[]
    DIM_SIGNALS = {
        "observability": ["apm","health_check","structured_logging"],
        "quality":       ["jest","playwright","supertest","sonarqube"],
        "security":      ["azure_keyvault","keycloak","jwt","passport"],
        "devops":        ["azure_devops","github_actions","docker","kubernetes"],
        "architecture":  ["clean_architecture","ddd","event_driven","graphql_federation","swagger"],
        "documentation": ["swagger","readme_documented"],
    }

    apps_index: dict[str,dict] = {
        app: {
            "app": app, "project": proj,
            "is_empty_repo": app in empty_repos,
            "signals": {}, "critical_gaps": [],
            "scanner": scanner_map.get(app, {}),
            "dimension_scores": {},
        }
        for app, proj in project_map.items()
    }

    for sig, v in sc.items():
        for entry in v.get("apps_with", []):
            a = entry["app"]
            if a in apps_index:
                apps_index[a]["signals"][sig] = {"found": True, "source": entry.get("source",""), "evidence": entry.get("evidence","")}
        for a in v.get("apps_without", []):
            if a in apps_index:
                apps_index[a]["signals"][sig] = {"found": False, "source": "", "evidence": ""}

    for ad in apps_index.values():
        for dim, sigs in DIM_SIGNALS.items():
            found = [s for s in sigs if ad["signals"].get(s, {}).get("found")]
            total = len(sigs)
            score = round((len(found)/total)*5, 2) if total else 0.0
            ad["dimension_scores"][dim] = {
                "score": score, "found": len(found), "total": total,
                "signals_found": found,
                "signals_missing": [s for s in sigs if s not in found],
                "calc": f"{len(found)}/{total} × 5 = {score}",
            }

    for e in raw.get("top_debt_apps", []):
        if e["app"] in apps_index:
            apps_index[e["app"]]["critical_gaps"] = e["critical_gaps"]

    raw["apps"] = list(apps_index.values())
    return raw


# =============================================================================
# Contexto mínimo para seção ROI (sem detalhe por app)
# =============================================================================

def build_minimal_context(data: dict) -> str:
    ctx  = f"Portfólio: {data['total_apps']} apps | {data['total_projects']} projetos\n"
    ctx += f"Repos vazios: {', '.join(data.get('empty_repos',[]))}\n\n"
    ctx += "Scores consolidados:\n"
    for dim, v in data.get("dimension_averages", {}).items():
        ctx += f"  {dim}: {v['avg_score']:.2f}/5 ({v['avg_coverage_pct']:.1f}%)\n"
    return ctx


# =============================================================================
# Agente principal
# =============================================================================

class GapAnalyzerV5:

    def __init__(self, api_key: str = None):
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY não encontrada.")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def run(self):
        print("=" * 70)
        print("🔍 GAP ANALYZER v5 — geração em múltiplas chamadas")
        print("   Fonte  : portfolio_structured.json")
        print("   ROI    : DORA / NIST SP 800-64 / Accelerate / CISQ")
        print("=" * 70)

        # ── 1. Carrega ──────────────────────────────────────────────────────
        print("\n📂 Carregando dados...")
        raw = load_json(JSON_PATH)
        md  = load_md(MD_PATH)
        print(f"   ✅ JSON: {raw['total_apps']} apps / {raw['total_projects']} projetos")
        if md:
            print(f"   ✅ MD: {len(md):,} chars")

        # ── 2. Normaliza ────────────────────────────────────────────────────
        print("\n🔧 Normalizando...")
        data = normalize_data(raw)
        print(f"   ✅ {len(data['apps'])} apps | {len(data.get('empty_repos',[]))} repos vazios")

        # ── 3. Pré-calcula esforço ──────────────────────────────────────────
        print("\n📐 Calculando esforço...")
        effort_table, effort_rows, total_sprints = compute_effort(data)
        print(f"   ✅ {len(effort_rows)} gaps | {total_sprints} sprints-pessoa total")

        # ── 4. Contextos ────────────────────────────────────────────────────
        portfolio_ctx = build_portfolio_context(data)
        minimal_ctx   = build_minimal_context(data)
        print(f"\n📝 Contexto principal: {len(portfolio_ctx):,} chars")

        # ── 5. Geração em múltiplas chamadas ────────────────────────────────
        print("\n🤖 Gerando relatório em 6 chamadas...")

        sections: list[str] = []

        sections.append(call_model(
            self.client,
            prompt_section_1(portfolio_ctx, data, md),
            "Seção 1 — Sumário Executivo + TOP 10",
        ))

        sections.append(call_model(
            self.client,
            prompt_section_2(portfolio_ctx),
            "Seção 2 — Dimensões 1-5 (Obs, Seg, Cloud, APIs, Qualidade)",
        ))

        sections.append(call_model(
            self.client,
            prompt_section_3(portfolio_ctx),
            "Seção 3 — Dimensões 6-8 (CI/CD, Arq, Docs) + Padrões",
        ))

        sections.append(call_model(
            self.client,
            prompt_section_4(portfolio_ctx),
            "Seção 4 — Distribuição + Heatmap + Repos vazios + Matriz",
        ))

        sections.append(call_model(
            self.client,
            prompt_section_5(portfolio_ctx, data),
            "Seção 5 — Débito + Recomendações + Roadmap + Conclusão",
        ))

        sections.append(call_model(
            self.client,
            prompt_section_roi(minimal_ctx, effort_table, effort_rows, total_sprints, data),
            "Seção 6 — ROI e Dimensionamento de Esforço",
        ))

        # ── 6. Concatena e salva ────────────────────────────────────────────
        full_report = "\n\n---\n\n".join(s.strip() for s in sections if s.strip())

        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_file   = output_dir / f"Gap_Analysis_{timestamp}.md"

        with open(out_file, "w", encoding="utf-8") as f:
            f.write(full_report)

        total_chars = len(full_report)
        print(f"\n✅ Relatório completo salvo!")
        print(f"📄 {out_file}")
        print(f"📊 {total_chars:,} chars | {len(sections)} seções")

        print("\n" + "=" * 70)
        print("✅ PRÓXIMOS PASSOS")
        print("=" * 70)
        print("   1. Revisar relatório gerado")
        print("   2. Calibrar esforços da seção ROI com o time")
        print("   3. Validar gaps com stakeholders")
        print("   4. Executar to_be_generator.py")
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
        GapAnalyzerV5().run()
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()