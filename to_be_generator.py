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


class ToBeGeneratorV3:
    """
    Gera modelo TO-BE em MÓDULOS para evitar limite de tokens.
    
    Estratégia:
    1. Gera múltiplas partes do TO-BE separadamente
    2. Consolida tudo em um documento final
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY não encontrada.")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.parts_dir = Path('outputs/to_be_parts')
        self.parts_dir.mkdir(parents=True, exist_ok=True)
    
    def find_latest_gap_analysis(self, base_dir: str = 'outputs') -> Path:
        """Encontra a análise de gaps mais recente."""
        base_path = Path(base_dir)
        gap_files = list(base_path.glob('Gap_Analysis_Initial_*.md'))
        
        if not gap_files:
            return None
        
        return max(gap_files, key=lambda p: p.stat().st_mtime)
    
    def find_concept_nav360(self, base_dir: str = 'outputs') -> Path:
        """Encontra o documento Concept NAV 360."""
        base_path = Path(base_dir)
        
        possible_locations = [
            base_path / 'Concept_NAV_360.md',
            base_path / 'concept_nav_360.md',
            base_path / 'Concept NAV 360.md',
            Path('Concept_NAV_360.md'),
            Path('concept_nav_360.md'),
        ]
        
        for location in possible_locations:
            if location.exists():
                return location
        
        return None
    
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
    
    def generate_part_1_executive_summary(
        self, 
        gap_analysis: str, 
        concept_nav360: str,
        portfolio_stats: Dict
    ) -> str:
        """Parte 1: Sumário Executivo e Visão Geral."""
        
        prompt = f"""Você é um Arquiteto de Soluções Sênior criando um Modelo TO-BE.

# TAREFA: PARTE 1 - SUMÁRIO EXECUTIVO E VISÃO GERAL

Gere APENAS as seções iniciais do documento TO-BE:

1. Cabeçalho e Metadata
2. Sumário Executivo
3. Princípios Norteadores
4. Visão Geral da Transformação (tabela comparativa AS-IS vs TO-BE)

---

## INPUTS

### Gap Analysis (Resumo dos Top 10 Gaps)
{gap_analysis[:15000]}

### Concept NAV 360 (Resumo)
{concept_nav360[:10000] if concept_nav360 else "Não disponível"}

### Estatísticas do Portfólio
```json
{json.dumps(portfolio_stats, indent=2)}
```

---

## INSTRUÇÕES

Gere um documento Markdown com:

# 🎯 MODELO TO-BE - Arquitetura Futura

**Versão:** 2.0  
**Data:** {datetime.now().strftime("%d/%m/%Y")}  
**Baseado em:**
- ✅ Análise de Gaps vs Boas Práticas
- ✅ Visão Estratégica de Negócio (Concept NAV 360)
- ✅ Realidade Atual do Portfólio (AS-IS)

---

## 📊 SUMÁRIO EXECUTIVO

### Propósito do TO-BE

[2-3 parágrafos explicando:]
- Por que este TO-BE foi criado (gaps + visão estratégica)
- Principais transformações propostas
- Valor esperado da evolução

### Contexto do Portfólio

**Perfil Atual:**
- **Portfólio:** {portfolio_stats.get('total_apps', 0)} aplicações distribuídas em {portfolio_stats.get('total_projects', 0)} projetos
- **Stack Tecnológico (por camada):**
  - *Runtime & Linguagem:* [Ex: Node.js 20 LTS + TypeScript (X/Y apps)]
  - *Frameworks:* [Ex: NestJS (X apps), Express (Y apps)]
  - *APIs:* [Ex: GraphQL (X apps), REST (Y apps)]
  - *Containerização:* [Ex: Docker (X apps), Kubernetes (Y apps)]
- **Maturidade Técnica:**
  - Arquitetura: [X/5] ⭐
  - Observabilidade: [X/5] ⭐
  - DevOps: [X/5] ⭐

**IMPORTANTE:** Use estrutura por camadas para evitar confusão entre níveis hierárquicos.
Exemplo: Não misture "Node.js (94%)" com "NestJS (61%)" na mesma frase - são níveis diferentes.
  
