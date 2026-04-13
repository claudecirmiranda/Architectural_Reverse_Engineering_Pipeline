import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import anthropic

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# =============================================================================
# Configuração
# =============================================================================
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-20250514"


class GapAnalyzerV2:
    """
    Analisa gaps entre AS-IS e BOAS PRÁTICAS DE MERCADO.
    
    Esta versão identifica problemas ANTES de criar o TO-BE,
    permitindo que o modelo futuro seja construído para resolver
    os gaps reais encontrados no portfólio.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY não encontrada.")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def load_all_blueprints(self, base_dir: str = 'outputs') -> Dict[str, List[Dict]]:
        """Carrega todos os blueprints AS-IS."""
        base_path = Path(base_dir)
        blueprints = {}
        
        for project_dir in base_path.iterdir():
            if not project_dir.is_dir() or project_dir.name == 'json':
                continue
            
            blueprints_dir = project_dir / 'blueprints'
            if not blueprints_dir.exists():
                continue
            
            project_name = project_dir.name
            blueprints[project_name] = []
            
            for blueprint_file in blueprints_dir.glob('*_blueprint.md'):
                with open(blueprint_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    blueprints[project_name].append({
                        'name': blueprint_file.stem.replace('_blueprint', ''),
                        'file': str(blueprint_file),
                        'content': content
                    })
        
        return blueprints
    
    def analyze_gaps_vs_best_practices(self, as_is_data: str, portfolio_stats: Dict) -> str:
        """
        Analisa gaps entre AS-IS e boas práticas de mercado.
        
        Esta é a PRIMEIRA análise de gaps, que identifica:
        1. Padrões anti-pattern no portfólio
        2. Ausência de práticas modernas
        3. Débitos técnicos por categoria
        4. Inconsistências e heterogeneidade
        """
        
        prompt = f"""Você é um Arquiteto de Soluções Sênior especializado em Modernização de Portfólios de Software.

# MISSÃO CRÍTICA

Você está realizando a **PRIMEIRA ANÁLISE DE GAPS** de um portfólio de aplicações.

**OBJETIVO**: Identificar problemas, anti-patterns e oportunidades de melhoria comparando o estado atual (AS-IS) 
com **BOAS PRÁTICAS DE MERCADO E PADRÕES MODERNOS**.

⚠️ **IMPORTANTE**: Esta análise acontece ANTES de definir o modelo TO-BE. 
O TO-BE será criado DEPOIS, baseado nos gaps que você identificar agora.

---

# REGRAS FUNDAMENTAIS

## 1. BASE APENAS NOS DADOS REAIS

✅ **PERMITIDO**:
- Identificar tecnologias REALMENTE presentes nos blueprints
- Apontar ausências de práticas modernas (se não houver evidência)
- Identificar inconsistências entre aplicações
- Calcular métricas baseadas nos dados

❌ **PROIBIDO**:
- Inventar tecnologias que não estão nos blueprints
- Assumir problemas sem evidência
- Criar gaps genéricos sem base nos dados

## 2. ESTRUTURA OBRIGATÓRIA PARA CADA GAP

```markdown
#### Gap: [Nome Claro e Específico]

**📊 Evidências AS-IS:**
- [App-1]: [Tecnologia/Padrão X encontrado] - fonte: [blueprint]
- [App-2]: [Ausência de Y] - fonte: [blueprint]
- [Estatística]: X de Y aplicações apresentam Z

**🎯 Boa Prática de Mercado:**
- [Descrição do que é considerado padrão moderno]
- [Referência: Cloud-native patterns / 12-factor / etc.]

**🔍 Gap Identificado:**
- [Diferença específica entre atual e ideal]
- [Impacto: Técnico/Operacional/Segurança/Custos]

**📈 Severidade:** [Crítica/Alta/Média/Baixa]
**🎯 Categoria:** [Arquitetura/Tecnologia/Segurança/Observabilidade/Processos]

**💡 Oportunidade:**
- [Benefício de resolver este gap]
```

## 3. CATEGORIAS DE ANÁLISE

Analise gaps nas seguintes dimensões:

