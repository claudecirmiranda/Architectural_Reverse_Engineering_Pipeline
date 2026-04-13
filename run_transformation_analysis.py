"""
Orquestrador de Transformação Arquitetural Completa

Este script executa todo o pipeline de análise e planejamento:
1. Geração de Blueprints AS-IS (se necessário)
2. Modelo TO-BE
3. Análise de Gaps
4. Roadmap de Adoção

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
    
    # 1. Verifica API Key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        issues.append("❌ ANTHROPIC_API_KEY não configurada")
    else:
        print("✅ API Key configurada")
    
    # 2. Verifica bibliotecas
    try:
        import anthropic
        print("✅ Biblioteca anthropic instalada")
    except ImportError:
        issues.append("❌ Biblioteca anthropic não instalada (pip install anthropic)")
    
    # 3. Verifica diretório outputs
    if not Path('outputs').exists():
        issues.append("❌ Diretório 'outputs' não encontrado")
    else:
        print("✅ Diretório outputs encontrado")
    
    # 4. Verifica se existem blueprints
    blueprints_found = False
    for project_dir in Path('outputs').iterdir():
        if project_dir.is_dir() and project_dir.name != 'json':
            blueprints_dir = project_dir / 'blueprints'
            if blueprints_dir.exists() and list(blueprints_dir.glob('*_blueprint.md')):
                blueprints_found = True
                break
    
    if not blueprints_found:
        print("⚠️  Nenhum blueprint AS-IS encontrado")
        print("   Será necessário executar blueprint_generator.py primeiro")
    else:
        print("✅ Blueprints AS-IS encontrados")
    
    if issues:
        print("\n" + "="*80)
        print("PROBLEMAS ENCONTRADOS:")
        for issue in issues:
            print(f"  {issue}")
        print("="*80)
        return False
    
    print("\n✅ Todos os pré-requisitos atendidos!")
    return True


def run_blueprint_generation():
    """Executa geração de blueprints se necessário."""
    print_banner("ETAPA 1: BLUEPRINTS AS-IS", "🔷")
    
    # Verifica se já existem blueprints
    blueprints_found = False
    for project_dir in Path('outputs').iterdir():
        if project_dir.is_dir() and project_dir.name != 'json':
            blueprints_dir = project_dir / 'blueprints'
            if blueprints_dir.exists() and list(blueprints_dir.glob('*_blueprint.md')):
                blueprints_found = True
                break
    
    if blueprints_found:
        print("✅ Blueprints AS-IS já existem, pulando geração...")
        response = input("\n🔄 Deseja regenerar blueprints? (s/N): ").strip().lower()
        if response != 's':
            return True
    
    print("📝 Executando blueprint_generator.py...")
    
    try:
        from blueprint_generator import BlueprintGenerator
        generator = BlueprintGenerator()
        generator.process_all_repositories()
        return True
    except Exception as e:
        print(f"❌ Erro ao gerar blueprints: {e}")
        return False


def run_to_be_generation():
    """Executa geração do modelo TO-BE."""
    print_banner("ETAPA 2: MODELO TO-BE", "🔷")
    
    # Verifica se já existe TO-BE
    to_be_files = list(Path('outputs').glob('TO_BE_Model_*.md'))
    if to_be_files:
        latest = max(to_be_files, key=lambda p: p.stat().st_mtime)
        print(f"✅ Modelo TO-BE já existe: {latest.name}")
        response = input("\n🔄 Deseja regenerar modelo TO-BE? (s/N): ").strip().lower()
        if response != 's':
            return True
    
    print("📝 Executando to_be_generator.py...")
    
    try:
        from to_be_generator import ToBeGenerator
        generator = ToBeGenerator()
        generator.generate()
        return True
    except Exception as e:
        print(f"❌ Erro ao gerar TO-BE: {e}")
        return False


def run_gap_analysis():
    """Executa análise de gaps."""
    print_banner("ETAPA 3: ANÁLISE DE GAPS", "🔷")
    
    # Verifica se já existe análise de gaps
    gap_files = list(Path('outputs').glob('Gap_Analysis_*.md'))
    if gap_files:
        latest = max(gap_files, key=lambda p: p.stat().st_mtime)
        print(f"✅ Análise de Gaps já existe: {latest.name}")
        response = input("\n🔄 Deseja regenerar análise de gaps? (s/N): ").strip().lower()
        if response != 's':
            return True
    
    print("📝 Executando gap_analyzer.py...")
    
    try:
        from gap_analyzer import GapAnalyzer
        analyzer = GapAnalyzer()
        analyzer.analyze()
        return True
    except Exception as e:
        print(f"❌ Erro ao analisar gaps: {e}")
        return False


def run_roadmap_generation():
    """Executa geração do roadmap."""
    print_banner("ETAPA 4: ROADMAP DE ADOÇÃO", "🔷")
    
    # Verifica se já existe roadmap
    roadmap_files = list(Path('outputs').glob('Adoption_Roadmap_*.md'))
    if roadmap_files:
        latest = max(roadmap_files, key=lambda p: p.stat().st_mtime)
        print(f"✅ Roadmap já existe: {latest.name}")
        response = input("\n🔄 Deseja regenerar roadmap? (s/N): ").strip().lower()
        if response != 's':
            return True
    
    print("📝 Executando roadmap_generator.py...")
    
    try:
        from roadmap_generator import RoadmapGenerator
        generator = RoadmapGenerator()
        generator.generate()
        return True
    except Exception as e:
        print(f"❌ Erro ao gerar roadmap: {e}")
        return False


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
    
    # Lista blueprints
    for project_dir in sorted(Path('outputs').iterdir()):
        if not project_dir.is_dir() or project_dir.name == 'json':
            continue
        
        blueprints_dir = project_dir / 'blueprints'
        if not blueprints_dir.exists():
            continue
        
        blueprints = list(blueprints_dir.glob('*_blueprint.md'))
        if blueprints:
            index_content += f"\n#### Projeto: {project_dir.name}\n\n"
            for bp in sorted(blueprints):
                app_name = bp.stem.replace('_blueprint', '')
                index_content += f"- [{app_name}](./{project_dir.name}/blueprints/{bp.name})\n"
    
    # TO-BE
    to_be_files = sorted(Path('outputs').glob('TO_BE_Model_*.md'), key=lambda p: p.stat().st_mtime)
    if to_be_files:
        latest_to_be = to_be_files[-1]
        index_content += f"""