### Gaps Críticos Identificados

Liste os top 5 gaps que o TO-BE vai resolver:

1. **[Gap 1]** - [Severidade] - [Apps afetadas] - [Impacto]
2. **[Gap 2]** - [Severidade] - [Apps afetadas] - [Impacto]
...

### Funcionalidades Estratégicas Habilitadas (Concept NAV 360)

Liste as top 5 funcionalidades do Concept que o TO-BE viabiliza:

1. **[Funcionalidade 1]** - [Descrição breve]
2. **[Funcionalidade 2]** - [Descrição breve]
...

---

## 🎯 PRINCÍPIOS NORTEADORES

Liste 5-7 princípios que guiam TODAS as decisões arquiteturais:

### 1. [Nome do Princípio]

**Baseado em:** [Gap que motivou este princípio]  
**Descrição:** [O que significa este princípio]  
**Aplicação:** [Como será aplicado]

### 2. [Nome do Princípio]

[Mesma estrutura]

---

## 📊 VISÃO GERAL DA TRANSFORMAÇÃO

Tabela comparativa AS-IS vs TO-BE por dimensão:

| Dimensão | AS-IS | TO-BE | Gap Resolvido | Benefício |
|----------|-------|-------|---------------|-----------|
| **Arquitetura** | [atual] | [futuro] | Gap #X | [benefício] |
| **Stack Tecnológico** | [atual] | [futuro] | Gap #Y | [benefício] |
| **Cloud-Native** | [atual] | [futuro] | Gap #Z | [benefício] |
| **APIs** | [atual] | [futuro] | Gap #W | [benefício] |
| **Observabilidade** | [atual] | [futuro] | Gap #V | [benefício] |
| **Segurança** | [atual] | [futuro] | Gap #U | [benefício] |
| **CI/CD** | [atual] | [futuro] | Gap #T | [benefício] |
| **Dados** | [atual] | [futuro] | Gap #S | [benefício] |

---

**FIM DA PARTE 1**

---

Gere o conteúdo acima de forma completa e profissional."""

        return self._call_api(prompt, "Parte 1 - Sumário Executivo")
    
    def generate_part_2_architecture(
        self, 
        gap_analysis: str,
        concept_nav360: str
    ) -> str:
        """Parte 2: Arquitetura de Referência."""
        
        prompt = f"""# TAREFA: PARTE 2 - ARQUITETURA DE REFERÊNCIA TO-BE

Gere as seções de arquitetura do TO-BE:

1. Visão Arquitetural (diagrama Mermaid)
2. Princípios Arquiteturais detalhados
3. Camadas da arquitetura

---

## INPUTS (Resumo)

### Top Gaps Arquiteturais
{gap_analysis[:10000]}

### Funcionalidades NAV 360 (Resumo)
{concept_nav360[:8000] if concept_nav360 else "N/A"}

---

## INSTRUÇÕES

Gere:

# 🏗️ ARQUITETURA DE REFERÊNCIA TO-BE

## Visão Arquitetural

```mermaid
graph TB
    subgraph "Camada de Experiência"
        A[Web App - React]
        B[Mobile App - React Native]
        C[Admin Portal]
    end
    
    subgraph "API Gateway Layer"
        D[API Gateway]
        E[BFF - Web]
        F[BFF - Mobile]
    end
    
    subgraph "Camada de Serviços"
        G[Serviços de Negócio]
        H[Serviços de Infraestrutura]
    end
    
    subgraph "Camada de Dados"
        I[PostgreSQL]
        J[Redis Cache]
        K[Event Bus]
    end
    
    subgraph "Observabilidade"
        L[Logs]
        M[Métricas]
        N[Tracing]
    end
    
    A --> D
    B --> D
    D --> E
    D --> F
    E --> G
    F --> G
    G --> H
    G --> I
    G --> J
```

**Descrição:**
[Explicação de cada camada e como resolve gaps identificados]

---

## Princípios Arquiteturais

### PA1: [Nome do Princípio]

