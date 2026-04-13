import os
import re
import json
import base64
import requests
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict

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

OUTPUT_JSON.mkdir(parents=True, exist_ok=True)
OUTPUT_REPORTS.mkdir(parents=True, exist_ok=True)

# =============================================================================
# Config
# =============================================================================
AZDO_ORG = os.getenv("AZDO_ORG")
AZDO_PAT = os.getenv("AZDO_PAT")
BASE_URL = f"https://dev.azure.com/{AZDO_ORG}"
HEADERS = {
    "Authorization": "Basic " + base64.b64encode(f":{AZDO_PAT}".encode()).decode()
}

CODE_EXTENSIONS = [".ts", ".js", ".tsx", ".jsx"]

# Padrões de detecção de camadas
LAYER_PATTERNS = {
    "controllers": [
        r"@Controller\(",
        r"@RestController",
        r"class\s+\w+Controller",
        r"\.controller\.",
        r"export\s+class\s+\w+Controller",
    ],
    "services": [
        r"@Injectable\(",
        r"@Service",
        r"class\s+\w+Service",
        r"\.service\.",
        r"export\s+class\s+\w+Service",
    ],
    "repositories": [
        r"@Repository",
        r"class\s+\w+Repository",
        r"\.repository\.",
        r"export\s+class\s+\w+Repository",
        r"@InjectRepository",
    ],
    "entities": [
        r"@Entity\(",
        r"class\s+\w+Entity",
        r"\.entity\.",
        r"export\s+class\s+\w+Entity",
    ],
    "dtos": [
        r"class\s+\w+Dto",
        r"\.dto\.",
        r"export\s+class\s+\w+Dto",
        r"export\s+interface\s+\w+Dto",
    ],
    "models": [
        r"class\s+\w+Model",
        r"\.model\.",
        r"export\s+class\s+\w+Model",
        r"export\s+interface\s+\w+Model",
    ],
    "resolvers": [
        r"@Resolver\(",
        r"class\s+\w+Resolver",
        r"\.resolver\.",
        r"export\s+class\s+\w+Resolver",
    ],
    "guards": [
        r"@Injectable\(\).*Guard",
        r"class\s+\w+Guard",
        r"\.guard\.",
        r"implements\s+CanActivate",
    ],
    "middlewares": [
        r"@Injectable\(\).*Middleware",
        r"class\s+\w+Middleware",
        r"\.middleware\.",
        r"implements\s+NestMiddleware",
    ],
    "interceptors": [
        r"@Injectable\(\).*Interceptor",
        r"class\s+\w+Interceptor",
        r"\.interceptor\.",
        r"implements\s+NestInterceptor",
    ],
    "pipes": [
        r"class\s+\w+Pipe",
        r"\.pipe\.",
        r"implements\s+PipeTransform",
    ],
    "validators": [
        r"class\s+\w+Validator",
        r"\.validator\.",
        r"@ValidatorConstraint",
    ],
    "use_cases": [
        r"class\s+\w+UseCase",
        r"\.use-case\.",
        r"\.usecase\.",
    ],
}

# Padrões de rotas e endpoints
ROUTE_PATTERNS = [
    r"@Get\(['\"]([^'\"]+)",
    r"@Post\(['\"]([^'\"]+)",
    r"@Put\(['\"]([^'\"]+)",
    r"@Delete\(['\"]([^'\"]+)",
    r"@Patch\(['\"]([^'\"]+)",
    r"router\.get\(['\"]([^'\"]+)",
    r"router\.post\(['\"]([^'\"]+)",
    r"app\.get\(['\"]([^'\"]+)",
    r"app\.post\(['\"]([^'\"]+)",
]

# Padrões de queries e mutations GraphQL
GRAPHQL_PATTERNS = [
    r"@Query\(\s*\(\)\s*=>\s*(\w+)",
    r"@Mutation\(\s*\(\)\s*=>\s*(\w+)",
    r"@Subscription\(\s*\(\)\s*=>\s*(\w+)",
]


# =============================================================================
# Helpers
# =============================================================================
def az_get(url: str, params: Optional[Dict] = None) -> Optional[Dict]:
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code not in [200, 201]:
            return None
        return r.json()
    except:
        return None


def get_default_branch(project: str, repo_id: str) -> str:
    url = f"{BASE_URL}/{project}/_apis/git/repositories/{repo_id}"
    data = az_get(url, {"api-version": "7.0"})
    if data and "defaultBranch" in data and data["defaultBranch"]:
        return data["defaultBranch"].replace("refs/heads/", "")
    return "main"


