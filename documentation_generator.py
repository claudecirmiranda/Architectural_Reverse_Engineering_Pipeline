import json
import os
from typing import Dict, List, Set
from collections import defaultdict
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# =============================================================================
# Paths & Env
# =============================================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")

OUTPUT_BASE = BASE_DIR / OUTPUT_DIR
OUTPUT_JSON = OUTPUT_BASE / "json"
OUTPUT_REPORTS = OUTPUT_BASE / "reports"
OUTPUT_DIAGRAMS = OUTPUT_BASE / "diagrams"
OUTPUT_REPOS = OUTPUT_REPORTS / "repos"

OUTPUT_JSON.mkdir(parents=True, exist_ok=True)
OUTPUT_REPORTS.mkdir(parents=True, exist_ok=True)
OUTPUT_DIAGRAMS.mkdir(parents=True, exist_ok=True)
OUTPUT_REPOS.mkdir(parents=True, exist_ok=True)

# =============================================================================
# Gerador de README.md para Repositórios
# =============================================================================

def generate_repo_readme(repo: Dict, project_name: str, layer_data: Dict = None, integration_data: Dict = None) -> str:
    """Gera README.md completo para um repositório"""
    
    name = repo["name"]
    language = repo["analysis"]["language"]
    frameworks = ", ".join(repo["analysis"]["frameworks"])
    project_types = ", ".join(repo["analysis"]["project_types"])
    
    # Buscar dados de camadas
    layer_info = None
    if layer_data:
        for proj in layer_data.get("projects", []):
            for r in proj.get("repos", []):
                if r["name"] == name:
                    layer_info = r
                    break
    
    # Buscar dados de integração
    integration_info = None
    if integration_data:
        for proj in integration_data.get("projects", []):
            for r in proj.get("repos", []):
                if r["name"] == name:
                    integration_info = r
                    break
    
    # Criar README
    readme = f"""# {name}

> **Projeto:** {project_name}  
> **Linguagem:** {language}  
> **Framework:** {frameworks}  
> **Tipo:** {project_types}

---

## 📋 Visão Geral

{generate_overview(repo, layer_info)}

---

## 🏗️ Arquitetura

### Stack Tecnológico

**Runtime:**
"""
    
    # Dependências
    deps = repo["analysis"]["dependencies"]
    if deps.get("runtime"):
        for dep in deps["runtime"][:10]:
            readme += f"- `{dep}`\n"
    else:
        readme += "- Nenhuma dependência runtime detectada\n"
    
    readme += "\n**Build & Dev:**\n"
    if deps.get("dev"):
        for dep in deps["dev"][:8]:
            readme += f"- `{dep}`\n"
    else:
        readme += "- Nenhuma dependência dev detectada\n"
    
    # Build System
    readme += f"\n### Build System\n\n"
    for bs in repo["analysis"]["build_systems"]:
        readme += f"- {bs}\n"
    
    # Estrutura de camadas
    if layer_info and layer_info.get("layer_summary"):
        readme += "\n### Camadas Arquiteturais\n\n"
        readme += "| Camada | Arquivos |\n"
        readme += "|--------|----------|\n"
        for layer, count in sorted(layer_info["layer_summary"].items(), key=lambda x: x[1], reverse=True):
            readme += f"| {layer.title()} | {count} |\n"
        
        if layer_info.get("architecture_patterns"):
            readme += f"\n**Padrões Detectados:** {', '.join(layer_info['architecture_patterns'])}\n"
    
    # Estatísticas
    if layer_info and layer_info.get("statistics"):
        stats = layer_info["statistics"]
        readme += "\n### Estatísticas\n\n"
        readme += f"- 🔧 **Classes:** {stats['total_classes']}\n"
        if stats['total_routes'] > 0:
            readme += f"- 🌐 **Rotas REST:** {stats['total_routes']}\n"
        if stats['total_graphql'] > 0:
            readme += f"- ⚡ **GraphQL Operations:** {stats['total_graphql']}\n"
        readme += f"- 📦 **Controllers:** {stats['controllers']}\n"
        readme += f"- ⚙️ **Services:** {stats['services']}\n"
        if stats['repositories'] > 0:
            readme += f"- 💾 **Repositories:** {stats['repositories']}\n"
    
    # Estrutura de pastas
    folder_struct = repo["analysis"]["folder_structure"]
    readme += "\n### Estrutura do Projeto\n\n"
    readme += f"- {'✅' if folder_struct['has_src'] else '❌'} Pasta `src/`\n"
    readme += f"- {'✅' if folder_struct['has_tests'] else '❌'} Testes\n"
    readme += f"- {'✅' if folder_struct['has_docs'] else '❌'} Documentação\n"
    readme += f"- {'✅' if folder_struct['has_ci_cd'] else '❌'} CI/CD\n"
    readme += f"- {'✅' if folder_struct['has_docker'] else '❌'} Docker\n"
    
    # Integrações
    if integration_info and integration_info.get("integrations"):
        readme += "\n---\n\n## 🔗 Integrações\n\n"
        
        integrations = integration_info["integrations"]
        
        if "authentication" in integrations:
            readme += "### 🔐 Autenticação\n\n"
            for item in integrations["authentication"]:
                readme += f"- {item['technology']}\n"
        
        if "databases" in integrations:
            readme += "\n### 💾 Bancos de Dados\n\n"
            for item in integrations["databases"]:
                readme += f"- {item['technology']}\n"
        
        if "message_queues" in integrations:
            readme += "\n### 📨 Mensageria\n\n"
            for item in integrations["message_queues"]:
                readme += f"- {item['technology']}\n"
        
        if "cloud_services" in integrations:
            readme += "\n### ☁️ Cloud Services\n\n"
            for item in integrations["cloud_services"]:
                readme += f"- {item['technology']}\n"
        
        if "graphql" in integrations:
            readme += "\n### ⚡ GraphQL\n\n"
            for item in integrations["graphql"]:
                readme += f"- {item['technology']}\n"
    
    # API Documentation
    if layer_info and layer_info.get("routes"):
        readme += "\n---\n\n## 📚 API Endpoints\n\n"
        
        # Agrupar por método
        routes_by_method = defaultdict(list)
        for route in layer_info["routes"][:30]:  # Top 30
            routes_by_method[route["method"]].append(route["path"])
        
        for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            if method in routes_by_method:
                readme += f"### {method}\n\n"
                for path in sorted(set(routes_by_method[method]))[:10]:
                    readme += f"- `{method} {path}`\n"
                readme += "\n"
    
    # GraphQL Operations
    if layer_info and layer_info.get("graphql_operations"):
        readme += "### GraphQL Operations\n\n"
        
        ops_by_type = defaultdict(list)
        for op in layer_info["graphql_operations"]:
            ops_by_type[op["type"]].append(op["name"])
        
        if "Query" in ops_by_type:
            readme += "**Queries:**\n"
            for name in sorted(set(ops_by_type["Query"]))[:10]:
                readme += f"- `{name}`\n"
            readme += "\n"
        
        if "Mutation" in ops_by_type:
            readme += "**Mutations:**\n"
            for name in sorted(set(ops_by_type["Mutation"]))[:10]:
                readme += f"- `{name}`\n"
            readme += "\n"
    
    # Getting Started
    readme += "---\n\n## 🚀 Como Começar\n\n"
    readme += "### Pré-requisitos\n\n"
    
    if language == "Node.js/TypeScript":
        readme += "- Node.js 18+\n"
        readme += "- npm ou yarn\n"
    elif language == "Java":
        readme += "- Java 17+\n"
        readme += "- Maven ou Gradle\n"
    elif language == ".NET":
        readme += "- .NET 6+\n"
    elif language == "Python":
        readme += "- Python 3.9+\n"
        readme += "- pip\n"
    
    if folder_struct['has_docker']:
        readme += "- Docker & Docker Compose\n"
    
    readme += "\n### Instalação\n\n"
    
    if language == "Node.js/TypeScript":
        readme += "```bash\n"
        readme += "# Instalar dependências\n"
        readme += "npm install\n\n"
        readme += "# Configurar variáveis de ambiente\n"
        readme += "cp .env.example .env\n\n"
        readme += "# Rodar em desenvolvimento\n"
        readme += "npm run start:dev\n"
        readme += "```\n"
    elif language == "Java":
        readme += "```bash\n"
        readme += "# Build com Maven\n"
        readme += "mvn clean install\n\n"
        readme += "# Rodar aplicação\n"
        readme += "mvn spring-boot:run\n"
        readme += "```\n"
    
    if folder_struct['has_docker']:
        readme += "\n### Docker\n\n"
        readme += "```bash\n"
        readme += "# Build imagem\n"
        readme += f"docker build -t {name} .\n\n"
        readme += "# Rodar container\n"
        readme += f"docker run -p 3000:3000 {name}\n"
        readme += "```\n"
    
    # Testes
    if folder_struct['has_tests']:
        readme += "\n### Testes\n\n"
        if language == "Node.js/TypeScript":
            readme += "```bash\n"
            readme += "# Rodar testes\n"
            readme += "npm test\n\n"
            readme += "# Cobertura\n"
            readme += "npm run test:cov\n"
            readme += "```\n"
    
    # Variáveis de ambiente
    if integration_info and integration_info.get("integrations", {}).get("environment_config"):
        readme += "\n---\n\n## ⚙️ Configuração\n\n"
        readme += "### Variáveis de Ambiente\n\n"
        
        env_vars = integration_info["integrations"]["environment_config"]
        for var in sorted(set([v["variable"] for v in env_vars]))[:20]:
            readme += f"- `{var}`\n"
    
    # Links úteis
    readme += "\n---\n\n## 🔗 Links Úteis\n\n"
    readme += f"- [Repositório no Azure DevOps]({repo['url']})\n"
    
    if folder_struct['has_ci_cd']:
        readme += "- Pipeline CI/CD configurado\n"
    
    # Footer
    readme += "\n---\n\n"
    readme += f"**Branch padrão:** `{repo['default_branch']}`  \n"
    readme += f"**Última atualização:** {repo.get('last_updated', 'N/A')}  \n"
    readme += "\n*Documentação gerada automaticamente*\n"
    
    return readme