**🎯 Gap(s) que Resolve:** [lista]  
**💼 Habilita (Concept):** [funcionalidade]

**Descrição:**
[Explicação completa]

**Aplicação Prática:**
- [Como será implementado]
- [Exemplos concretos]

**Benefícios:**
- Técnico: [benefício]
- Operacional: [benefício]
- Negócio: [benefício]

---

[Repita para 5-7 princípios arquiteturais]

---

## Detalhamento por Camada

### Camada de Experiência

**Responsabilidades:**
- [Lista]

**Tecnologias:**
- [Stack específico]

**Padrões:**
- [Padrões aplicados]

**Gap Resolvido:** [referência aos gaps]

---

[Repita para cada camada]

---

**FIM DA PARTE 2**"""

        return self._call_api(prompt, "Parte 2 - Arquitetura")
    
    def generate_part_3_tech_decisions(
        self,
        gap_analysis: str,
        concept_nav360: str,
        decision_area: str
    ) -> str:
        """Parte 3: Decisões Técnicas (dividido por área)."""
        
        areas_map = {
            'stack': 'Stack Tecnológico e Frameworks',
            'architecture': 'Padrões Arquiteturais (BFF, Microserviços, etc.)',
            'apis': 'APIs e Integração',
            'cloud': 'Cloud-Native e Containerização',
            'observability': 'Observabilidade e Monitoramento',
            'security': 'Segurança',
            'cicd': 'CI/CD e DevOps',
            'data': 'Gestão de Dados e NASI'
        }
        
        area_name = areas_map.get(decision_area, decision_area)
        
        prompt = f"""# TAREFA: PARTE 3.{list(areas_map.keys()).index(decision_area) + 1} - DECISÕES TÉCNICAS: {area_name}

Gere as decisões técnicas estratégicas para a área de **{area_name}**.

---

## INPUTS (Resumo)

### Gaps Relacionados a {area_name}
{gap_analysis[:10000]}

### Funcionalidades NAV 360 Relacionadas
{concept_nav360[:5000] if concept_nav360 else "N/A"}

---

## INSTRUÇÕES

Para cada decisão técnica nesta área, use o formato:

## 🔧 DECISÕES TÉCNICAS: {area_name}

### Decisão: [Nome Específico]

**🎯 Gap(s) que Resolve:**
- Gap #X: [descrição] - [severidade] - [Y apps]
- Gap #Z: [descrição] - [severidade] - [W apps]

**💼 Habilita (Concept NAV 360):**
- [Funcionalidade 1]: [como esta decisão viabiliza]
- [Funcionalidade 2]: [como esta decisão viabiliza]

**📋 Especificação TO-BE:**

[Descrição técnica detalhada da decisão]

**Tecnologias/Ferramentas:**
- [Lista específica]

**Padrões:**
- [Padrões aplicados]

**Exemplo de Implementação:**
```[linguagem]
// Código exemplo se relevante
```

**Rationale:**
- [Por que esta decisão resolve os gaps]
- [Por que esta tecnologia/abordagem foi escolhida]
- [Considerações sobre o AS-IS]

**✅ Benefícios Esperados:**
- **Técnico**: [benefício mensurável]
- **Operacional**: [benefício mensurável]
- **Negócio**: [benefício mensurável]

**⚠️ Restrições e Trade-offs:**
- [Limitações]
- [O que fica de fora]
- [Riscos]

**📊 Impacto:**
- **Apps Afetadas**: [lista com nomes reais]
- **Esforço de Migração**: [S/M/L/XL]
- **Prioridade**: [P0/P1/P2]
- **Dependências**: [outras decisões necessárias]

---

[Repita para 3-5 decisões nesta área]

---

**FIM DA PARTE 3.{list(areas_map.keys()).index(decision_area) + 1}**"""

        return self._call_api(prompt, f"Parte 3 - Decisões {area_name}")
    
    def generate_part_4_patterns_integrations(
        self,
        gap_analysis: str,
        concept_nav360: str
    ) -> str:
        """Parte 4: Padrões, Integrações e Modelo de Dados."""
        
        prompt = f"""# TAREFA: PARTE 4 - PADRÕES, INTEGRAÇÕES E DADOS

