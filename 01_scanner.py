import requests
import base64
import json
import os
import re
from pathlib import Path
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()

AZDO_ORG = os.getenv("AZDO_ORG")
AZDO_PAT = os.getenv("AZDO_PAT")

AZURE_ORG = AZDO_ORG
AZURE_PROJECT = None  # Filtrar por projeto específico (None = todos)
PAT = AZDO_PAT

# Lê variável de ambiente
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")

BASE_DIR = Path(__file__).resolve().parent.parent

# Monta diretório final
output_dir = BASE_DIR / OUTPUT_DIR / "json"
output_dir.mkdir(parents=True, exist_ok=True)

# Arquivo final
filename = output_dir / "azure_scanner.json"

BASE_URL = f"https://dev.azure.com/{AZURE_ORG}"
HEADERS = {
    "Authorization": "Basic " + base64.b64encode(f":{PAT}".encode()).decode()
}

# Pastas importantes para escanear
IMPORTANT_FOLDERS = ["src", "devops", "configs", ".github", ".azure", "infrastructure", "helm", "charts"]

# Arquivos importantes para análise
TARGET_FILES = [
    "package.json",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "gradle.properties",
    "Dockerfile",
    "docker-compose.yml",
    "requirements.txt",
    "pyproject.toml",
    "Pipfile",
    "go.mod",
    "go.sum",
    "Cargo.toml",
    "mix.exs",
    "composer.json",
    ".csproj",
    ".fsproj",
    ".vbproj",
    "azure-pipelines.yml",
    "azure-pipelines.yaml",
    ".gitlab-ci.yml",
    "Jenkinsfile",
    "Makefile",
    "CMakeLists.txt"
]


# =========================================================
# Helper para chamar API
# =========================================================
def az_get(url, params=None):
    """Helper para chamar API com melhor tratamento de erros"""
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        # Debug
        if r.status_code not in [200, 201]:
            print(f"⚠️  Erro {r.status_code}: {url}")
            print(f"    Response: {r.text[:200]}")  # Primeiros 200 chars
            return None
            
        return r.json()
    except requests.exceptions.JSONDecodeError as e:
        print(f"❌ Erro JSON Decode: {e}")
        print(f"    URL: {url}")
        print(f"    Response text: {r.text[:200] if 'r' in locals() else 'N/A'}")
        return None
    except Exception as e:
        print(f"❌ Exceção: {e}")
        return None


# =========================================================
# Buscar arquivos recursivamente (com limite de profundidade)
# =========================================================
def fetch_files_recursive(org, project, repo_id, path="/", depth=0, max_depth=3):
    """
    Busca arquivos recursivamente, priorizando pastas importantes.
    Retorna: (arquivos, pastas)
    """
    if depth > max_depth:
        return [], []

    url = f"{BASE_URL}/{project}/_apis/git/repositories/{repo_id}/items"
    params = {
        "scopePath": path,
        "recursionLevel": "OneLevel",
        "api-version": "7.0"
    }
    
    data = az_get(url, params)
    if not data or "value" not in data:
        return [], []

    files = []
    folders = []

    for item in data["value"]:
        item_path = item.get("path", "").lstrip("/")
        
        # Determinar se é pasta
        is_folder = item.get("isFolder", False) or item.get("gitObjectType") == "tree"
        
        if is_folder:
            folder_name = item_path.split("/")[-1] if "/" in item_path else item_path
            folders.append(item_path)
            
            # Explorar apenas pastas importantes
            if depth == 0 or any(important in item_path.lower() for important in IMPORTANT_FOLDERS):
                sub_files, sub_folders = fetch_files_recursive(
                    org, project, repo_id, f"/{item_path}", depth + 1, max_depth
                )
                files.extend(sub_files)
                folders.extend(sub_folders)
        else:
            files.append(item_path)

    return files, folders