def generate_overview(repo: Dict, layer_info: Dict = None) -> str:
    """Gera descrição overview do repositório"""
    
    name = repo["name"]
    project_types = repo["analysis"]["project_types"]
    
    overview = ""
    
    # Tipo de projeto
    if "API/Backend" in project_types:
        overview += "Serviço backend que expõe APIs REST"
        if layer_info and layer_info.get("statistics", {}).get("total_graphql", 0) > 0:
            overview += " e GraphQL"
        overview += " para consumo por aplicações front-end e mobile.\n\n"
    
    elif "Frontend/SPA" in project_types:
        overview += "Aplicação front-end single-page construída em React.\n\n"
    
    elif "Library/SDK" in project_types:
        overview += "Biblioteca compartilhada utilizada por outros serviços da plataforma.\n\n"
    
    elif "Worker/Background Job" in project_types:
        overview += "Serviço de processamento assíncrono e jobs em background.\n\n"
    
    else:
        overview += f"Componente do tipo {', '.join(project_types)}.\n\n"
    
    # Adicionar contexto
    if "-bff" in name:
        overview += "Este é um **Backend for Frontend (BFF)** que agrega múltiplos serviços downstream "
        overview += "e fornece uma API otimizada para as necessidades específicas do cliente.\n\n"
    
    if "gateway" in name.lower():
        overview += "Atua como **API Gateway** centralizando o acesso aos microserviços da plataforma.\n\n"
    
    if "lib-" in name or "library" in name.lower():
        overview += "Fornece funcionalidades reutilizáveis como autenticação, cache, logging, etc.\n\n"
    
    return overview