Gere as seções de:
1. Padrões e Guidelines
2. Integrações TO-BE
3. Modelo de Dados TO-BE

---

## INPUTS (Resumo)

### Gaps Relevantes
{gap_analysis[:8000]}

### Funcionalidades NAV 360 Relevantes
{concept_nav360[:8000] if concept_nav360 else "N/A"}

---

## INSTRUÇÕES

Gere:

# 🎨 PADRÕES E GUIDELINES

## Padrões de Desenvolvimento

### Estrutura de Código Padrão

```
app/
├── src/
│   ├── modules/          # Módulos de negócio
│   │   ├── patient/
│   │   ├── appointment/
│   │   ├── family/       # Novo - Gestão Familiar
│   │   └── search/       # Novo - Busca Inteligente
│   ├── shared/           # Código compartilhado
│   ├── infrastructure/   # Integrações
│   └── main.ts
├── test/
└── docs/
```

**Rationale**: [Por que esta estrutura]

### Convenções de Nomenclatura

[Padrões específicos]

### Gestão de Configurações

[Como será feito]

---

## Padrões de API

### Design de APIs REST

```
GET    /api/v1/patients/:id
POST   /api/v1/patients/:id/appointments
GET    /api/v1/families/:familyId/members
POST   /api/v1/search/intelligent
```

### Design de APIs GraphQL

```graphql
query GetPatientJourney {{
  patient(id: "123") {{
    personalizedHero
    upcomingAppointments
    familyMembers {{
      vaccinationCalendar
    }}
  }}
}}
```

**Decisão**: [Quando usar REST vs GraphQL]

---

# 🔌 INTEGRAÇÕES TO-BE

## Mapa de Integrações

| Sistema Externo | Propósito | Protocolo | Habilita (Concept) | Criticidade |
|----------------|-----------|-----------|-------------------|-------------|
| SUS | Calendário Vacinal | REST | ✅ Calendário Vacinal | Alta |
| Operadoras | Cobertura/Autorização | SOAP/REST | ✅ Vitrine de Produtos | Alta |
| Prescrição Digital | Histórico Médico | HL7/FHIR | ✅ NASI | Média |
| Laboratórios | Resultados de Exames | REST | ✅ NASI | Alta |

## Estratégia de Integrações

**🎯 Gap que Resolve**: [gaps de integração]  
**💼 Habilita**: [funcionalidades que dependem de integrações]

**Padrões:**
- API Gateway para todas as integrações
- Circuit Breaker e retry logic
- Fallback e degradação graciosa
- Cache agressivo de dados externos

**Exemplo de Implementação:**
```typescript
// Circuit breaker pattern
@Injectable()
class SUSIntegrationService {{
  @CircuitBreaker({{ threshold: 5, timeout: 10000 }})
  async getVaccinationData(cpf: string) {{
    // Implementation
  }}
}}
```

---

# 📊 MODELO DE DADOS TO-BE

## Entidades Core

### Patient (Paciente)

```typescript
interface Patient {{
  id: string;
  personalInfo: PersonalInfo;
  healthProfile: HealthProfile;
  
  // Novos campos - Gestão Familiar
  familyId?: string;
  relationshipType: 'holder' | 'dependent';
  
  // Novos campos - Personalização
  preferences: UserPreferences;
  journeyStage: JourneyStage;
  
  // NASI
  healthHistory: HealthHistory;
  vaccinationCalendar: VaccinationCalendar;
}}
```

**Rationale**: [Como suporta funcionalidades do Concept]

### Family (Família)

```typescript
interface Family {{
  id: string;
  primaryHolder: Patient;
  members: FamilyMember[];
  sharedCalendar: VaccinationCalendar;
  familyPreferences: FamilyPreferences;
}}
```

**💼 Habilita**: Gestão Familiar (Concept NAV 360)

---

[Continue com outras entidades relevantes]

---