### A) Arquitetura e Design
- Padrões arquiteturais (monolito vs microserviços)
- Separação de responsabilidades
- Acoplamento e coesão
- Escalabilidade e resiliência

### B) Stack Tecnológico
- Versões de frameworks e bibliotecas
- Consistência tecnológica
- Modernidade das escolhas
- Suporte de longo prazo

### C) Cloud-Native e Containerização
- Uso de containers
- Orquestração (Kubernetes, etc.)
- Stateless vs Stateful
- 12-Factor compliance

### D) APIs e Integração
- Padrões de API (REST/GraphQL/gRPC)
- Versionamento de APIs
- Documentação (OpenAPI/Swagger)
- Gateway/BFF patterns

### E) Dados e Persistência
- Tipos de banco de dados
- Estratégias de cache
- Data patterns (CQRS, Event Sourcing)
- Migrations e versionamento

### F) Observabilidade
- Logging estruturado
- Métricas (APM)
- Tracing distribuído
- Health checks e readiness probes

### G) Segurança
- Autenticação e autorização
- Secrets management
- API security
- Compliance e auditoria

### H) CI/CD e DevOps
- Pipelines de build
- Testes automatizados
- Deployment strategies
- Infrastructure as Code

### I) Qualidade de Código
- Testes (unitários, integração, e2e)
- Code coverage
- Análise estática
- Linting e formatação

### J) Documentação
- README e getting started
- Arquitetura documentada
- ADRs (Architecture Decision Records)
- Runbooks operacionais

---

# DADOS DO PORTFÓLIO

## Estatísticas Consolidadas

{json.dumps(portfolio_stats, indent=2, ensure_ascii=False)}

## Blueprints AS-IS Completos

{as_is_data}

---

# INSTRUÇÕES PARA ANÁLISE

Gere um documento Markdown estruturado seguindo este formato:

# 🔍 ANÁLISE DE GAPS - AS-IS vs BOAS PRÁTICAS

**Data da Análise:** {datetime.now().strftime("%d/%m/%Y")}  
**Portfólio:** {portfolio_stats.get('total_apps', 0)} aplicações em {portfolio_stats.get('total_projects', 0)} projetos

---

## 📊 SUMÁRIO EXECUTIVO

### Visão Geral do Portfólio

[Descreva em 3-4 parágrafos:]
- Perfil técnico predominante (stacks, padrões, maturidade)
- Nível de consistência vs heterogeneidade
- Principais gaps críticos identificados
- Oportunidades estratégicas de modernização

### Métricas de Maturidade

| Dimensão | Nível Atual | Gaps Críticos | Oportunidade |
|----------|-------------|---------------|--------------|
| Arquitetura | [0-5] ⭐ | [número] | [potencial] |
| Cloud-Native | [0-5] ⭐ | [número] | [potencial] |
| Observabilidade | [0-5] ⭐ | [número] | [potencial] |
| Segurança | [0-5] ⭐ | [número] | [potencial] |
| DevOps | [0-5] ⭐ | [número] | [potencial] |

**IMPORTANTE**: Base as estrelas em evidências concretas dos blueprints.

---

## 🎯 GAPS PRIORITÁRIOS (TOP 10)

Tabela consolidada dos 10 gaps mais importantes:

| # | Gap | Apps Afetadas | Severidade | Categoria | Impacto | Esforço |
|---|-----|---------------|------------|-----------|---------|---------|
| 1 | [gap específico] | [X/Y] | 🔴 Crítica | [cat] | Alto | M |
| 2 | [gap específico] | [X/Y] | 🔴 Crítica | [cat] | Alto | L |
| ... | ... | ... | ... | ... | ... | ... |

**Legenda:**
- Severidade: 🔴 Crítica / 🟠 Alta / 🟡 Média / 🟢 Baixa
- Esforço: S (Small) / M (Medium) / L (Large) / XL (Extra Large)

---

## 📋 ANÁLISE DETALHADA POR CATEGORIA

### 1️⃣ Arquitetura e Design

#### Gap 1.1: [Nome Específico]

**📊 Evidências AS-IS:**
- ✅ **Encontrado**:
  - [App-1] implementa [padrão X] - fonte: [blueprint]
  - [App-2] não especifica arquitetura - fonte: [blueprint]