# =============================================================================
# Gerador de Dependency Graph
# =============================================================================

def generate_dependency_graph_file(scan_data: Dict) -> str:
    """Gera arquivo Mermaid com grafo de dependências"""
    
    mermaid = """graph LR
    %% Dependency Graph - NPM Packages
    
    classDef runtime fill:#4caf50,stroke:#2e7d32,color:#fff
    classDef dev fill:#2196f3,stroke:#1565c0,color:#fff
    classDef shared fill:#ff9800,stroke:#e65100
    
"""
    
    # Coletar todas as dependências
    all_deps = defaultdict(set)
    
    for project in scan_data["projects"]:
        for repo in project["repos"]:
            deps = repo["analysis"]["dependencies"]
            
            # Runtime
            for dep in deps.get("runtime", [])[:20]:
                all_deps["runtime"].add(dep)
            
            # Dev
            for dep in deps.get("dev", [])[:15]:
                all_deps["dev"].add(dep)
    
    # Top packages mais usados
    dep_count = defaultdict(int)
    for project in scan_data["projects"]:
        for repo in project["repos"]:
            for dep in repo["analysis"]["dependencies"].get("runtime", []):
                dep_count[dep] += 1
    
    top_deps = sorted(dep_count.items(), key=lambda x: x[1], reverse=True)[:15]
    
    mermaid += "    %% Top Shared Dependencies\n"
    for dep, count in top_deps:
        clean = dep.replace("@", "").replace("/", "_").replace("-", "_")
        mermaid += f"    {clean}[\"{dep}<br/>({count} repos)\"]:::runtime\n"
    
    return mermaid