def fetch_file_content(project: str, repo_id: str, path: str, branch: str) -> Optional[str]:
    if not path.startswith("/"):
        path = f"/{path}"
    
    url = f"{BASE_URL}/{project}/_apis/git/repositories/{repo_id}/items"
    params = {"path": path, "download": "true", "api-version": "7.0"}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code == 200 and r.text:
            return r.text
    except:
        pass
    
    params = {
        "path": path,
        "includeContent": "true",
        "versionDescriptor.versionType": "branch",
        "versionDescriptor.version": branch,
        "api-version": "7.0",
    }
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if "content" in data:
                return data["content"]
            return r.text
    except:
        pass
    
    return None


def list_code_files(project: str, repo_id: str, path: str = "/", max_depth: int = 5, current_depth: int = 0) -> List[str]:
    """Lista arquivos de código recursivamente"""
    if current_depth >= max_depth:
        return []
    
    url = f"{BASE_URL}/{project}/_apis/git/repositories/{repo_id}/items"
    params = {"scopePath": path, "recursionLevel": "OneLevel", "api-version": "7.0"}
    
    data = az_get(url, params)
    if not data or "value" not in data:
        return []
    
    files = []
    for item in data["value"]:
        item_path = item.get("path", "").lstrip("/")
        is_folder = item.get("isFolder", False) or item.get("gitObjectType") == "tree"
        
        if is_folder:
            if any(x in item_path.lower() for x in ["src", "lib", "app", "server", "api", "controller", "service", "domain", "infrastructure"]):
                sub_files = list_code_files(project, repo_id, f"/{item_path}", max_depth, current_depth + 1)
                files.extend(sub_files)
        else:
            if any(item_path.endswith(ext) for ext in CODE_EXTENSIONS):
                files.append(item_path)
    
    return files


# =============================================================================
# Análise de Camadas
# =============================================================================
def analyze_file_layer(content: str, filename: str) -> Dict[str, List[str]]:
    """Analisa um arquivo e detecta camadas arquiteturais"""
    layers_found = defaultdict(list)
    
    # Detectar por path
    filename_lower = filename.lower()
    for layer_name in LAYER_PATTERNS.keys():
        if layer_name in filename_lower or f"/{layer_name}/" in filename_lower:
            layers_found[layer_name].append(filename)
    
    # Detectar por padrões no código
    for layer_name, patterns in LAYER_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, content, re.MULTILINE):
                if filename not in layers_found[layer_name]:
                    layers_found[layer_name].append(filename)
                break
    
    return dict(layers_found)


def extract_class_info(content: str, filename: str) -> List[Dict]:
    """Extrai informações de classes (nome, tipo, métodos)"""
    classes = []
    
    # Padrão para classes TypeScript/JavaScript
    class_pattern = r"export\s+class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?\s*\{"
    matches = re.finditer(class_pattern, content)
    
    for match in matches:
        class_name = match.group(1)
        extends = match.group(2)
        implements = match.group(3)
        
        # Detectar tipo da classe
        class_type = "Unknown"
        if "Controller" in class_name:
            class_type = "Controller"
        elif "Service" in class_name:
            class_type = "Service"
        elif "Repository" in class_name:
            class_type = "Repository"
        elif "Entity" in class_name:
            class_type = "Entity"
        elif "Dto" in class_name:
            class_type = "DTO"
        elif "Resolver" in class_name:
            class_type = "Resolver"
        elif "UseCase" in class_name:
            class_type = "UseCase"
        elif "Guard" in class_name:
            class_type = "Guard"
        elif "Middleware" in class_name:
            class_type = "Middleware"
        
        # Extrair métodos
        methods = []
        method_pattern = r"(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*[\w<>\[\]]+)?\s*\{"
        method_matches = re.finditer(method_pattern, content[match.end():match.end() + 5000])  # Limitar busca
        
        for method_match in list(method_matches)[:20]:  # Limitar a 20 métodos
            method_name = method_match.group(1)
            if not method_name.startswith("_") and method_name not in ["constructor"]:
                methods.append(method_name)
        
        classes.append({
            "name": class_name,
            "type": class_type,
            "file": filename,
            "extends": extends,
            "implements": implements,
            "methods": methods[:10],  # Top 10 métodos
            "method_count": len(methods)
        })
    
    return classes


def extract_routes(content: str, filename: str) -> List[Dict]:
    """Extrai rotas REST dos controllers"""
    routes = []
    
    for pattern in ROUTE_PATTERNS:
        matches = re.finditer(pattern, content)
        for match in matches:
            route = match.group(1)
            method = "GET"
            if "@Post" in match.group(0) or "post(" in match.group(0):
                method = "POST"
            elif "@Put" in match.group(0) or "put(" in match.group(0):
                method = "PUT"
            elif "@Delete" in match.group(0) or "delete(" in match.group(0):
                method = "DELETE"
            elif "@Patch" in match.group(0):
                method = "PATCH"
            
            routes.append({
                "method": method,
                "path": route,
                "file": filename
            })
    
    return routes