- ❌ **Não Encontrado**:
  - Nenhuma aplicação documenta [padrão Y]
- 📈 **Estatística**: X de Y apps (Z%) usam/não usam W

**🎯 Boa Prática de Mercado:**
- [Descrição do padrão moderno esperado]
- Referência: [Cloud-native patterns / Martin Fowler / etc.]

**🔍 Gap Identificado:**
- [Diferença clara entre atual e desejado]
- Impacto em: [Manutenibilidade/Escalabilidade/Custos]

**📈 Severidade:** [Crítica/Alta/Média/Baixa]  
**💰 Impacto Estimado:** [Técnico/Operacional/Financeiro]  
**⏱️ Esforço de Resolução:** [S/M/L/XL]

**💡 Oportunidade:**
- [Benefício específico de resolver este gap]

**🎯 Aplicações Afetadas:**
- [Lista real com nomes dos blueprints]

---

[Repita para todos os gaps identificados em cada categoria]

### 2️⃣ Stack Tecnológico

[Mesma estrutura]

### 3️⃣ Cloud-Native e Containerização

[Mesma estrutura]

### 4️⃣ APIs e Integração

[Mesma estrutura]

### 5️⃣ Dados e Persistência

[Mesma estrutura]

### 6️⃣ Observabilidade

[Mesma estrutura]

### 7️⃣ Segurança

[Mesma estrutura]

### 8️⃣ CI/CD e DevOps

[Mesma estrutura]

### 9️⃣ Qualidade de Código

[Mesma estrutura]

### 🔟 Documentação

[Mesma estrutura]

---

## 🎨 ANÁLISE DE PADRÕES

### Padrões Positivos Identificados

Liste práticas BOAS encontradas no portfólio:

1. **[Padrão Positivo 1]**
   - Encontrado em: [Apps X, Y, Z]
   - Impacto: [Benefício observado]
   - Recomendação: Expandir para outras aplicações

### Anti-Patterns Identificados

Liste práticas RUINS encontradas no portfólio:

1. **[Anti-Pattern 1]**
   - Encontrado em: [Apps A, B, C]
   - Risco: [Problema causado]
   - Prioridade de correção: [Alta/Média/Baixa]

### Inconsistências Críticas

Liste áreas onde há falta de padronização:

1. **[Área de Inconsistência]**
   - Variações encontradas: [Lista]
   - Apps afetadas: [Número e %]
   - Impacto: [Complexidade operacional/custos]

---

## 📊 ANÁLISE QUANTITATIVA

### Distribuição de Gaps por Categoria

```mermaid
pie title "Gaps por Categoria"
    "Arquitetura" : [número]
    "Cloud-Native" : [número]
    "Observabilidade" : [número]
    "Segurança" : [número]
    "DevOps" : [número]
    "Outros" : [número]
```

### Distribuição por Severidade

| Severidade | Quantidade | % do Total | Apps Afetadas |
|------------|------------|------------|---------------|
| 🔴 Crítica | [num] | [%] | [lista] |
| 🟠 Alta | [num] | [%] | [lista] |
| 🟡 Média | [num] | [%] | [lista] |
| 🟢 Baixa | [num] | [%] | [lista] |

### Heatmap de Gaps por Aplicação

| Aplicação | Arquitetura | Cloud | Obs | Seg | DevOps | Total |
|-----------|-------------|-------|-----|-----|--------|-------|
| [App-1] | 🔴 3 | 🟠 2 | 🟡 1 | 🔴 2 | 🟢 0 | 8 |
| [App-2] | 🟡 1 | 🟢 0 | 🟠 2 | 🟡 1 | 🟡 1 | 5 |

**Legenda**: Número = quantidade de gaps | Cor = severidade máxima

---

## 🎯 MATRIZ DE PRIORIZAÇÃO

### Quick Wins (Alto Impacto + Baixo Esforço)