**FIM DA PARTE 4**"""

        return self._call_api(prompt, "Parte 4 - Padrões e Integrações")
    
    def generate_part_5_roadmap_metrics(
        self,
        gap_analysis: str,
        concept_nav360: str
    ) -> str:
        """Parte 5: Roadmap, Métricas e Conclusão."""
        
        prompt = f"""# TAREFA: PARTE 5 - ROADMAP, MÉTRICAS E CONCLUSÃO

Gere as seções finais:
1. Capacidades Habilitadas (mapa Concept → TO-BE)
2. Estratégia de Evolução (roadmap macro em ondas)
3. Métricas de Sucesso
4. Riscos e Mitigações
5. Governança
6. Conclusão

---

## INPUTS (Resumo)

### Gaps Prioritários
{gap_analysis[:8000]}

### Funcionalidades NAV 360
{concept_nav360[:8000] if concept_nav360 else "N/A"}

---

## INSTRUÇÕES

Gere:

# 🎯 CAPACIDADES HABILITADAS

## Mapa: Decisões TO-BE → Funcionalidades Concept NAV 360

| Funcionalidade Concept | Decisões TO-BE Relacionadas | Status | Dependências |
|------------------------|----------------------------|--------|--------------|
| Hero Personalizado | Stack Node/NestJS, BFF Pattern, GraphQL | ✅ Viabilizado | - |
| Gestão Familiar | Modelo de Dados Family, APIs REST | ✅ Viabilizado | - |
| Busca Inteligente | Elasticsearch, ML Search | ✅ Viabilizado | - |
| Vitrine de Produtos | BFF, Catálogo de Serviços | ✅ Viabilizado | - |
| Calendário Vacinal | Integração SUS, Modelo VaccinationCalendar | ⚠️ Viabilizado | Integração SUS |
| NASI Centralizado | Data Lake, Integrações HL7/FHIR | ⚠️ Viabilizado | Múltiplas integrações |

**Legenda:**
- ✅ Plenamente Viabilizado (apenas decisões TO-BE)
- ⚠️ Parcialmente Viabilizado (depende de integrações externas)
- ❌ Não Viabilizado (requer análise adicional)

---

# 🚀 ESTRATÉGIA DE EVOLUÇÃO

## Abordagem: Evolução Incremental

**Princípio**: Não fazer "Big Bang". Evoluir gradualmente do AS-IS para o TO-BE.

## Roadmap Macro em Ondas

```mermaid
gantt
    title Evolução AS-IS → TO-BE
    dateFormat YYYY-MM
    section Onda 1: Fundação
    Padronização Stack (Node/NestJS) :2025-03, 2M
    Observabilidade Base :2025-04, 2M
    CI/CD Padronizado :2025-05, 1M
    
    section Onda 2: Capacidades Core
    BFF Pattern :2025-06, 2M
    APIs GraphQL :2025-07, 2M
    Gestão Familiar (MVP) :2025-08, 3M
    
    section Onda 3: Integrações
    Integração SUS (Calendário Vacinal) :2025-11, 2M
    NASI - Fase 1 :2026-01, 3M
    
    section Onda 4: Escala
    Expansão para Portfólio Completo :2026-04, 6M
```

---

## 🏗️ Onda 1: Fundação (Meses 1-4)

**🎯 Objetivo**: Resolver gaps críticos de baixo esforço (Quick Wins)

**📊 Apps Prioritárias**:
- [Lista de 3-5 apps para começar]

**📦 Entregas**:
1. **Padronização Stack**
   - Migrar apps selecionadas para Node.js 20 LTS + NestJS
   - Gap resolvido: Heterogeneidade tecnológica
   
2. **Observabilidade Base**
   - Implementar logging estruturado
   - APM básico (New Relic/Datadog)
   - Gap resolvido: Falta de observabilidade

3. **CI/CD Padronizado**
   - Pipeline GitLab CI padrão
   - Testes automatizados obrigatórios
   - Gap resolvido: Inconsistência em pipelines

**✅ Critérios de Sucesso**:
- X apps migradas com sucesso
- Observabilidade em 100% das apps migradas
- Pipeline CI/CD < 10min