def extract_graphql_operations(content: str, filename: str) -> List[Dict]:
    """Extrai queries e mutations GraphQL"""
    operations = []
    
    for pattern in GRAPHQL_PATTERNS:
        matches = re.finditer(pattern, content)
        for match in matches:
            operation_name = match.group(1)
            operation_type = "Query"
            if "@Mutation" in match.group(0):
                operation_type = "Mutation"
            elif "@Subscription" in match.group(0):
                operation_type = "Subscription"
            
            operations.append({
                "type": operation_type,
                "name": operation_name,
                "file": filename
            })
    
    return operations


def detect_architecture_pattern(layers: Dict[str, int]) -> List[str]:
    """Detecta padrões arquiteturais baseado nas camadas"""
    patterns = []
    
    if layers.get("controllers", 0) > 0 and layers.get("services", 0) > 0:
        patterns.append("MVC (Model-View-Controller)")
    
    if layers.get("use_cases", 0) > 0 and layers.get("entities", 0) > 0:
        patterns.append("Clean Architecture")
    
    if layers.get("repositories", 0) > 0:
        patterns.append("Repository Pattern")
    
    if layers.get("dtos", 0) > 0:
        patterns.append("DTO Pattern")
    
    if layers.get("resolvers", 0) > 0:
        patterns.append("GraphQL Architecture")
    
    if (layers.get("guards", 0) > 0 or layers.get("middlewares", 0) > 0 or 
        layers.get("interceptors", 0) > 0):
        patterns.append("Aspect-Oriented Programming (AOP)")
    
    if layers.get("validators", 0) > 0:
        patterns.append("Validation Layer")
    
    return patterns if patterns else ["Generic/Unstructured"]


# =============================================================================
# Scanner Principal
# =============================================================================
def run_layer_analyzer():
    print("🏗️ Iniciando Análise de Camadas Arquiteturais...")
    print(f"📍 Organization: {AZDO_ORG}\n")
    
    # Carregar scan anterior
    scanner_file = OUTPUT_JSON / "azure_scanner.json"

    if not scanner_file.exists():
        print("❌ Arquivo azure_scanner.json não encontrado!")
        return

    with open(scanner_file, "r", encoding="utf-8") as f:
        scan_data = json.load(f)    
    
    output = {
        "organization": AZDO_ORG,
        "scan_date": scan_data.get("scan_date"),
        "projects": []
    }
    
    for project in scan_data["projects"]:
        print(f"\n{'='*60}")
        print(f"📦 Projeto: {project['name']}")
        print(f"{'='*60}")
        
        project_analysis = {
            "id": project["id"],
            "name": project["name"],
            "repos": []
        }
        
        for idx, repo in enumerate(project["repos"], 1):
            # Pular repos não-backend
            if repo["analysis"]["language"] not in ["Node.js/TypeScript", "Java", ".NET"]:
                continue
            
            print(f"\n  [{idx}/{len(project['repos'])}] 🔎 {repo['name']}")
            
            # Detectar branch
            branch = get_default_branch(project["name"], repo["id"])
            
            # Listar arquivos
            print(f"      📂 Listando arquivos...")
            code_files = list_code_files(project["name"], repo["id"])
            print(f"      ✓ {len(code_files)} arquivos encontrados")
            
            # Limitar análise
            code_files = code_files[:100]  # Analisar até 100 arquivos
            
            # Análise
            all_layers = defaultdict(list)
            all_classes = []
            all_routes = []
            all_graphql = []
            files_analyzed = 0
            
            print(f"      🔬 Analisando estrutura...")
            
            for file_path in code_files:
                content = fetch_file_content(project["name"], repo["id"], file_path, branch)
                if not content:
                    continue
                
                # Análise de camadas
                layers = analyze_file_layer(content, file_path)
                for layer, files in layers.items():
                    all_layers[layer].extend(files)
                
                # Extrair classes
                classes = extract_class_info(content, file_path)
                all_classes.extend(classes)
                
                # Extrair rotas
                routes = extract_routes(content, file_path)
                all_routes.extend(routes)
                
                # Extrair GraphQL
                graphql = extract_graphql_operations(content, file_path)
                all_graphql.extend(graphql)
                
                files_analyzed += 1
            
            # Consolidar
            layer_summary = {layer: len(set(files)) for layer, files in all_layers.items()}
            
            # Detectar padrões
            patterns = detect_architecture_pattern(layer_summary)
            
            # Stats
            total_classes = len(all_classes)
            total_routes = len(all_routes)
            total_graphql = len(all_graphql)
            
            print(f"      ✓ {files_analyzed} arquivos analisados")
            print(f"      ✓ {total_classes} classes encontradas")
            print(f"      ✓ {total_routes} rotas REST")
            print(f"      ✓ {total_graphql} operações GraphQL")
            
            if layer_summary:
                print(f"      📊 Camadas detectadas:")
                for layer, count in sorted(layer_summary.items(), key=lambda x: x[1], reverse=True):
                    print(f"         - {layer}: {count}")
            
            repo_analysis = {
                "id": repo["id"],
                "name": repo["name"],
                "language": repo["analysis"]["language"],
                "files_analyzed": files_analyzed,
                "layer_summary": layer_summary,
                "architecture_patterns": patterns,
                "classes": all_classes[:50],  # Top 50 classes
                "routes": all_routes[:100],  # Top 100 rotas
                "graphql_operations": all_graphql[:50],  # Top 50 operações
                "statistics": {
                    "total_classes": total_classes,
                    "total_routes": total_routes,
                    "total_graphql": total_graphql,
                    "controllers": len([c for c in all_classes if c["type"] == "Controller"]),
                    "services": len([c for c in all_classes if c["type"] == "Service"]),
                    "repositories": len([c for c in all_classes if c["type"] == "Repository"]),
                    "resolvers": len([c for c in all_classes if c["type"] == "Resolver"]),
                    "entities": len([c for c in all_classes if c["type"] == "Entity"]),
                    "dtos": len([c for c in all_classes if c["type"] == "DTO"]),
                }
            }
            
            project_analysis["repos"].append(repo_analysis)
        
        output["projects"].append(project_analysis)
    
    # Salvar resultado
    output_file = OUTPUT_JSON / "layer_analysis.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"📄 Arquivo salvo: {output_file}")
    
    print("\n" + "="*60)
    print("✅ Análise de Camadas concluída!")
    print(f"📄 Arquivo salvo: {output_file}")
    print("="*60 + "\n")
    
    # Gerar relatório
    generate_layer_report(output)