### 2️⃣ Modelo TO-BE (Estado Futuro)

Visão do estado futuro desejado da arquitetura:

- [📘 Modelo TO-BE](./{latest_to_be.name})

"""
    
    # Gap Analysis
    gap_files = sorted(Path('outputs').glob('Gap_Analysis_*.md'), key=lambda p: p.stat().st_mtime)
    if gap_files:
        latest_gap = gap_files[-1]
        index_content += f"""
### 3️⃣ Análise de Gaps

Identificação de lacunas entre AS-IS e TO-BE:

- [📊 Análise de Gaps](./{latest_gap.name})

"""
    
    # Roadmap
    roadmap_files = sorted(Path('outputs').glob('Adoption_Roadmap_*.md'), key=lambda p: p.stat().st_mtime)
    if roadmap_files:
        latest_roadmap = roadmap_files[-1]
        index_content += f"""
### 4️⃣ Roadmap de Adoção

Plano de implementação da transformação:

- [🗺️ Roadmap de Adoção](./{latest_roadmap.name})

"""
    
    # Estatísticas
    total_blueprints = 0
    for project_dir in Path('outputs').iterdir():
        if project_dir.is_dir() and project_dir.name != 'json':
            blueprints_dir = project_dir / 'blueprints'
            if blueprints_dir.exists():
                total_blueprints += len(list(blueprints_dir.glob('*_blueprint.md')))
    
    index_content += f"""
---

## 📊 Estatísticas

