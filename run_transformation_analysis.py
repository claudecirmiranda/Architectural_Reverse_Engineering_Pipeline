"""
Orquestrador de Transformação Arquitetural Completa

Pipeline completo em ordem correta:

  1. Blueprints AS-IS      → blueprint_generator_ai.py
  2. Extração de portfólio → blueprint_extractor.py    (gera portfolio_structured.json)
  3. Análise de Gaps       → gap_analyzer_v5.py         (requer portfolio_structured.json)
  4. Modelo TO-BE          → tobe_generator_v5.py       (requer Gap_Analysis_*.md)
  5. Roadmap de Adoção     → roadmap_generator.py       (requer TO_BE_Model_*.md + Gap_Analysis_*.md)

Uso: python run_transformation_analysis.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


def print_banner(text: str, char: str = "="):
    """Imprime banner formatado."""
    width = 80
    print(f"\n{char * width}")
    print(f"{text.center(width)}")
    print(f"{char * width}\n")


def check_prerequisites():
    """Verifica pré-requisitos."""
    print_banner("VERIFICANDO PRÉ-REQUISITOS", "=")

    issues = []

    # 1. API Key
    if not os.getenv("ANTHROPIC_API_KEY"):
        issues.append("❌ ANTHROPIC_API_KEY não configurada")
    else:
        print("✅ API Key configurada")

    # 2. Biblioteca anthropic
    try:
        import anthropic
        print("✅ Biblioteca anthropic instalada")
    except ImportError:
        issues.append("❌ Biblioteca anthropic não instalada (pip install anthropic)")

    # 3. Diretório outputs
    if not Path("outputs").exists():
        issues.append("❌ Diretório 'outputs' não encontrado")
    else:
        print("✅ Diretório outputs encontrado")

    # 4. Blueprints AS-IS
    blueprints_found = any(
        list((d / "blueprints").glob("*_blueprint.md"))
        for d in Path("outputs").iterdir()
        if d.is_dir() and d.name != "json" and (d / "blueprints").exists()
    )
    if blueprints_found:
        print("✅ Blueprints AS-IS encontrados")
    else:
        print("⚠️  Nenhum blueprint AS-IS encontrado — será gerado na Etapa 1")

    if issues:
        print("\n" + "=" * 80)
        print("PROBLEMAS ENCONTRADOS:")
        for issue in issues:
            print(f"  {issue}")
        print("=" * 80)
        return False

    print("\n✅ Todos os pré-requisitos atendidos!")
    return True


# =============================================================================
# ETAPA 1 — Blueprints AS-IS
# =============================================================================

def run_blueprint_generation():
    """Gera blueprints AS-IS por aplicação."""
    print_banner("ETAPA 1: BLUEPRINTS AS-IS", "🔷")

    blueprints_found = any(
        list((d / "blueprints").glob("*_blueprint.md"))
        for d in Path("outputs").iterdir()
        if d.is_dir() and d.name != "json" and (d / "blueprints").exists()
    )

    if blueprints_found:
        print("✅ Blueprints AS-IS já existem.")
        if input("\n🔄 Deseja regenerar blueprints? (s/N): ").strip().lower() != "s":
            return True

    print("📝 Executando blueprint_generator_ai.py...")
    try:
        from blueprint_generator_ai import BlueprintGenerator
        BlueprintGenerator().process_all_repositories()
        return True
    except Exception as e:
        print(f"❌ Erro ao gerar blueprints: {e}")
        return False


# =============================================================================
# ETAPA 2 — Extração de portfólio (portfolio_structured.json)
# =============================================================================

def run_blueprint_extraction():
    """Extrai dados estruturados dos blueprints para portfolio_structured.json."""
    print_banner("ETAPA 2: EXTRAÇÃO DE PORTFÓLIO", "🔷")

    portfolio_file = Path("outputs/portfolio_structured.json")

    if portfolio_file.exists():
        print(f"✅ portfolio_structured.json já existe ({portfolio_file.stat().st_size:,} bytes).")
        if input("\n🔄 Deseja re-extrair? (s/N): ").strip().lower() != "s":
            return True

    print("📝 Executando blueprint_extractor.py...")
    try:
        from blueprint_extractor import main as extractor_main
        extractor_main()
        if not portfolio_file.exists():
            print("❌ portfolio_structured.json não foi gerado.")
            return False
        return True
    except Exception as e:
        print(f"❌ Erro na extração do portfólio: {e}")
        return False


# =============================================================================
# ETAPA 3 — Análise de Gaps (gap_analyzer_v5)
# =============================================================================

def run_gap_analysis():
    """Executa análise de gaps (v5)."""
    print_banner("ETAPA 3: ANÁLISE DE GAPS", "🔷")

    # Dependência obrigatória
    if not Path("outputs/portfolio_structured.json").exists():
        print("❌ portfolio_structured.json não encontrado.")
        print("   Execute a Etapa 2 (blueprint_extractor) primeiro.")
        return False

    gap_files = list(Path("outputs").glob("Gap_Analysis_*.md"))
    if gap_files:
        latest = max(gap_files, key=lambda p: p.stat().st_mtime)
        print(f"✅ Análise de Gaps já existe: {latest.name}")
        if input("\n🔄 Deseja regenerar análise de gaps? (s/N): ").strip().lower() != "s":
            return True

    print("📝 Executando gap_analyzer_v5.py...")
    try:
        from gap_analyzer_v5 import GapAnalyzerV5
        GapAnalyzerV5().run()
        return True
    except Exception as e:
        print(f"❌ Erro na análise de gaps: {e}")
        return False


# =============================================================================
# ETAPA 4 — Modelo TO-BE (tobe_generator_v5 = ToBeGeneratorV4)
# =============================================================================

def run_to_be_generation():
    """Gera modelo TO-BE (v4) a partir do portfólio e da análise de gaps."""
    print_banner("ETAPA 4: MODELO TO-BE", "🔷")

    # Dependência obrigatória
    if not list(Path("outputs").glob("Gap_Analysis_*.md")):
        print("❌ Nenhum Gap_Analysis_*.md encontrado.")
        print("   Execute a Etapa 3 (gap_analyzer_v5) primeiro.")
        return False

    to_be_files = list(Path("outputs").glob("TO_BE_Model_*.md"))
    if to_be_files:
        latest = max(to_be_files, key=lambda p: p.stat().st_mtime)
        print(f"✅ Modelo TO-BE já existe: {latest.name}")
        if input("\n🔄 Deseja regenerar modelo TO-BE? (s/N): ").strip().lower() != "s":
            return True

    print("📝 Executando tobe_generator_v5.py...")
    try:
        from tobe_generator_v5 import ToBeGeneratorV4
        ToBeGeneratorV4().generate()
        return True
    except Exception as e:
        print(f"❌ Erro ao gerar TO-BE: {e}")
        return False


# =============================================================================
# ETAPA 5 — Roadmap de Adoção
# =============================================================================

def run_roadmap_generation():
    """Gera roadmap de adoção."""
    print_banner("ETAPA 5: ROADMAP DE ADOÇÃO", "🔷")

    roadmap_files = list(Path("outputs").glob("Adoption_Roadmap_*.md"))
    if roadmap_files:
        latest = max(roadmap_files, key=lambda p: p.stat().st_mtime)
        print(f"✅ Roadmap já existe: {latest.name}")
        if input("\n🔄 Deseja regenerar roadmap? (s/N): ").strip().lower() != "s":
            return True

    print("📝 Executando roadmap_generator.py...")
    try:
        from roadmap_generator import RoadmapGenerator
        RoadmapGenerator().generate()
        return True
    except Exception as e:
        print(f"❌ Erro ao gerar roadmap: {e}")
        return False


# =============================================================================
# Índice final
# =============================================================================

def generate_index():
    """Gera índice com todos os documentos gerados."""
    print_banner("GERANDO ÍNDICE", "📚")

    index_content = f"""# Índice de Documentação de Transformação Arquitetural

Gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M:%S")}

---

## 📋 Visão Geral

Este índice consolida toda a documentação gerada pelo processo de análise e planejamento da transformação arquitetural.

---

## 📂 Estrutura da Documentação

### 1️⃣ Blueprints AS-IS (Estado Atual)

Análise detalhada de cada aplicação existente:

"""

    for project_dir in sorted(Path("outputs").iterdir()):
        if not project_dir.is_dir() or project_dir.name == "json":
            continue
        blueprints_dir = project_dir / "blueprints"
        if not blueprints_dir.exists():
            continue
        blueprints = list(blueprints_dir.glob("*_blueprint.md"))
        if blueprints:
            index_content += f"\n#### Projeto: {project_dir.name}\n\n"
            for bp in sorted(blueprints):
                app_name = bp.stem.replace("_blueprint", "")
                index_content += f"- [{app_name}](./{project_dir.name}/blueprints/{bp.name})\n"

    # Portfólio estruturado
    portfolio_file = Path("outputs/portfolio_structured.json")
    if portfolio_file.exists():
        index_content += f"""

### 2️⃣ Dados Estruturados do Portfólio

- [📦 portfolio_structured.json](./portfolio_structured.json) — base factual para gap analysis e TO-BE
- [📋 portfolio_summary.md](./portfolio_summary.md) — tabela auditável para revisão humana

"""

    # Gap Analysis
    gap_files = sorted(Path("outputs").glob("Gap_Analysis_*.md"), key=lambda p: p.stat().st_mtime)
    if gap_files:
        latest_gap = gap_files[-1]
        index_content += f"""
### 3️⃣ Análise de Gaps

Identificação de lacunas entre AS-IS e boas práticas de mercado:

- [📊 Análise de Gaps](./{latest_gap.name})