# =============================================================================
# Gerador de Onboarding Guide
# =============================================================================

def generate_onboarding_guide(scan_data: Dict, integration_data: Dict, layer_data: Dict) -> str:
    """Gera guia de onboarding para novos desenvolvedores"""
    
    guide = """# 🚀 Guia de Onboarding - Nav Paciente Platform

Bem-vindo ao time! Este guia vai te ajudar a entender a arquitetura e começar a contribuir rapidamente.

---

## 📋 Índice

1. [Visão Geral da Plataforma](#visao-geral)
2. [Arquitetura](#arquitetura)
3. [Stack Tecnológica](#stack)
4. [Estrutura de Repositórios](#repositorios)
5. [Setup do Ambiente](#setup)
6. [Fluxo de Desenvolvimento](#fluxo)
7. [Padrões e Convenções](#padroes)
8. [Links Úteis](#links)

---

## 🎯 Visão Geral da Plataforma {#visao-geral}

**Nav Paciente** é uma plataforma de saúde digital que permite:
- Agendamento de exames
- Visualização de resultados
- Gestão de convênios
- Notificações em tempo real

### Números da Plataforma

"""
    
    total_repos = sum(p["total_repos"] for p in scan_data["projects"])
    total_integrations = integration_data.get("total_integrations", 0)
    
    guide += f"- **{total_repos}** repositórios\n"
    guide += f"- **{total_integrations}** integrações\n"
    
    # Contar por tipo
    bffs = len([r for p in scan_data["projects"] for r in p["repos"] if "-bff" in r["name"]])
    services = len([r for p in scan_data["projects"] for r in p["repos"] if "services-api" in r["name"]])
    libs = len([r for p in scan_data["projects"] for r in p["repos"] if "lib-" in r["name"]])
    
    guide += f"- **{bffs}** BFFs (Backend for Frontend)\n"
    guide += f"- **{services}** Microserviços\n"
    guide += f"- **{libs}** Bibliotecas compartilhadas\n"
    
    guide += """

---

## 🏗️ Arquitetura {#arquitetura}

### Camadas da Aplicação

```
┌─────────────────────────────────────┐
│     Frontend (React/React Native)   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Apollo Gateway (GraphQL)       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         BFF Layer (NestJS)          │
│  - Account BFF                      │
│  - Scheduling BFF                   │
│  - Exam Results BFF                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Microservices (NestJS)         │
│  - Declarations                     │
│  - Events                           │
│  - Patient Config                   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Data Layer                  │
│  - PostgreSQL                       │
│  - Redis Cache                      │
│  - Azure Service Bus                │
└─────────────────────────────────────┘
```

### Padrões Arquiteturais

"""
    
    # Coletar padrões mais comuns
    if layer_data:
        pattern_count = defaultdict(int)
        for project in layer_data.get("projects", []):
            for repo in project.get("repos", []):
                for pattern in repo.get("architecture_patterns", []):
                    pattern_count[pattern] += 1
        
        for pattern, count in sorted(pattern_count.items(), key=lambda x: x[1], reverse=True)[:5]:
            guide += f"- **{pattern}** ({count} repositórios)\n"
    
    guide += """

---

## 💻 Stack Tecnológica {#stack}

### Backend
- **Runtime:** Node.js 18+
- **Framework:** NestJS (Express)
- **Linguagem:** TypeScript
- **API:** GraphQL (Apollo Federation) + REST

### Frontend
- **Framework:** React 18
- **Mobile:** React Native + Expo
- **State:** Apollo Client + Zustand
- **UI:** Design System proprietário

### Dados
- **Database:** PostgreSQL
- **Cache:** Redis
- **Message Queue:** Azure Service Bus
- **Storage:** Azure Blob Storage

### Infraestrutura
- **Cloud:** Azure
- **Containers:** Docker + Kubernetes (AKS)
- **CI/CD:** Azure Pipelines
- **Monitoring:** Dynatrace + Elastic APM

### Autenticação
- **SSO:** Keycloak (4 realms)
- **Tokens:** JWT
- **Protocols:** OAuth2 / OpenID Connect

---

## 📦 Estrutura de Repositórios {#repositorios}

### BFFs (Backend for Frontend)

"""
    
    # Listar principais BFFs
    for project in scan_data["projects"]:
        for repo in project["repos"]:
            if "-bff" in repo["name"]:
                guide += f"- **{repo['name']}**: "
                overview = repo['name'].replace('npac-', '').replace('-api-bff', '')
                guide += f"{overview.title()}\n"
    
    guide += "\n### Microserviços\n\n"
    
    # Listar principais services
    for project in scan_data["projects"]:
        for repo in project["repos"]:
            if "services-api" in repo["name"] and not repo['name'].endswith('-deployment'):
                guide += f"- **{repo['name']}**\n"
    
    guide += "\n### Bibliotecas Compartilhadas\n\n"
    
    # Listar libs
    for project in scan_data["projects"]:
        for repo in project["repos"]:
            if "lib-" in repo["name"]:
                lib_name = repo['name'].replace('npac-services-lib-', '')
                guide += f"- **{lib_name}**: "
                if lib_name == "auth":
                    guide += "Autenticação e autorização\n"
                elif lib_name == "cache":
                    guide += "Cliente Redis\n"
                elif lib_name == "requests":
                    guide += "HTTP client wrapper\n"
                elif lib_name == "utils":
                    guide += "Utilitários comuns\n"
                else:
                    guide += "\n"
    
    guide += """

---

## 🛠️ Setup do Ambiente {#setup}

### 1. Ferramentas Necessárias

```bash
# Node.js
nvm install 18
nvm use 18

# Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Docker
# Instalar Docker Desktop

# Git
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@dasa.com.br"
```

### 2. Acesso aos Sistemas

- [ ] Azure DevOps
- [ ] Keycloak (credenciais de dev)
- [ ] Azure Portal
- [ ] Dynatrace
- [ ] Confluence/Wiki da equipe

### 3. Clonar Repositório

```bash
# Exemplo: BFF de agendamento
git clone https://dasadevops@dev.azure.com/dasadevops/nav-paciente-servicos/_git/npac-scheduling-api-bff

cd npac-scheduling-api-bff
npm install
cp .env.example .env
npm run start:dev
```

### 4. Configurar Variáveis de Ambiente

Principais variáveis:
- `KEYCLOAK_*_URL`: URLs dos realms
- `REDIS_HOST`: Endereço do Redis
- `POSTGRES_*`: Conexão com banco
- `*_API_URL`: URLs dos serviços downstream

---

## 🔄 Fluxo de Desenvolvimento {#fluxo}

### Branching Strategy

```
main (produção)
  ├── develop (homologação)
  │   ├── feature/TICKET-123-nova-funcionalidade
  │   └── bugfix/TICKET-456-corrigir-bug
```

### Workflow

1. **Criar branch** a partir de `develop`
   ```bash
   git checkout develop
   git pull
   git checkout -b feature/TICKET-123-descricao
   ```

2. **Desenvolver** seguindo os padrões

3. **Testar localmente**
   ```bash
   npm test
   npm run test:e2e
   ```

4. **Commit** seguindo Conventional Commits
   ```bash
   git commit -m "feat(scheduling): adicionar validação de horário"
   ```

5. **Push e Pull Request**
   ```bash
   git push origin feature/TICKET-123-descricao
   # Criar PR no Azure DevOps
   ```

6. **Code Review** → Merge → Deploy automático

---

## 📏 Padrões e Convenções {#padroes}

### Estrutura de Pastas (NestJS)

```
src/
├── app.module.ts
├── main.ts
├── config/           # Configurações
├── controllers/      # Controllers REST
├── resolvers/        # Resolvers GraphQL
├── services/         # Lógica de negócio
├── repositories/     # Acesso a dados
├── entities/         # Modelos do banco
├── dtos/             # Data Transfer Objects
├── guards/           # Autenticação/Autorização
├── interceptors/     # AOP
└── utils/            # Utilitários
```

### Nomenclatura

- **Classes**: PascalCase (`UserService`)
- **Arquivos**: kebab-case (`user.service.ts`)
- **Variáveis**: camelCase (`userName`)
- **Constantes**: UPPER_SNAKE_CASE (`API_URL`)

### Code Style

- ESLint + Prettier configurados
- Máximo 100 caracteres por linha
- Sempre usar TypeScript (não any!)
- Testes obrigatórios para features

---

## 🔗 Links Úteis {#links}

### Documentação
- [Confluence da Equipe](https://link-do-confluence)
- [Diagramas de Arquitetura](./ARCHITECTURE.md)
- [API Gateway](https://gateway.nav.dasa.com.br/graphql)

### Ferramentas
- [Azure DevOps](https://dev.azure.com/dasadevops)
- [Dynatrace](https://link-dynatrace)
- [Keycloak Admin](https://keycloak.dasa.com.br)

### Comunicação
- Slack: #nav-paciente-dev
- Daily: 9h30 (Teams)
- Sprint Planning: Segundas 14h

---

## 🆘 Precisa de Ajuda?

- **Tech Lead**: [nome@dasa.com.br]
- **Arquiteto**: [nome@dasa.com.br]
- **Scrum Master**: [nome@dasa.com.br]

Bem-vindo ao time! 🚀

---

*Última atualização: """ + scan_data.get('scan_date', 'N/A') + "*\n"
    
    return guide