- **Aplicações Analisadas**: {total_blueprints}
- **Projetos**: {len([d for d in Path('outputs').iterdir() if d.is_dir() and d.name != 'json'])}
- **Documentos TO-BE**: {len(to_be_files)}
- **Análises de Gap**: {len(gap_files)}
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

Esta documentação foi estruturada para atender diferentes audiências:

- **C-Level**: Sumários executivos, ROI, roadmap de alto nível
- **VPs Engenharia**: Decisões arquiteturais, estratégia técnica
- **Tech Leads**: Detalhes técnicos, padrões, ferramentas
- **PMO**: Cronogramas, recursos, riscos, orçamento
- **Desenvolvedores**: Novos padrões, treinamentos, mudanças

---

*Gerado automaticamente pelo Transformation Orchestrator*
"""
    
    # Salva índice
    index_path = Path('outputs') / 'INDEX.md'
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"✅ Índice gerado: {index_path}")
    return index_path


def main():
    """Função principal."""
    print_banner("ORQUESTRADOR DE TRANSFORMAÇÃO ARQUITETURAL", "🚀")
    
    print("""
Este script irá executar todo o pipeline de análise:

1️⃣  Blueprints AS-IS - Análise do estado atual
2️⃣  Modelo TO-BE - Definição do estado futuro
3️⃣  Análise de Gaps - Identificação de lacunas
4️⃣  Roadmap de Adoção - Plano de implementação

""")
    
    response = input("Deseja continuar? (S/n): ").strip().lower()
    if response == 'n':
        print("❌ Operação cancelada")
        return
    
    # Verifica pré-requisitos
    if not check_prerequisites():
        print("\n❌ Corrija os problemas acima antes de continuar")
        return
    
    start_time = datetime.now()
    
    # Executa pipeline
    steps = [
        ("Blueprints AS-IS", run_blueprint_generation),
        ("Modelo TO-BE", run_to_be_generation),
        ("Análise de Gaps", run_gap_analysis),
        ("Roadmap de Adoção", run_roadmap_generation)
    ]
    
    completed = []
    failed = []
    
    for step_name, step_func in steps:
        try:
            if step_func():
                completed.append(step_name)
            else:
                failed.append(step_name)
                print(f"\n⚠️  Etapa '{step_name}' falhou, mas continuando...")
        except KeyboardInterrupt:
            print("\n\n❌ Operação interrompida pelo usuário")
            break
        except Exception as e:
            print(f"\n❌ Erro inesperado em '{step_name}': {e}")
            failed.append(step_name)
    
    # Gera índice
    try:
        generate_index()
    except Exception as e:
        print(f"⚠️  Erro ao gerar índice: {e}")
    
    # Relatório final
    end_time = datetime.now()
    duration = end_time - start_time
    
    print_banner("RELATÓRIO FINAL", "🎉")
    
    print(f"⏱️  Tempo Total: {duration}")
    print(f"\n✅ Etapas Concluídas ({len(completed)}):")
    for step in completed:
        print(f"   • {step}")
    
    if failed:
        print(f"\n❌ Etapas com Falha ({len(failed)}):")
        for step in failed:
            print(f"   • {step}")
    
    print("\n" + "="*80)
    print("📂 Todos os arquivos foram salvos em: ./outputs/")
    print("📖 Consulte INDEX.md para navegar pela documentação")
    print("="*80)
    
    print("""
    
🎯 DOCUMENTAÇÃO COMPLETA GERADA!

Você agora tem:
  ✅ Blueprints detalhados de cada aplicação (AS-IS)
  ✅ Modelo de arquitetura futura (TO-BE)
  ✅ Análise detalhada de gaps
  ✅ Roadmap de implementação com ondas, recursos e KPIs

📋 Próximos passos sugeridos:
  1. Revisar toda a documentação gerada
  2. Validar tecnicamente com arquitetos e tech leads
  3. Apresentar ao Steering Committee
  4. Obter aprovação de budget e recursos
  5. Iniciar execução!

🚀 Boa sorte com sua transformação arquitetural!
    """)


if __name__ == "__main__":
    main()