---

## 🏗️ Onda 2: Capacidades Arquiteturais (Meses 5-8)

**🎯 Objetivo**: Implementar padrões que habilitam funcionalidades NAV 360

**📊 Apps Prioritárias**:
- Criação de novos BFFs (Web + Mobile)
- [Apps que vão consumir os BFFs]

**📦 Entregas**:
1. **BFF Pattern**
   - BFF para Web
   - BFF para Mobile
   - Habilita: Hero Personalizado, Experiência Diferenciada

2. **APIs GraphQL**
   - Substituir REST por GraphQL onde aplicável
   - Habilita: Busca Inteligente, Vitrine de Produtos

3. **Gestão Familiar MVP**
   - Modelo de dados Family
   - APIs de gestão de dependentes
   - Habilita: Gestão Familiar (Concept NAV 360)

**✅ Critérios de Sucesso**:
- BFFs em produção com 99.9% uptime
- 80% das APIs migradas para GraphQL
- MVP Gestão Familiar com 1000+ usuários

---

## 🏗️ Onda 3: Integrações Estratégicas (Meses 9-14)

**🎯 Objetivo**: Viabilizar funcionalidades que dependem de integrações externas

**📦 Entregas**:
1. **Integração SUS**
   - Calendário Vacinal
   - Habilita: Calendário Vacinal (Concept NAV 360)

2. **NASI - Fase 1**
   - Histórico de Exames
   - Histórico de Consultas
   - Habilita: NASI Centralizado (Concept NAV 360)

**✅ Critérios de Sucesso**:
- Integração SUS com 95% disponibilidade
- 10.000+ pacientes com histórico no NASI

---

## 🏗️ Onda 4: Escala e Otimização (Meses 15-20)

**🎯 Objetivo**: Expandir TO-BE para todo o portfólio

**📦 Entregas**:
- Migração das apps restantes
- Otimizações de performance
- Refinamentos baseados em feedback

---

# 📏 MÉTRICAS DE SUCESSO TO-BE

## Métricas Técnicas

| Métrica | AS-IS (Baseline) | TO-BE (Meta) | Prazo |
|---------|------------------|--------------|-------|
| Tempo de Load (p95) | 5s | < 2s | 12 meses |
| Disponibilidade | 99.5% | 99.9% | 12 meses |
| Cobertura de Testes | 30% | > 80% | 12 meses |
| Time to Market | 3 meses | < 1 mês | 12 meses |
| Incidentes/mês | 15 | < 5 | 12 meses |

## Métricas de Negócio (Concept NAV 360)

| Métrica | Baseline | Meta | Prazo |
|---------|----------|------|-------|
| Share de Agendamentos via Nav | 20% | 40% | 12 meses |
| Taxa de Conversão Novas Fichas | 2% | 5% | 6 meses |
| Adoção Gestão Familiar | 0% | 25% | 9 meses |
| NPS Plataforma | 45 | 60 | 12 meses |
| Tempo de Sessão | 3min | 7min | 12 meses |

---

# ⚠️ RISCOS E MITIGAÇÕES

## Riscos Técnicos

### Risco 1: Complexidade de Migração

**Descrição**: Migração de apps legadas pode ser mais complexa que estimado  
**Probabilidade**: Alta  
**Impacto**: Médio  
**Mitigação**:
- Começar por apps mais simples (Onda 1)
- POC detalhada antes de cada onda
- Squad de apoio para migrações

### Risco 2: Performance de Integrações Externas

**Descrição**: Integrações com SUS, operadoras podem ser lentas/instáveis  
**Probabilidade**: Alta  
**Impacto**: Alto  
**Mitigação**:
- Cache agressivo
- Circuit breaker pattern
- Experiência degradada aceitável

---

[Continue com outros riscos]

---

# 📋 GOVERNANÇA E PRÓXIMOS PASSOS

## Decisões Tomadas Neste TO-BE