```mermaid
quadrantChart
    title Priorização de Gaps
    x-axis Baixo Esforço --> Alto Esforço
    y-axis Baixo Impacto --> Alto Impacto
    quadrant-1 Quick Wins
    quadrant-2 Grandes Apostas
    quadrant-3 Fill-ins
    quadrant-4 Agradáveis de Ter
    
    [Gap Real 1]: [0.x, 0.y]
    [Gap Real 2]: [0.x, 0.y]
```

### Classificação por Quadrante

**🎯 Quick Wins (Prioridade Máxima)**
1. [Gap] - [X apps afetadas] - Benefício: [desc]
2. [Gap] - [Y apps afetadas] - Benefício: [desc]

**🚀 Grandes Apostas (Planejamento Estratégico)**
1. [Gap] - [X apps afetadas] - ROI estimado: [desc]

**⚡ Fill-ins (Quando houver capacidade)**
1. [Gap] - [X apps afetadas]

**💡 Agradáveis de Ter (Backlog)**
1. [Gap] - [X apps afetadas]

---

## 💰 ANÁLISE DE DÉBITO TÉCNICO

### Estimativa de Débito por Categoria

| Categoria | Débito Estimado | Apps Afetadas | Prioridade |
|-----------|----------------|---------------|------------|
| Arquitetura | [esforço total] | [lista] | P0 |
| Cloud-Native | [esforço total] | [lista] | P1 |
| Observabilidade | [esforço total] | [lista] | P1 |

**Métrica de Débito**: 
- S = 1 sprint-pessoa
- M = 2-4 sprints-pessoa
- L = 5-10 sprints-pessoa
- XL = 10+ sprints-pessoa

### Top 5 Aplicações com Maior Débito

1. **[App-1]**: [total gaps] gaps | [severidade] | Débito: [XL]
2. **[App-2]**: [total gaps] gaps | [severidade] | Débito: [L]

---

## 🎓 ANÁLISE DE COMPETÊNCIAS

### Competências Técnicas Necessárias

Baseado nas tecnologias REALMENTE encontradas:

**Competências Atuais Exigidas:**
- [Tech-1]: [número] aplicações requerem
- [Tech-2]: [número] aplicações requerem

**Gaps de Competências (para modernização):**
- [Nova competência 1]: Necessária para resolver [gap X]
- [Nova competência 2]: Necessária para resolver [gap Y]

---

## 🎯 RECOMENDAÇÕES ESTRATÉGICAS

### Recomendação 1: [Título Específico]

**Baseado em:** [Gaps específicos que afetam X aplicações]

**Ação Recomendada:**
- [Ação específica e acionável]
- [Passos para implementação]

**Benefícios Esperados:**
- Técnico: [benefício]
- Operacional: [benefício]
- Financeiro: [benefício]

**Aplicações Prioritárias:**
- [Lista ordenada por criticidade]

**Esforço Estimado:** [S/M/L/XL]

**Timeline Sugerido:** [curto/médio/longo prazo]

---

[Repita para top 5-7 recomendações]

---

## 📈 ROADMAP MACRO SUGERIDO

Baseado na priorização de gaps:

```mermaid
gantt
    title Roadmap de Resolução de Gaps (Macro)
    dateFormat YYYY-MM
    section Fase 1 - Quick Wins
    [Gap Prioritário 1] :2025-03, 2M
    [Gap Prioritário 2] :2025-03, 1M
    section Fase 2 - Fundação
    [Gap Crítico 1] :2025-05, 3M
    section Fase 3 - Escala
    [Gap de Escala] :2025-08, 4M
```

**Nota**: Este é um roadmap MACRO. O roadmap detalhado será criado após 
definir o modelo TO-BE baseado nestes gaps.

---

## 🎯 PRÓXIMOS PASSOS

### Imediato (Próximos 30 dias)

1. **Validar Gaps Críticos**
   - Revisar top 10 gaps com stakeholders
   - Confirmar prioridades e impactos
   - Ajustar severidades se necessário

2. **Definir Modelo TO-BE**
   - Usar esta análise como base
   - Criar arquitetura de referência que resolva os gaps prioritários
   - Validar viabilidade técnica e financeira

### Curto Prazo (60-90 dias)

3. **Criar Roadmap Detalhado**
   - Detalhar ondas de migração
   - Definir critérios de priorização de apps
   - Estimar custos e recursos