# =============================================================================
# Main - Gerador Principal
# =============================================================================

def main():
    print("📝 Gerador de Documentação Automática")
    print("="*60)
    
    # Carregar dados
    scanner_file = OUTPUT_JSON / "azure_scanner.json"
    integration_file = OUTPUT_JSON / "integration_map.json"
    layer_file = OUTPUT_JSON / "layer_analysis.json"

    if not scanner_file.exists():
        print("❌ azure_scanner.json não encontrado!")
        return

    with open(scanner_file, "r", encoding="utf-8") as f:
        scan_data = json.load(f)

    integration_data = {}
    if integration_file.exists():
        with open(integration_file, "r", encoding="utf-8") as f:
            integration_data = json.load(f)

    layer_data = {}
    if layer_file.exists():
        with open(layer_file, "r", encoding="utf-8") as f:
            layer_data = json.load(f)
    
    print("✅ Dados carregados\n")
    
    # Criar pasta de docs
    docs_dir = OUTPUT_REPORTS
    repos_dir = OUTPUT_REPOS
    
    # 1. Gerar README para cada repositório
    print("📄 Gerando READMEs para repositórios...")
    repo_count = 0
    
    for project in scan_data["projects"]:
        for repo in project["repos"]:
            # Pular repos vazios
            if repo["analysis"]["language"] == "Unknown":
                continue
            
            readme = generate_repo_readme(repo, project["name"], layer_data, integration_data)
            
            filename = repos_dir / f"{repo['name']}_README.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(readme)

            repo_count += 1
    
    print(f"   ✅ {repo_count} READMEs gerados\n")
    
    # 2. Gerar Dependency Graph
    print("📊 Gerando grafo de dependências...")
    dep_graph = generate_dependency_graph_file(scan_data)
        
    with open(OUTPUT_DIAGRAMS / "dependency_graph.mmd", "w", encoding="utf-8") as f:
        f.write(dep_graph)
            
    print("   ✅ Grafo salvo em dependency_graph.mmd\n")
    
    # 3. Gerar Onboarding Guide
    print("🚀 Gerando guia de onboarding...")
    onboarding = generate_onboarding_guide(scan_data, integration_data, layer_data)
        
    with open(OUTPUT_REPORTS / "ONBOARDING.md", "w", encoding="utf-8") as f:
        f.write(onboarding)
                
    print("   ✅ Guia salvo em ONBOARDING.md\n")
    
    # 4. Gerar índice
    print("📑 Gerando índice de documentação...")
    index = generate_documentation_index(scan_data, repo_count)
    with open(f"{docs_dir}/INDEX.md", "w", encoding="utf-8") as f:
        f.write(index)
    print("   ✅ Índice salvo em INDEX.md\n")
    
    print("="*60)
    print("✅ Documentação gerada com sucesso!")
    print(f"📁 Localização: {docs_dir}/")
    print("="*60)
    print("\n📚 Arquivos gerados:")
    print(f"   - INDEX.md (índice geral)")
    print(f"   - ONBOARDING.md (guia de onboarding)")
    print(f"   - dependency_graph.mmd (grafo de dependências)")
    print(f"   - repos/*.md ({repo_count} READMEs individuais)")