def generate_layer_report(data: Dict):
    """Gera relatório consolidado de camadas"""
    print("\n" + "="*60)
    print("📊 RELATÓRIO DE CAMADAS ARQUITETURAIS")
    print("="*60 + "\n")
    
    # Consolidar estatísticas
    total_repos = 0
    total_classes = 0
    total_routes = 0
    total_graphql = 0
    pattern_count = defaultdict(int)
    layer_totals = defaultdict(int)
    
    for project in data["projects"]:
        for repo in project["repos"]:
            total_repos += 1
            stats = repo["statistics"]
            total_classes += stats["total_classes"]
            total_routes += stats["total_routes"]
            total_graphql += stats["total_graphql"]
            
            for pattern in repo["architecture_patterns"]:
                pattern_count[pattern] += 1
            
            for layer, count in repo["layer_summary"].items():
                layer_totals[layer] += count
    
    print(f"📦 Repositórios analisados: {total_repos}")
    print(f"🔧 Total de classes: {total_classes}")
    print(f"🌐 Total de rotas REST: {total_routes}")
    print(f"⚡ Total de operações GraphQL: {total_graphql}")
    print()
    
    print("🏗️ Padrões Arquiteturais Detectados:")
    for pattern, count in sorted(pattern_count.items(), key=lambda x: x[1], reverse=True):
        print(f"   ✓ {pattern}: {count} repositórios")
    print()
    
    print("📊 Distribuição de Camadas:")
    for layer, count in sorted(layer_totals.items(), key=lambda x: x[1], reverse=True):
        print(f"   • {layer}: {count} arquivos")
    print()
    
    # Salvar relatório em texto
    report_text = f"""RELATÓRIO DE CAMADAS ARQUITETURAIS
{'='*60}

Resumo Geral:
- Repositórios analisados: {total_repos}
- Total de classes: {total_classes}
- Total de rotas REST: {total_routes}
- Total de operações GraphQL: {total_graphql}

Padrões Arquiteturais:
"""
    for pattern, count in sorted(pattern_count.items(), key=lambda x: x[1], reverse=True):
        report_text += f"  ✓ {pattern}: {count} repositórios\n"
    
    report_text += "\nDistribuição de Camadas:\n"
    for layer, count in sorted(layer_totals.items(), key=lambda x: x[1], reverse=True):
        report_text += f"  • {layer}: {count} arquivos\n"
    
    report_file = OUTPUT_REPORTS / "layer_report.txt"

    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"✅ Relatório salvo em: {report_file}\n")

if __name__ == "__main__":
    run_layer_analyzer()