4. **Iniciar Quick Wins**
   - Implementar gaps de baixo esforço/alto impacto
   - Gerar aprendizados para grandes apostas
   - Comunicar vitórias rápidas

---

## 📝 CONCLUSÃO

### Principais Descobertas

1. **[Descoberta 1]**: [Descrição baseada em dados]
2. **[Descoberta 2]**: [Descrição baseada em dados]
3. **[Descoberta 3]**: [Descrição baseada em dados]

### Nível de Maturidade Atual

**Score Consolidado**: [X/5] ⭐

**Baseado em:**
- [Métrica 1]: [valor/evidência]
- [Métrica 2]: [valor/evidência]

### Mensagem Final

[Síntese em 2-3 parágrafos sobre:]
- Estado atual do portfólio
- Oportunidades identificadas
- Direcionamento para o TO-BE

---

**⚠️ NOTA IMPORTANTE**: Esta análise de gaps serve como INPUT para a criação 
do Modelo TO-BE. O estado futuro desejado deve ser desenhado especificamente 
para resolver os gaps prioritários identificados neste documento.

---

# VALIDAÇÃO FINAL

Antes de finalizar, certifique-se:

✅ Todos os gaps têm evidências concretas dos blueprints  
✅ Todas as tecnologias mencionadas foram realmente encontradas  
✅ Aplicações afetadas são reais e verificáveis  
✅ Métricas e estatísticas estão corretas  
✅ Nenhum gap foi inventado sem base nos dados  
✅ Severidades são justificadas por impacto real  

---