def generate_documentation_index(scan_data: Dict, repo_count: int) -> str:
    """Gera índice principal da documentação"""
    
    index = f"""# 📚 Índice de Documentação - Nav Paciente Platform

**Organização:** {scan_data['organization']}  
**Última atualização:** {scan_data['scan_date']}  
**Total de repositórios:** {repo_count}

---

## 🎯 Documentos Principais

1. **[ONBOARDING.md](./ONBOARDING.md)** - Guia de onboarding para novos desenvolvedores
2. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Documentação completa da arquitetura
3. **[dependency_graph.mmd](./dependency_graph.mmd)** - Grafo de dependências entre pacotes

---

## 📦 Documentação por Repositório

### Backend - BFFs

"""
    
    # Listar BFFs
    for project in scan_data["projects"]:
        for repo in project["repos"]:
            if "-bff" in repo["name"] and repo["analysis"]["language"] != "Unknown":
                index += f"- [{repo['name']}](./repos/{repo['name']}_README.md)\n"
    
    index += "\n### Backend - Microserviços\n\n"
    
    # Listar services
    for project in scan_data["projects"]:
        for repo in project["repos"]:
            if "services-api" in repo["name"] and repo["analysis"]["language"] != "Unknown":
                index += f"- [{repo['name']}](./repos/{repo['name']}_README.md)\n"
    
    index += "\n### Bibliotecas Compartilhadas\n\n"
    
    # Listar libs
    for project in scan_data["projects"]:
        for repo in project["repos"]:
            if "lib-" in repo["name"] and repo["analysis"]["language"] != "Unknown":
                index += f"- [{repo['name']}](./repos/{repo['name']}_README.md)\n"
    
    index += "\n### Frontend\n\n"
    
    # Listar frontend
    for project in scan_data["projects"]:
        for repo in project["repos"]:
            if ("front" in repo["name"] or "app" in repo["name"]) and repo["analysis"]["language"] != "Unknown":
                index += f"- [{repo['name']}](./repos/{repo['name']}_README.md)\n"
    
    index += "\n### Utilitários\n\n"
    
    # Listar utilities
    for project in scan_data["projects"]:
        for repo in project["repos"]:
            if repo["name"].startswith("lkst-") and repo["analysis"]["language"] != "Unknown":
                index += f"- [{repo['name']}](./repos/{repo['name']}_README.md)\n"
    
    index += """

---

## 🔍 Como Usar Esta Documentação

### Para Novos Desenvolvedores
1. Comece pelo [ONBOARDING.md](./ONBOARDING.md)
2. Leia a [ARCHITECTURE.md](./ARCHITECTURE.md) para entender a estrutura
3. Escolha um repositório e leia seu README específico

### Para Desenvolvedores Experientes
- Use o índice acima para navegar diretamente aos READMEs
- Consulte os diagramas de arquitetura para visão geral
- Use o grafo de dependências para entender integrações

### Para Arquitetos
- Revise os padrões arquiteturais identificados
- Analise as integrações e dependências
- Valide a consistência entre repositórios

---

## 🔄 Mantendo Atualizado

Esta documentação foi **gerada automaticamente** através de análise estática do código.

Para regenerar:
```bash
python auto_documentation_generator.py
```

---

*Gerado automaticamente em """ + scan_data['scan_date'] + "*\n"
    
    return index


if __name__ == "__main__":
    main()