# =========================================================
# Ler conteúdo de arquivo
# =========================================================
def fetch_file_content(org, project, repo_id, path):
    """
    Busca o conteúdo de um arquivo - MESMA LÓGICA DO DIAGNÓSTICO QUE FUNCIONA
    """
    if not path.startswith("/"):
        path = f"/{path}"
    
    url = f"{BASE_URL}/{project}/_apis/git/repositories/{repo_id}/items"
    params = {
        "path": path,
        "includeContent": "true",
        "api-version": "7.0"
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        if response.status_code != 200:
            return None
        
        # EXATAMENTE como no diagnóstico: tentar JSON primeiro
        try:
            data = response.json()
            if "content" in data:
                content = data["content"]
                
                # Se for JSON, validar
                if path.endswith(".json"):
                    try:
                        json.loads(content)
                        return content
                    except json.JSONDecodeError:
                        pass
                else:
                    return content
        except json.JSONDecodeError:
            pass
        
        # Se JSON não funcionou, usar raw content com múltiplos encodings
        # ESTE É O MÉTODO QUE FUNCIONA NO DIAGNÓSTICO
        raw_content = response.content
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'iso-8859-1', 'cp1252']
        
        for enc in encodings:
            try:
                decoded = raw_content.decode(enc)
                
                # Se for JSON, validar antes de retornar
                if path.endswith(".json"):
                    try:
                        json.loads(decoded)
                        return decoded
                    except json.JSONDecodeError:
                        continue
                else:
                    # Para outros arquivos, retornar se conseguiu decodificar
                    if decoded.strip():  # Não retornar strings vazias
                        return decoded
                    
            except (UnicodeDecodeError, AttributeError):
                continue
        
        return None
        
    except Exception as e:
        return None