✅ Stack: Node.js 20 LTS + NestJS  
✅ Padrão: BFF para Web e Mobile  
✅ APIs: GraphQL para queries complexas, REST para operações simples  
✅ Observabilidade: Stack unificada (logs + métricas + tracing)  
✅ Cloud: Containers Docker + Kubernetes  

## Decisões Pendentes

⏳ Escolha final de APM (New Relic vs Datadog vs Elastic APM)  
⏳ Estratégia de migração de dados legados  
⏳ Definição de SLAs por serviço  

## Próximos Passos (Próximos 30 Dias)

1. **Validar TO-BE com Stakeholders**
   - Apresentar para liderança técnica
   - Ajustar baseado em feedback
   - Obter buy-in das equipes

2. **Detalhar Onda 1**
   - Selecionar 3-5 apps para início
   - Criar roadmap detalhado
   - Estimar esforços granulares

3. **Setup de Infraestrutura**
   - Provisionar ambientes
   - Configurar observabilidade
   - Preparar pipelines CI/CD

---

# 🎯 CONCLUSÃO

## Resumo Executivo Final

Este Modelo TO-BE foi construído especificamente para:

1. **Resolver Gaps Reais**: Top 10 gaps identificados do portfólio atual
2. **Viabilizar Estratégia**: Funcionalidades do Concept NAV 360
3. **Ser Pragmático**: Evolução incremental, não reescrita total

**Principais Decisões:**
- Stack unificado em Node.js/NestJS
- BFF Pattern para experiências diferenciadas
- GraphQL para queries complexas
- Observabilidade como fundação
- Evolução em 4 ondas ao longo de 20 meses

**Valor Esperado:**
- Redução de 60% no time to market
- Aumento de 100% no share de agendamentos
- 99.9% de disponibilidade
- Plataforma preparada para escalar

## Alinhamento Estratégico

**✅ Gaps Resolvidos**: 47 de 50 gaps identificados (94%)  
**✅ Concept Viabilizado**: 8 de 8 funcionalidades (100%)  
**✅ ROI Esperado**: 3x em 24 meses

---

## Mensagem Final

Este TO-BE não é apenas um documento técnico - é um **plano de transformação acionável** 
que conecta problemas reais (gaps) com soluções específicas (decisões TO-BE) e 
objetivos de negócio (Concept NAV 360).

**Próximo passo crítico**: Validação com stakeholders e início da Onda 1.

---

**FIM DA PARTE 5**"""

        return self._call_api(prompt, "Parte 5 - Roadmap e Conclusão")
    
    def _call_api(self, prompt: str, part_name: str) -> str:
        """Chama a API do Claude."""
        try:
            print(f"   🤖 Gerando: {part_name}...")
            
            message = self.client.messages.create(
                model=MODEL,
                max_tokens=16000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = message.content[0].text
            print(f"   ✅ {part_name} concluída ({len(content):,} caracteres)")
            return content
            
        except Exception as e:
            print(f"   ❌ Erro ao gerar {part_name}: {e}")
            return f"\n\n# ⚠️ ERRO AO GERAR {part_name}\n\n{str(e)}\n\n"
    
    def consolidate_parts(self, parts: List[str], timestamp: str) -> Path:
        """Consolida todas as partes em um único documento."""
        print("\n📦 Consolidando partes em documento único...")
        
        # Remove marcadores de "FIM DA PARTE X"
        cleaned_parts = []
        for part in parts:
            cleaned = part.replace("**FIM DA PARTE", "<!-- FIM DA PARTE")
            cleaned = cleaned.replace("FIM DA PARTE", "<!-- FIM DA PARTE")
            cleaned_parts.append(cleaned)
        
        # Junta tudo
        full_document = "\n\n---\n\n".join(cleaned_parts)
        
        # Adiciona índice no início
        toc = """
# 📑 ÍNDICE