"""

    # TO-BE
    to_be_files = sorted(Path("outputs").glob("TO_BE_Model_*.md"), key=lambda p: p.stat().st_mtime)
    if to_be_files:
        latest_to_be = to_be_files[-1]
        index_content += f"""
### 4️⃣ Modelo TO-BE (Estado Futuro)

Visão do estado futuro desejado da arquitetura:

- [📘 Modelo TO-BE](./{latest_to_be.name})

"""

    # Roadmap
    roadmap_files = sorted(Path("outputs").glob("Adoption_Roadmap_*.md"), key=lambda p: p.stat().st_mtime)
    if roadmap_files:
        latest_roadmap = roadmap_files[-1]
        index_content += f"""
### 5️⃣ Roadmap de Adoção

Plano de implementação da transformação:

- [🗺️ Roadmap de Adoção](./{latest_roadmap.name})

"""

    # Estatísticas
    total_blueprints = sum(
        len(list((d / "blueprints").glob("*_blueprint.md")))
        for d in Path("outputs").iterdir()
        if d.is_dir() and d.name != "json" and (d / "blueprints").exists()
    )

    index_content += f"""
---

## 📊 Estatísticas

- **Aplicações Analisadas**: {total_blueprints}
- **Projetos**: {len([d for d in Path('outputs').iterdir() if d.is_dir() and d.name != 'json'])}
- **Análises de Gap**: {len(gap_files)}
- **Modelos TO-BE**: {len(to_be_files)}
- **Roadmaps**: {len(roadmap_files)}

---

## 🎯 Próximos Passos

1. **Revisar** toda a documentação gerada
2. **Validar** com stakeholders técnicos
3. **Apresentar** ao Steering Committee
4. **Aprovar** roadmap e orçamento
5. **Iniciar** execução da Onda 1

---

## 👥 Audiências

| Artefato | Audiência |
|---|---|
| Blueprints AS-IS | Tech Leads, Arquitetos |
| Modelo TO-BE | VPs de Engenharia, Arquitetos |
| Análise de Gaps | VPs de Engenharia, PMO, Arquitetos |
| Roadmap de Adoção | PMO, C-Level, VPs |

---

*Gerado automaticamente pelo Orquestrador de Transformação Arquitetural*
"""

    index_path = Path("outputs") / "INDEX.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)

    print(f"✅ Índice gerado: {index_path}")
    return index_path


# =============================================================================
# Main
# =============================================================================

def main():
    print_banner("ORQUESTRADOR DE TRANSFORMAÇÃO ARQUITETURAL", "🚀")

    print("""
Pipeline completo (ordem correta):

  1️⃣  Blueprints AS-IS      — análise do estado atual por aplicação
  2️⃣  Extração de Portfólio — gera portfolio_structured.json (base factual)
  3️⃣  Análise de Gaps       — identifica lacunas vs. boas práticas (gap_analyzer_v5)
  4️⃣  Modelo TO-BE          — arquitetura futura informada pelos gaps (tobe_generator_v5)
  5️⃣  Roadmap de Adoção     — iniciativas priorizadas por impacto e dependência

""")

    if input("Deseja continuar? (S/n): ").strip().lower() == "n":
        print("❌ Operação cancelada")
        return

    if not check_prerequisites():
        print("\n❌ Corrija os problemas acima antes de continuar")
        return

    start_time = datetime.now()

    steps = [
        ("Blueprints AS-IS",       run_blueprint_generation),
        ("Extração de Portfólio",  run_blueprint_extraction),
        ("Análise de Gaps",        run_gap_analysis),
        ("Modelo TO-BE",           run_to_be_generation),
        ("Roadmap de Adoção",      run_roadmap_generation),
    ]

    completed = []
    failed = []

    for step_name, step_func in steps:
        try:
            if step_func():
                completed.append(step_name)
            else:
                failed.append(step_name)
                print(f"\n⚠️  Etapa '{step_name}' falhou — continuando...")
        except KeyboardInterrupt:
            print("\n\n❌ Operação interrompida pelo usuário")
            break
        except Exception as e:
            print(f"\n❌ Erro inesperado em '{step_name}': {e}")
            failed.append(step_name)

    try:
        generate_index()
    except Exception as e:
        print(f"⚠️  Erro ao gerar índice: {e}")

    duration = datetime.now() - start_time
    print_banner("RELATÓRIO FINAL", "🎉")

    print(f"⏱️  Tempo Total: {duration}")
    print(f"\n✅ Etapas Concluídas ({len(completed)}):")
    for step in completed:
        print(f"   • {step}")

    if failed:
        print(f"\n❌ Etapas com Falha ({len(failed)}):")
        for step in failed:
            print(f"   • {step}")

    print("\n" + "=" * 80)
    print("📂 Todos os arquivos foram salvos em: ./outputs/")
    print("📖 Consulte outputs/INDEX.md para navegar pela documentação")
    print("=" * 80)


if __name__ == "__main__":
    main()