def fetch_file_content_debug(org, project, repo_id, path):
    """
    Versão DEBUG para descobrir o que a API está retornando
    """
    if not path.startswith("/"):
        path = f"/{path}"
    
    url = f"{BASE_URL}/{project}/_apis/git/repositories/{repo_id}/items"
    params = {
        "path": path,
        "includeContent": "true",
        "api-version": "7.0"
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        print(f"\n      🔍 DEBUG para {path}:")
        print(f"         Status: {response.status_code}")
        print(f"         Content-Type: {response.headers.get('Content-Type')}")
        print(f"         Content-Length: {len(response.content)} bytes")
        
        if response.status_code != 200:
            print(f"         ❌ Status não é 200")
            return None
        
        # Tentar JSON
        try:
            data = response.json()
            print(f"         ✓ JSON válido")
            print(f"         Keys disponíveis: {list(data.keys())}")
            
            if "content" in data:
                print(f"         ✓ Campo 'content' ENCONTRADO!")
                return data["content"]
            else:
                print(f"         ⚠️  Campo 'content' NÃO encontrado")
                print(f"         Resposta completa: {json.dumps(data, indent=2)[:300]}")
        except json.JSONDecodeError as e:
            print(f"         ⚠️  Não é JSON válido: {e}")
        
        # Tentar raw content
        print(f"         🔄 Tentando raw content...")
        raw_content = response.content
        
        if len(raw_content) == 0:
            print(f"         ❌ Raw content está vazio")
            return None
        
        print(f"         ✓ Raw content tem {len(raw_content)} bytes")
        print(f"         Primeiros 50 bytes (hex): {raw_content[:50].hex()}")
        
        # Tentar decodificar
        for enc in ['utf-8', 'utf-8-sig', 'latin-1']:
            try:
                decoded = raw_content.decode(enc)
                print(f"         ✓ Decodificado com {enc}")
                print(f"         Preview: {decoded[:100]}...")
                
                if path.endswith(".json"):
                    try:
                        json.loads(decoded)
                        print(f"         ✅ É JSON válido!")
                        return decoded
                    except:
                        print(f"         ⚠️  Não é JSON válido com {enc}")
                        continue
                else:
                    return decoded
                    
            except:
                continue
        
        print(f"         ❌ Nenhum encoding funcionou")
        return None
        
    except Exception as e:
        print(f"         ❌ Exceção: {e}")
        return None

def fetch_file_content_raw(org, project, repo_id, path):
    """
    Método alternativo: baixa o arquivo diretamente como blob.
    Usa o endpoint de download que sempre retorna conteúdo.
    """
    if not path.startswith("/"):
        path = f"/{path}"
    
    # Este endpoint retorna o conteúdo diretamente sem JSON wrapper
    url = f"{BASE_URL}/{project}/_apis/git/repositories/{repo_id}/items"
    params = {
        "path": path,
        "download": "true",
        "api-version": "7.0"
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        
        if response.status_code == 200:
            return response.text
        
        return None
            
    except Exception as e:
        print(f"      ❌ Erro ao buscar raw {path}: {e}")
        return None


def get_default_branch(org, project, repo_id):
    """Busca o branch padrão do repositório"""
    url = f"{BASE_URL}/{project}/_apis/git/repositories/{repo_id}"
    params = {"api-version": "7.0"}
    
    data = az_get(url, params)
    if data and "defaultBranch" in data:
        # Remove o prefixo refs/heads/
        return data["defaultBranch"].replace("refs/heads/", "")
    
    return "main"  # fallback


def fetch_file_content_v2(org, project, repo_id, path, default_branch):
    """
    Versão 2: Usa o branch correto detectado do repositório.
    """
    if not path.startswith("/"):
        path = f"/{path}"
    
    # Primeiro tenta baixar diretamente
    url = f"{BASE_URL}/{project}/_apis/git/repositories/{repo_id}/items"
    
    # Método 1: Download direto (mais confiável)
    params = {
        "path": path,
        "download": "true",
        "api-version": "7.0"
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if response.status_code == 200 and response.text:
            return response.text
    except:
        pass
    
    # Método 2: Com versionDescriptor
    params = {
        "path": path,
        "includeContent": "true",
        "versionDescriptor.versionType": "branch",
        "versionDescriptor.version": default_branch,
        "api-version": "7.0"
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if response.status_code == 200:
            # Tenta JSON primeiro
            try:
                data = response.json()
                if "content" in data:
                    return data["content"]
            except:
                pass
            
            # Se não for JSON válido, retorna texto
            if response.text:
                return response.text
    except:
        pass
    
    print(f"      ⚠️  Não foi possível ler: {path}")
    return None


# =========================================================
# Buscar arquivos .csproj, .fsproj, .vbproj dinamicamente
# =========================================================
def find_project_files(files, extensions):
    """Encontra arquivos com extensões específicas"""
    return [f for f in files if any(f.endswith(ext) for ext in extensions)]


# =========================================================
# Parse de dependências por linguagem
# =========================================================
def parse_dependencies(files_content, repo_id, project_name):
    """Extrai dependências de diferentes tipos de arquivos - VERSÃO CORRIGIDA"""
    deps = {
        "runtime": [],
        "dev": [],
        "build": []
    }

    # Helper para encontrar arquivo por nome (ignora path)
    def find_file_content(filename):
        for key, content in files_content.items():
            if key.endswith(filename) or key == filename:
                return content
        return None

    # Node.js - package.json
    pkg_content = find_file_content("package.json")
    if pkg_content:
        try:
            pkg = json.loads(pkg_content)
            deps["runtime"] = list(pkg.get("dependencies", {}).keys())
            deps["dev"] = list(pkg.get("devDependencies", {}).keys())
        except json.JSONDecodeError as e:
            print(f"      ⚠️  Erro ao parsear package.json: {e}")
        except Exception as e:
            print(f"      ⚠️  Erro inesperado no package.json: {e}")

    # Java - pom.xml
    pom_content = find_file_content("pom.xml")
    if pom_content:
        artifacts = re.findall(r"<artifactId>(.*?)</artifactId>", pom_content)
        deps["runtime"].extend(artifacts)

    # Python - requirements.txt
    req_content = find_file_content("requirements.txt")
    if req_content:
        reqs = req_content.split("\n")
        for req in reqs:
            req = req.strip()
            if req and not req.startswith("#"):
                pkg = req.split("==")[0].split(">=")[0].split("~=")[0].strip()
                if pkg:
                    deps["runtime"].append(pkg)

    # Python - pyproject.toml
    pyproj_content = find_file_content("pyproject.toml")
    if pyproj_content:
        matches = re.findall(r'"([a-zA-Z0-9\-_]+)[><=~]', pyproj_content)
        deps["runtime"].extend(matches)

    # Go - go.mod
    gomod_content = find_file_content("go.mod")
    if gomod_content:
        matches = re.findall(r"require\s+([\w\.\-\/]+)", gomod_content)
        deps["runtime"].extend(matches)

    # .NET - .csproj, .fsproj, .vbproj
    for key, content in files_content.items():
        if key.endswith((".csproj", ".fsproj", ".vbproj")):
            packages = re.findall(r'<PackageReference Include="(.*?)"', content)
            deps["runtime"].extend(packages)

    # Gradle - build.gradle / build.gradle.kts
    for key, content in files_content.items():
        if "build.gradle" in key:
            # implementation 'group:artifact:version'
            matches = re.findall(r"implementation\s+['\"]([^:]+:[^:]+)", content)
            deps["runtime"].extend([m.split(':')[1] if ':' in m else m for m in matches])

    return deps


# =========================================================
# Detectar Linguagem
# =========================================================
def detect_language(files):
    """Detecta a linguagem principal do repositório"""
    f_set = set(f.lower() for f in files)
    
    # Prioridade por especificidade
    if any(".csproj" in f or ".fsproj" in f or ".vbproj" in f for f in files):
        return ".NET"
    if "package.json" in f_set:
        return "Node.js/TypeScript"
    if "pom.xml" in f_set or "build.gradle" in f_set:
        return "Java"
    if "go.mod" in f_set:
        return "Go"
    if "cargo.toml" in f_set:
        return "Rust"
    if "requirements.txt" in f_set or "pyproject.toml" in f_set:
        return "Python"
    if "mix.exs" in f_set:
        return "Elixir"
    if "composer.json" in f_set:
        return "PHP"
    
    # Fallback para extensões
    extensions = [f.split(".")[-1].lower() for f in files if "." in f]
    if "py" in extensions:
        return "Python"
    if "js" in extensions or "ts" in extensions:
        return "JavaScript/TypeScript"
    if "java" in extensions:
        return "Java"
    if "cs" in extensions:
        return "C#"
    if "go" in extensions:
        return "Go"
    
    return "Unknown"


# =========================================================
# Detectar Build System
# =========================================================
def detect_build_system(files):
    """Detecta o sistema de build"""
    f_set = set(f.lower() for f in files)
    
    systems = []
    
    if "pom.xml" in f_set:
        systems.append("Maven")
    if "build.gradle" in f_set or "build.gradle.kts" in f_set:
        systems.append("Gradle")
    if "package.json" in f_set:
        systems.append("NPM/Yarn")
    if any(".csproj" in f or ".fsproj" in f for f in files):
        systems.append("MSBuild/.NET CLI")
    if "makefile" in f_set:
        systems.append("Make")
    if "cmakelists.txt" in f_set:
        systems.append("CMake")
    if "dockerfile" in f_set:
        systems.append("Docker")
    if "go.mod" in f_set:
        systems.append("Go Modules")
    if "cargo.toml" in f_set:
        systems.append("Cargo")
    
    return systems if systems else ["Unknown"]


# =========================================================
# Detectar Framework
# =========================================================
def detect_framework(language, deps):
    """Detecta frameworks baseado em linguagem e dependências"""
    all_deps = deps.get("runtime", []) + deps.get("dev", [])
    all_deps_lower = [d.lower() for d in all_deps]
    
    frameworks = []
    
    if language == "Node.js/TypeScript":
        if "express" in all_deps_lower:
            frameworks.append("Express")
        if any("nest" in d for d in all_deps_lower):
            frameworks.append("NestJS")
        if "fastify" in all_deps_lower:
            frameworks.append("Fastify")
        if "react" in all_deps_lower:
            frameworks.append("React")
        if "vue" in all_deps_lower:
            frameworks.append("Vue.js")
        if "angular" in all_deps_lower:
            frameworks.append("Angular")
        if "next" in all_deps_lower:
            frameworks.append("Next.js")
        if "vite" in all_deps_lower:
            frameworks.append("Vite")
    
    if language == "Java":
        if any("spring" in d for d in all_deps_lower):
            frameworks.append("Spring Boot")
        if any("quarkus" in d for d in all_deps_lower):
            frameworks.append("Quarkus")
        if any("micronaut" in d for d in all_deps_lower):
            frameworks.append("Micronaut")
    
    if language == ".NET":
        if any("aspnetcore" in d for d in all_deps_lower):
            frameworks.append("ASP.NET Core")
        if any("maui" in d for d in all_deps_lower):
            frameworks.append("MAUI")
        if any("blazor" in d for d in all_deps_lower):
            frameworks.append("Blazor")
    
    if language == "Python":
        if "django" in all_deps_lower:
            frameworks.append("Django")
        if "flask" in all_deps_lower:
            frameworks.append("Flask")
        if "fastapi" in all_deps_lower:
            frameworks.append("FastAPI")
    
    return frameworks if frameworks else ["None detected"]


# =========================================================
# Detectar Tipo do Projeto
# =========================================================
def detect_project_type(language, frameworks, files, folders):
    """Detecta o tipo/propósito do repositório"""
    files_lower = [f.lower() for f in files]
    folders_lower = [f.lower() for f in folders]
    
    types = []
    
    # Backend APIs
    backend_frameworks = ["express", "nestjs", "fastify", "spring boot", "asp.net core", "django", "flask", "fastapi"]
    if any(fw.lower() in [f.lower() for f in frameworks] for fw in backend_frameworks):
        types.append("API/Backend")
    
    # Frontend
    frontend_frameworks = ["react", "vue.js", "angular", "next.js"]
    if any(fw.lower() in [f.lower() for f in frameworks] for fw in frontend_frameworks):
        types.append("Frontend/SPA")
    
    # Mobile
    if any("android" in f or "ios" in f or "mobile" in f for f in folders_lower):
        types.append("Mobile")
    
    # Worker/Queue
    if any("worker" in f or "queue" in f or "consumer" in f for f in files_lower + folders_lower):
        types.append("Worker/Background Job")
    
    # IaC
    if any("terraform" in f or "pulumi" in f or "cloudformation" in f for f in files_lower):
        types.append("Infrastructure as Code")
    
    # Kubernetes/Helm
    if any("helm" in f or "charts" in f or "k8s" in f for f in folders_lower):
        types.append("Kubernetes/Helm")
    
    # CI/CD
    if any("azure-pipelines" in f or "jenkinsfile" in f or ".gitlab-ci" in f for f in files_lower):
        types.append("CI/CD Pipeline")
    
    # Biblioteca/SDK
    if language in ["Node.js/TypeScript", "Python", "Java", ".NET"] and not types:
        if any("lib" in f or "sdk" in f or "package" in f for f in folders_lower):
            types.append("Library/SDK")
    
    return types if types else ["Unknown/Generic"]


# =========================================================
# Analisar estrutura de pastas
# =========================================================
def analyze_folder_structure(folders):
    """Analisa a estrutura de pastas para insights arquiteturais"""
    structure = {
        "has_tests": any("test" in f.lower() for f in folders),
        "has_docs": any("doc" in f.lower() for f in folders),
        "has_ci_cd": any("devops" in f.lower() or ".github" in f.lower() or ".azure" in f.lower() for f in folders),
        "has_docker": False,  # Será detectado por arquivos
        "has_src": any("src" in f.lower() for f in folders),
        "architecture_hints": []
    }
    
    # Detectar padrões arquiteturais
    if any("controller" in f.lower() for f in folders):
        structure["architecture_hints"].append("MVC/Controller-based")
    if any("service" in f.lower() for f in folders):
        structure["architecture_hints"].append("Service Layer")
    if any("repository" in f.lower() or "repo" in f.lower() for f in folders):
        structure["architecture_hints"].append("Repository Pattern")
    if any("domain" in f.lower() for f in folders):
        structure["architecture_hints"].append("Domain-Driven Design")
    if any("api" in f.lower() for f in folders):
        structure["architecture_hints"].append("API-first")
    
    return structure

# =========================================================
# Scanner Principal
# =========================================================
def run_scanner():
    """Scanner Principal - COM DEBUGGING MELHORADO"""
    print("🚀 Iniciando Azure DevOps Technical Scanner...")
    print(f"📍 Organization: {AZURE_ORG}")
    
    # Listar projetos
    projects_data = az_get(f"{BASE_URL}/_apis/projects?api-version=7.0")
    if not projects_data:
        print("❌ Erro ao buscar projetos")
        return
    
    projects = projects_data.get("value", [])
    
    if AZURE_PROJECT:
        projects = [p for p in projects if p["name"] == AZURE_PROJECT]
        print(f"🎯 Filtrando apenas projeto: {AZURE_PROJECT}")
    
    output = {
        "organization": AZURE_ORG,
        "scan_date": "2025-12-11",
        "total_projects": len(projects),
        "projects": []
    }
    
    # Para cada projeto
    for proj in projects:
        print(f"\n{'='*60}")
        print(f"📦 Projeto: {proj['name']}")
        print(f"{'='*60}")
        
        repos_data = az_get(f"{BASE_URL}/{proj['name']}/_apis/git/repositories?api-version=7.0")
        if not repos_data:
            continue
            
        repos = repos_data.get("value", [])
        
        project_block = {
            "id": proj["id"],
            "name": proj["name"],
            "description": proj.get("description", ""),
            "total_repos": len(repos),
            "repos": []
        }
        
        # Para cada repositório
        for idx, repo in enumerate(repos, 1):
            print(f"\n  [{idx}/{len(repos)}] 🔍 Analisando: {repo['name']}")
            
            # Buscar arquivos recursivamente
            print(f"      📂 Escaneando estrutura de arquivos...")
            files, folders = fetch_files_recursive(AZURE_ORG, proj["name"], repo["id"])
            print(f"      ✓ {len(files)} arquivos | {len(folders)} pastas")

            # Identificar arquivos importantes
            important_files = []
            for target in TARGET_FILES:
                matches = [f for f in files if f.lower().endswith(target.lower()) or f.lower() == target.lower()]
                important_files.extend(matches)
            
            # Buscar .csproj e similares dinamicamente
            dotnet_files = find_project_files(files, [".csproj", ".fsproj", ".vbproj"])
            important_files.extend(dotnet_files)
            
            important_files = list(set(important_files))  # Remove duplicatas
            
            # Ler conteúdo dos arquivos importantes
            files_content = {}
            if important_files:
                print(f"      📖 Lendo {len(important_files)} arquivos importantes...")
                for file_path in important_files:
                    #content = fetch_file_content(AZURE_ORG, proj["name"], repo["id"], file_path)
                    content = fetch_file_content_debug(AZURE_ORG, proj["name"], repo["id"], file_path)

                    if content:
                        files_content[file_path] = content
                        print(f"      ✓ Lido: {file_path} ({len(content)} bytes)")
            else:
                print(f"      ℹ️  Nenhum arquivo importante detectado")
            
            # Análise
            print(f"      🔬 Analisando tecnologias...")
            language = detect_language(files)
            build_systems = detect_build_system(files)
            deps = parse_dependencies(files_content, repo["id"], proj["name"])
            frameworks = detect_framework(language, deps)
            project_types = detect_project_type(language, frameworks, files, folders)
            folder_structure = analyze_folder_structure(folders)
            
            # Adicionar detecção de Docker
            folder_structure["has_docker"] = any("dockerfile" in f.lower() for f in files)
            
            print(f"      ✓ Linguagem: {language}")
            print(f"      ✓ Build Systems: {', '.join(build_systems)}")
            print(f"      ✓ Frameworks: {', '.join(frameworks)}")
            print(f"      ✓ Tipo: {', '.join(project_types)}")
            print(f"      ✓ Dependências: {len(deps['runtime'])} runtime, {len(deps['dev'])} dev")
            
            repo_info = {
                "id": repo["id"],
                "name": repo["name"],
                "default_branch": repo.get("defaultBranch", "").replace("refs/heads/", ""),
                "url": repo.get("webUrl", repo.get("url")),
                "size": repo.get("size", 0),
                "analysis": {
                    "language": language,
                    "build_systems": build_systems,
                    "frameworks": frameworks,
                    "project_types": project_types,
                    "dependencies": deps,
                    "folder_structure": folder_structure
                },
                "files": {
                    "total_files": len(files),
                    "total_folders": len(folders),
                    "important_files": important_files,
                    "files_read": list(files_content.keys()),
                    "sample_files": files[:20]
                }
            }
            
            project_block["repos"].append(repo_info)
        
        output["projects"].append(project_block)
    
    # Salvar resultado
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("✅ Scanner concluído com sucesso!")
    print(f"📄 Arquivo salvo: {filename}")
    print(f"📊 Total de projetos: {output['total_projects']}")
    print(f"📊 Total de repositórios: {sum(p['total_repos'] for p in output['projects'])}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_scanner()