1. [Sumário Executivo](#-sumário-executivo)
2. [Arquitetura de Referência](#️-arquitetura-de-referência-to-be)
3. [Decisões Técnicas](#-decisões-técnicas)
4. [Padrões e Integrações](#-padrões-e-guidelines)
5. [Roadmap e Métricas](#-capacidades-habilitadas)

---

"""
        
        full_document = toc + full_document
        
        # Salva documento consolidado
        output_path = Path('outputs')
        output_path.mkdir(exist_ok=True)
        
        filename = f"TO_BE_Model_v3_Complete_{timestamp}.md"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_document)
        
        print(f"   ✅ Documento consolidado salvo: {filepath}")
        return filepath
    
    def generate(self):
        """Executa o processo completo de geração modular do TO-BE."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print("="*80)
        print("🎯 GERADOR DE MODELO TO-BE V3 - ABORDAGEM MODULAR")
        print("="*80)
        print("\n📌 ESTRATÉGIA:")
        print("   1. Gera TO-BE em 5 partes independentes")
        print("   2. Consolida tudo em documento final único")
        print("   3. Evita limite de tokens de saída")
        
        # 1. Carrega inputs
        print("\n📖 Carregando inputs...")
        
        gap_file = self.find_latest_gap_analysis()
        if not gap_file:
            print("❌ Gap Analysis não encontrada!")
            return
        print(f"   ✅ Gap Analysis: {gap_file.name}")
        
        with open(gap_file, 'r', encoding='utf-8') as f:
            gap_analysis = f.read()
        
        concept_file = self.find_concept_nav360()
        concept_nav360 = None
        if concept_file:
            print(f"   ✅ Concept NAV 360: {concept_file.name}")
            with open(concept_file, 'r', encoding='utf-8') as f:
                concept_nav360 = f.read()
        else:
            print("   ⚠️  Concept NAV 360 não encontrado")
        
        blueprints = self.load_all_blueprints()
        portfolio_stats = {
            'total_projects': len(blueprints),
            'total_apps': sum(len(apps) for apps in blueprints.values()),
            'projects': list(blueprints.keys())
        }
        print(f"   ✅ Blueprints: {portfolio_stats['total_apps']} apps")
        
        # 2. Gera partes
        print(f"\n🔧 Gerando TO-BE em partes...")
        parts = []
        
        # Parte 1: Sumário
        parts.append(self.generate_part_1_executive_summary(
            gap_analysis, concept_nav360, portfolio_stats
        ))
        
        # Parte 2: Arquitetura
        parts.append(self.generate_part_2_architecture(
            gap_analysis, concept_nav360
        ))
        
        # Parte 3: Decisões Técnicas (múltiplas sub-partes)
        decision_areas = ['stack', 'architecture', 'apis', 'observability', 'data']
        for area in decision_areas:
            parts.append(self.generate_part_3_tech_decisions(
                gap_analysis, concept_nav360, area
            ))
        
        # Parte 4: Padrões e Integrações
        parts.append(self.generate_part_4_patterns_integrations(
            gap_analysis, concept_nav360
        ))
        
        # Parte 5: Roadmap e Conclusão
        parts.append(self.generate_part_5_roadmap_metrics(
            gap_analysis, concept_nav360
        ))
        
        # 3. Consolida
        filepath = self.consolidate_parts(parts, timestamp)
        
        # 4. Estatísticas
        with open(filepath, 'r', encoding='utf-8') as f:
            full_content = f.read()
        
        print("\n" + "="*80)
        print("✅ TO-BE V3 GERADO COM SUCESSO!")
        print("="*80)
        
        print(f"\n📄 Arquivo: {filepath}")
        print(f"📊 Tamanho total: {len(full_content):,} caracteres")
        print(f"📦 Partes geradas: {len(parts)}")
        print(f"📏 Seções principais: ~{full_content.count('##')}")
        
        print(f"\n📖 PRÓXIMOS PASSOS:")
        print(f"   1. ✅ Revisar documento completo")
        print(f"   2. ✅ Validar com stakeholders")
        print(f"   3. ⏭️  Executar: roadmap_generator_v2.py")


def main():
    """Função principal."""
    if not ANTHROPIC_API_KEY:
        print("❌ ERRO: ANTHROPIC_API_KEY não configurada!")
        return
    
    try:
        generator = ToBeGeneratorV3()
        generator.generate()
    
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()