Gere agora a **ANÁLISE COMPLETA DE GAPS vs BOAS PRÁTICAS** seguindo RIGOROSAMENTE todas as instruções acima."""

        try:
            print("🤖 Analisando gaps entre AS-IS e Boas Práticas de Mercado...")
            print("   📋 Modo: Identificação de problemas reais do portfólio")
            
            message = self.client.messages.create(
                model=MODEL,
                max_tokens=16000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text
        
        except Exception as e:
            print(f"❌ Erro ao analisar gaps: {e}")
            return None
    
    def calculate_portfolio_stats(self, blueprints: Dict[str, List[Dict]]) -> Dict:
        """Calcula estatísticas do portfólio."""
        total_projects = len(blueprints)
        total_apps = sum(len(apps) for apps in blueprints.values())
        
        # Contar tecnologias mencionadas (análise simples)
        tech_stack = {}
        frameworks = {}
        databases = {}
        
        for project, apps in blueprints.items():
            for app in apps:
                content = app['content'].lower()
                
                # Node.js e frameworks
                if 'node.js' in content or 'nodejs' in content:
                    tech_stack['Node.js'] = tech_stack.get('Node.js', 0) + 1
                if 'nestjs' in content or 'nest.js' in content:
                    frameworks['NestJS'] = frameworks.get('NestJS', 0) + 1
                if 'express' in content:
                    frameworks['Express'] = frameworks.get('Express', 0) + 1
                
                # Bancos de dados
                if 'postgresql' in content or 'postgres' in content:
                    databases['PostgreSQL'] = databases.get('PostgreSQL', 0) + 1
                if 'mongodb' in content or 'mongo' in content:
                    databases['MongoDB'] = databases.get('MongoDB', 0) + 1
                if 'redis' in content:
                    databases['Redis'] = databases.get('Redis', 0) + 1
                
                # Outros
                if 'typescript' in content:
                    tech_stack['TypeScript'] = tech_stack.get('TypeScript', 0) + 1
                if 'graphql' in content:
                    tech_stack['GraphQL'] = tech_stack.get('GraphQL', 0) + 1
                if 'docker' in content:
                    tech_stack['Docker'] = tech_stack.get('Docker', 0) + 1
                if 'kubernetes' in content or 'k8s' in content:
                    tech_stack['Kubernetes'] = tech_stack.get('Kubernetes', 0) + 1
        
        return {
            'total_projects': total_projects,
            'total_apps': total_apps,
            'tech_stack': tech_stack,
            'frameworks': frameworks,
            'databases': databases,
            'apps_per_project': {
                project: len(apps) for project, apps in blueprints.items()
            }
        }
    
    def save_gap_analysis(self, content: str, output_dir: str = 'outputs'):
        """Salva a análise de gaps."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Gap_Analysis_Initial_{timestamp}.md"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def analyze(self):
        """Executa o processo completo de análise de gaps inicial."""
        print("="*80)
        print("🔍 ANÁLISE INICIAL DE GAPS - AS-IS vs BOAS PRÁTICAS")
        print("="*80)
        print("\n📌 NOVA ABORDAGEM:")
        print("   1. Identifica gaps vs boas práticas de mercado")
        print("   2. Depois, TO-BE será criado para resolver estes gaps")
        print("   3. Finalmente, roadmap baseado no TO-BE específico")
        
        # 1. Carrega blueprints AS-IS
        print("\n📖 Carregando blueprints AS-IS...")
        blueprints = self.load_all_blueprints()
        
        total_projects = len(blueprints)
        total_apps = sum(len(apps) for apps in blueprints.values())
        
        print(f"✅ {total_projects} projetos carregados")
        print(f"✅ {total_apps} aplicações analisadas")
        
        if total_apps == 0:
            print("❌ Nenhum blueprint AS-IS encontrado!")
            print("   Execute blueprint_generator.py primeiro.")
            return
        
        # 2. Calcula estatísticas do portfólio
        print("\n📊 Calculando estatísticas do portfólio...")
        portfolio_stats = self.calculate_portfolio_stats(blueprints)
        
        print(f"   📦 Stack encontrado:")
        for tech, count in portfolio_stats['tech_stack'].items():
            print(f"      - {tech}: {count} apps")
        
        # 3. Prepara dados consolidados AS-IS
        print("\n📝 Consolidando blueprints AS-IS...")
        as_is_summary = "# BLUEPRINTS AS-IS CONSOLIDADOS\n\n"
        
        for project, apps in blueprints.items():
            as_is_summary += f"## Projeto: {project} ({len(apps)} aplicações)\n\n"
            for app in apps:
                as_is_summary += f"### Aplicação: {app['name']}\n\n"
                as_is_summary += f"**Arquivo fonte:** `{app['file']}`\n\n"
                as_is_summary += app['content'] + "\n\n"
                as_is_summary += "---\n\n"
        
        # 4. Analisa gaps vs boas práticas
        print(f"\n🔍 Analisando gaps vs boas práticas de mercado...")
        print("   ⏱️  Este processo pode levar alguns minutos...")
        
        gap_analysis = self.analyze_gaps_vs_best_practices(as_is_summary, portfolio_stats)
        
        if not gap_analysis:
            print("❌ Falha ao gerar análise de gaps")
            return
        
        # 5. Salva análise
        print("\n💾 Salvando análise de gaps...")
        filepath = self.save_gap_analysis(gap_analysis)
        
        print(f"\n✅ Análise de gaps INICIAL concluída!")
        print(f"📄 Arquivo: {filepath}")
        print(f"📊 Tamanho: {len(gap_analysis):,} caracteres")
        
        print("\n" + "="*80)
        print("✅ ANÁLISE INICIAL CONCLUÍDA!")
        print("="*80)
        
        print(f"\n📖 PRÓXIMOS PASSOS:")
        print(f"   1. ✅ Revisar: {filepath.name}")
        print(f"   2. ⏭️  Executar: to_be_generator_v2.py")
        print(f"      (Criará TO-BE baseado nos gaps identificados)")
        print(f"   3. ⏭️  Executar: roadmap_generator.py")
        print(f"      (Criará roadmap AS-IS → TO-BE)")
        
        print("\n💡 IMPORTANTE:")
        print("   O TO-BE será desenhado especificamente para resolver")
        print("   os gaps prioritários identificados nesta análise!")


def main():
    """Função principal."""
    if not ANTHROPIC_API_KEY:
        print("❌ ERRO: ANTHROPIC_API_KEY não configurada!")
        print("   Configure no arquivo .env ou como variável de ambiente")
        return
    
    try:
        analyzer = GapAnalyzerV2()
        analyzer.analyze()
    
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()