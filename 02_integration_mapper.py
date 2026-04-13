import os
import re
import json
import base64
import requests
from pathlib import Path
from typing import Dict, List, Set, Optional
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

# Garante diretórios
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

# Arquivos a serem analisados
CODE_EXTENSIONS = [".ts", ".js", ".tsx", ".jsx", ".java", ".py", ".cs", ".go"]

# Padrões de integração expandidos para múltiplas linguagens

INTEGRATION_PATTERNS = {
    # =========================================================================
    # NESTJS / TYPESCRIPT / JAVASCRIPT
    # =========================================================================
    "nestjs_decorators": [
        (r"@(?:Query|Mutation|Subscription)\s*\(", "NestJS GraphQL Resolvers"),
        (r"@(?:Args|Context|Info|Parent)\s*\(", "NestJS GraphQL Parameters"),
        (r"@(?:ObjectType|InputType|Field|InterfaceType)\s*\(", "NestJS GraphQL Types"),
        (r"@(?:Controller|Get|Post|Put|Delete|Patch|Options)\s*\(", "NestJS REST API"),
        (r"@Injectable\s*\(", "NestJS Services"),
        (r"@Module\s*\(", "NestJS Modules"),
        (r"@UseGuards\s*\(", "NestJS Guards"),
        (r"@UseInterceptors\s*\(", "NestJS Interceptors"),
        (r"@UsePipes\s*\(", "NestJS Pipes"),
    ],
    
    # =========================================================================
    # JAVA / SPRING BOOT
    # =========================================================================
    "spring_annotations": [
        (r"@RestController|@Controller", "Spring MVC Controllers"),
        (r"@RequestMapping|@GetMapping|@PostMapping|@PutMapping|@DeleteMapping", "Spring REST Endpoints"),
        (r"@Service|@Component|@Repository", "Spring Components"),
        (r"@Autowired|@Inject", "Spring Dependency Injection"),
        (r"@Entity|@Table|@Column", "JPA/Hibernate Entities"),
        (r"@Transactional", "Spring Transactions"),
        (r"@Configuration|@Bean", "Spring Configuration"),
        (r"@EnableScheduling|@Scheduled", "Spring Scheduling"),
        (r"@EnableAsync|@Async", "Spring Async Processing"),
        (r"@KafkaListener|@RabbitListener", "Spring Messaging"),
        (r"@PreAuthorize|@Secured|@RolesAllowed", "Spring Security"),
    ],
    
    "java_frameworks": [
        (r"import\s+org\.springframework", "Spring Framework"),
        (r"import\s+javax\.persistence|jakarta\.persistence", "JPA"),
        (r"import\s+org\.hibernate", "Hibernate ORM"),
        (r"import\s+com\.netflix\.hystrix", "Netflix Hystrix"),
        (r"import\s+io\.micronaut", "Micronaut Framework"),
        (r"import\s+javax\.ws\.rs|jakarta\.ws\.rs", "JAX-RS (Jersey/RESTEasy)"),
        (r"import\s+org\.apache\.camel", "Apache Camel"),
    ],
    
    # =========================================================================
    # PYTHON / FLASK / DJANGO / FASTAPI
    # =========================================================================
    "python_decorators": [
        (r"@app\.route\s*\(|@bp\.route\s*\(", "Flask Routes"),
        (r"@app\.(?:get|post|put|delete|patch)\s*\(", "FastAPI Routes"),
        (r"@login_required|@permission_required", "Flask Auth Decorators"),
        (r"@celery\.task|@shared_task", "Celery Tasks"),
        (r"@staticmethod|@classmethod|@property", "Python Class Decorators"),
    ],
    
    "python_frameworks": [
        (r"from\s+flask\s+import|import\s+flask", "Flask Framework"),
        (r"from\s+django|import\s+django", "Django Framework"),
        (r"from\s+fastapi\s+import|import\s+fastapi", "FastAPI Framework"),
        (r"from\s+sqlalchemy\s+import|import\s+sqlalchemy", "SQLAlchemy ORM"),
        (r"from\s+pydantic\s+import|import\s+pydantic", "Pydantic Validation"),
        (r"from\s+celery\s+import|import\s+celery", "Celery Task Queue"),
        (r"import\s+pytest|from\s+pytest", "Pytest Testing"),
    ],
    
    # =========================================================================
    # PHP / LARAVEL / SYMFONY
    # =========================================================================
    "php_annotations": [
        (r"#\[Route\(|@Route\(", "PHP/Symfony Routes"),
        (r"#\[Get\(|#\[Post\(|#\[Put\(|#\[Delete\(", "PHP HTTP Methods"),
        (r"@ORM\\Entity|#\[ORM\\Entity\]", "Doctrine ORM Entities"),
        (r"@ORM\\Table|#\[ORM\\Table\]", "Doctrine Tables"),
        (r"public\s+function\s+\w+\s*\([^)]*Request", "Laravel/Symfony Request Handlers"),
    ],
    
    "php_frameworks": [
        (r"use\s+Illuminate\\", "Laravel Framework"),
        (r"use\s+Symfony\\", "Symfony Framework"),
        (r"use\s+Doctrine\\", "Doctrine ORM"),
        (r"use\s+Psr\\Http", "PSR HTTP Standards"),
        (r"use\s+GuzzleHttp\\", "Guzzle HTTP Client"),
    ],
    
    # =========================================================================
    # C# / .NET / ASP.NET
    # =========================================================================
    "dotnet_annotations": [
        (r"\[Route\(|\[HttpGet\]|\[HttpPost\]|\[HttpPut\]|\[HttpDelete\]", ".NET API Controllers"),
        (r"\[ApiController\]", ".NET API Controllers"),
        (r"\[Authorize\]|\[AllowAnonymous\]", ".NET Authorization"),
        (r"\[FromBody\]|\[FromQuery\]|\[FromRoute\]", ".NET Parameter Binding"),
        (r"\[Table\(|\[Column\(", "Entity Framework Attributes"),
        (r"\[ServiceFilter\]|\[TypeFilter\]", ".NET Filters"),
    ],
    
    "dotnet_frameworks": [
        (r"using\s+Microsoft\.AspNetCore", "ASP.NET Core"),
        (r"using\s+Microsoft\.EntityFrameworkCore", "Entity Framework Core"),
        (r"using\s+System\.Net\.Http", ".NET HttpClient"),
        (r"using\s+MediatR", "MediatR (CQRS)"),
        (r"using\s+AutoMapper", "AutoMapper"),
    ],
    
    # =========================================================================
    # GO / GOLANG
    # =========================================================================
    "golang_frameworks": [
        (r"import\s+\"github\.com/gin-gonic/gin\"", "Gin Web Framework"),
        (r"import\s+\"github\.com/gorilla/mux\"", "Gorilla Mux Router"),
        (r"import\s+\"github\.com/labstack/echo\"", "Echo Framework"),
        (r"import\s+\"gorm\.io/gorm\"", "GORM ORM"),
        (r"import\s+\"github\.com/go-redis/redis\"", "Go Redis Client"),
        (r"import\s+\"google\.golang\.org/grpc\"", "gRPC"),
    ],
    
    # =========================================================================
    # HTTP CLIENTS (Multi-language)
    # =========================================================================
    "http_clients": [
        # JavaScript/TypeScript
        (r"axios\.(?:get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)", "Axios HTTP"),
        (r"fetch\s*\(\s*['\"]([^'\"]+)", "Fetch API"),
        
        # Java
        (r"RestTemplate\.(?:getForObject|postForObject|exchange)", "Spring RestTemplate"),
        (r"WebClient\.(?:get|post|put|delete)", "Spring WebClient"),
        (r"HttpClient\.newHttpClient\(\)", "Java 11+ HttpClient"),
        
        # Python
        (r"requests\.(?:get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)", "Python Requests"),
        (r"httpx\.(?:get|post|put|delete|patch)", "Python HTTPX"),
        (r"aiohttp\.ClientSession", "Python aiohttp"),
        
        # PHP
        (r"Guzzle\\Client|GuzzleHttp\\Client", "PHP Guzzle"),
        (r"file_get_contents\s*\(\s*['\"]http", "PHP file_get_contents"),
        
        # C#
        (r"HttpClient\.(?:GetAsync|PostAsync|PutAsync|DeleteAsync)", ".NET HttpClient"),
        (r"RestSharp\.RestClient", ".NET RestSharp"),
        
        # Go
        (r"http\.(?:Get|Post|Put|Delete)\s*\(\s*\"([^\"]+)", "Go http package"),
        (r"resty\.New\(\)", "Go Resty Client"),
    ],
    
    # =========================================================================
    # MESSAGE QUEUES
    # =========================================================================
    "message_queues": [
        (r"@azure/service-bus", "Azure Service Bus"),
        (r"@azure/event-hubs", "Azure Event Hubs"),
        (r"kafka|KafkaProducer|KafkaConsumer", "Apache Kafka"),
        (r"rabbitmq|amqp|pika", "RabbitMQ"),
        (r"aws-sdk.*sqs|boto3.*sqs", "AWS SQS"),
        (r"@google-cloud/pubsub", "Google Cloud Pub/Sub"),
        (r"redis\.(?:publish|subscribe)|PUBLISH|SUBSCRIBE", "Redis Pub/Sub"),
    ],
    
    # =========================================================================
    # DATABASES
    # =========================================================================
    "databases": [
        # NoSQL
        (r"mongoose\.connect|MongoClient", "MongoDB"),
        (r"redis|ioredis|jedis|StackExchange\.Redis", "Redis"),
        (r"cosmosdb|@azure/cosmos|CosmosClient", "Azure Cosmos DB"),
        (r"cassandra-driver|DataStax", "Apache Cassandra"),
        
        # SQL
        (r"typeorm|sequelize|prisma", "Node.js ORM"),
        (r"pg|node-postgres", "PostgreSQL (Node.js)"),
        (r"mysql2|mysql", "MySQL (Node.js)"),
        (r"jdbc:postgresql|org\.postgresql", "PostgreSQL (Java)"),
        (r"jdbc:mysql|com\.mysql", "MySQL (Java)"),
        (r"System\.Data\.SqlClient|Microsoft\.Data\.SqlClient", "SQL Server (.NET)"),
        (r"psycopg2|asyncpg", "PostgreSQL (Python)"),
        (r"pymysql|mysql-connector-python", "MySQL (Python)"),
    ],
    
    # =========================================================================
    # AUTHENTICATION & AUTHORIZATION
    # =========================================================================
    "authentication": [
        (r"keycloak|nest-keycloak", "Keycloak"),
        (r"passport-jwt|jsonwebtoken|jwt-simple", "JWT (Node.js)"),
        (r"@nestjs/passport|passport", "Passport.js"),
        (r"oauth2|openid", "OAuth2/OpenID"),
        (r"Spring Security|@EnableWebSecurity", "Spring Security"),
        (r"Microsoft\.AspNetCore\.Authentication", "ASP.NET Authentication"),
        (r"flask-login|flask-jwt-extended", "Flask Auth"),
        (r"Auth0|auth0", "Auth0"),
    ],
    
    # =========================================================================
    # CLOUD SERVICES
    # =========================================================================
    "cloud_services": [
        # Azure
        (r"@azure/storage-blob", "Azure Blob Storage"),
        (r"@azure/app-configuration", "Azure App Configuration"),
        (r"@azure/keyvault", "Azure Key Vault"),
        
        # AWS
        (r"aws-sdk|@aws-sdk|boto3", "AWS SDK"),
        (r"s3|S3Client", "AWS S3"),
        (r"lambda|LambdaClient", "AWS Lambda"),
        
        # GCP
        (r"@google-cloud/storage", "Google Cloud Storage"),
        (r"firebase-admin", "Firebase"),
        
        # Multi-cloud
        (r"terraform|Terraform", "Terraform IaC"),
    ],
    
    # =========================================================================
    # MONITORING & LOGGING
    # =========================================================================
    "monitoring": [
        (r"@dynatrace/oneagent", "Dynatrace"),
        (r"elastic-apm|@elastic/apm", "Elastic APM"),
        (r"@opentelemetry|opentelemetry", "OpenTelemetry"),
        (r"winston|pino|bunyan", "Node.js Logging"),
        (r"log4j|slf4j|logback", "Java Logging"),
        (r"Serilog|NLog|log4net", ".NET Logging"),
        (r"logging\.getLogger|import\s+logging", "Python Logging"),
        (r"@dasa-logs/plte-log-lib", "DASA Logging"),
        (r"newrelic|New Relic", "New Relic"),
        (r"datadog|Datadog", "Datadog"),
    ],
    
    # =========================================================================
    # GRAPHQL
    # =========================================================================
    "graphql": [
        (r"@apollo/(?:server|gateway|subgraph)", "Apollo GraphQL"),
        (r"graphql-ws|subscriptions-transport-ws", "GraphQL Subscriptions"),
        (r"@nestjs/graphql", "NestJS GraphQL"),
        (r"com\.graphql-java", "GraphQL Java"),
        (r"strawberry|graphene|ariadne", "Python GraphQL"),
    ],
    
    # =========================================================================
    # TESTING FRAMEWORKS
    # =========================================================================
    "testing": [
        (r"jest|@jest", "Jest (JavaScript)"),
        (r"mocha|chai", "Mocha/Chai (JavaScript)"),
        (r"junit|@Test|@BeforeEach", "JUnit (Java)"),
        (r"pytest|import\s+pytest", "Pytest (Python)"),
        (r"PHPUnit|TestCase", "PHPUnit (PHP)"),
        (r"xunit|NUnit|MSTest", ".NET Testing"),
        (r"cypress|@cypress", "Cypress E2E"),
        (r"playwright|@playwright", "Playwright E2E"),
    ],
    
    # =========================================================================
    # CONTAINERIZATION & ORCHESTRATION
    # =========================================================================
    "containerization": [
        (r"FROM\s+[\w/:-]+", "Dockerfile"),
        (r"docker-compose|docker_compose", "Docker Compose"),
        (r"kubernetes|k8s|kubectl", "Kubernetes"),
        (r"apiVersion:\s*apps/v1", "Kubernetes Manifests"),
        (r"helm|Helm", "Helm Charts"),
    ],
}

# Padrões de URLs e endpoints
URL_PATTERNS = [
    r"https?://[^\s'\")]+",
    r"process\.env\.[A-Z_]+_URL",
    r"config\.get\(['\"].*[Uu]rl['\"]",
    r"application\.properties.*url",  # Java
    r"appsettings\.json.*Url",  # .NET
]

# Padrões de URLs e endpoints
URL_PATTERNS = [
    r"https?://[^\s'\")]+",
    r"process\.env\.[A-Z_]+_URL",
    r"config\.get\(['\"].*[Uu]rl['\"]",
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
    
    # Método 1: download direto
    params = {"path": path, "download": "true", "api-version": "7.0"}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=30)
        if r.status_code == 200 and r.text:
            return r.text
    except:
        pass
    
    # Método 2: com branch
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


def list_files_recursive(project: str, repo_id: str, path: str = "/", max_depth: int = 5, current_depth: int = 0) -> List[str]:
    """Lista arquivos de código recursivamente"""
    if current_depth >= max_depth:
        return []
    
    url = f"{BASE_URL}/{project}/_apis/git/repositories/{repo_id}/items"
    params = {
        "scopePath": path,
        "recursionLevel": "OneLevel",
        "api-version": "7.0",
    }
    
    data = az_get(url, params)
    if not data or "value" not in data:
        return []
    
    files = []
    for item in data["value"]:
        item_path = item.get("path", "").lstrip("/")
        is_folder = item.get("isFolder", False) or item.get("gitObjectType") == "tree"
        
        if is_folder:
            # Explorar apenas pastas importantes
            if any(x in item_path.lower() for x in ["src", "lib", "app", "server", "api", "service", "controller"]):
                sub_files = list_files_recursive(project, repo_id, f"/{item_path}", max_depth, current_depth + 1)
                files.extend(sub_files)
        else:
            # Adicionar apenas arquivos de código
            if any(item_path.endswith(ext) for ext in CODE_EXTENSIONS):
                files.append(item_path)
    
    return files


# =============================================================================
# Análise de Integrações
# =============================================================================
def analyze_integrations(content: str, filename: str) -> Dict[str, List[Dict]]:
    """Analisa um arquivo e retorna todas as integrações encontradas"""
    integrations = defaultdict(list)
    
    # 1. Detectar padrões de integração
    for category, patterns in INTEGRATION_PATTERNS.items():
        for pattern, tech_name in patterns:
            if isinstance(pattern, str):
                # Busca simples por string
                if re.search(pattern, content, re.IGNORECASE):
                    integrations[category].append({
                        "technology": tech_name,
                        "file": filename,
                        "type": "dependency"
                    })
            else:
                # Regex com captura
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    url = match.group(1) if match.groups() else match.group(0)
                    integrations[category].append({
                        "technology": tech_name,
                        "file": filename,
                        "endpoint": url,
                        "type": "code_call"
                    })
    
    # 2. Extrair URLs
    for pattern in URL_PATTERNS:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            url = match.group(0)
            # Filtrar URLs comuns não relevantes
            if not any(x in url.lower() for x in ["localhost", "example.com", "test", "mock"]):
                integrations["external_apis"].append({
                    "url": url,
                    "file": filename,
                    "type": "http_endpoint"
                })
    
    # 3. Detectar variáveis de ambiente (endpoints configuráveis)
    env_vars = re.findall(r"process\.env\.([A-Z_]+(?:URL|HOST|ENDPOINT|API))", content)
    for var in env_vars:
        integrations["environment_config"].append({
            "variable": var,
            "file": filename,
            "type": "env_variable"
        })
    
    return integrations


def deduplicate_integrations(integrations: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
    """Remove duplicatas mantendo a mais informativa"""
    result = {}
    
    for category, items in integrations.items():
        seen = set()
        unique_items = []
        
        for item in items:
            # Criar chave única baseada nos campos relevantes
            if "technology" in item:
                key = item["technology"]
            elif "url" in item:
                key = item["url"]
            elif "variable" in item:
                key = item["variable"]
            else:
                continue
            
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        
        if unique_items:
            result[category] = unique_items
    
    return result


# =============================================================================
# Scanner Principal
# =============================================================================
def run_integration_mapper():
    print("🔍 Iniciando Mapeamento de Integrações...")
    print(f"📍 Organization: {AZDO_ORG}\n")
    
    # Carregar scan anterior
    scanner_file = OUTPUT_JSON / "azure_scanner.json"

    if not scanner_file.exists():
        print("❌ Arquivo azure_scanner.json não encontrado!")
        print("   Execute o scanner primeiro.")
        return

    with open(scanner_file, "r", encoding="utf-8") as f:
        scan_data = json.load(f)    
    
    output = {
        "organization": AZDO_ORG,
        "scan_date": scan_data.get("scan_date"),
        "total_integrations": 0,
        "projects": []
    }
    
    for project in scan_data["projects"]:
        print(f"\n{'='*60}")
        print(f"📦 Projeto: {project['name']}")
        print(f"{'='*60}")
        
        project_integrations = {
            "id": project["id"],
            "name": project["name"],
            "repos": []
        }
        
        for idx, repo in enumerate(project["repos"], 1):
            # Pular repos vazios
            if repo["analysis"]["language"] == "Unknown":
                continue
            
            print(f"\n  [{idx}/{len(project['repos'])}] 🔎 {repo['name']}")
            
            # Detectar branch
            branch = get_default_branch(project["name"], repo["id"])
            
            # Listar arquivos de código
            print(f"      📂 Listando arquivos de código...")
            code_files = list_files_recursive(project["name"], repo["id"])
            print(f"      ✓ {len(code_files)} arquivos encontrados")
            
            # Limitar para não sobrecarregar (analisar até 50 arquivos principais)
            code_files = code_files[:50]
            
            # Analisar arquivos
            all_integrations = defaultdict(list)
            files_analyzed = 0
            
            for file_path in code_files:
                content = fetch_file_content(project["name"], repo["id"], file_path, branch)
                if content:
                    file_integrations = analyze_integrations(content, file_path)
                    for category, items in file_integrations.items():
                        all_integrations[category].extend(items)
                    files_analyzed += 1
            
            # Deduplica e limpa
            all_integrations = deduplicate_integrations(dict(all_integrations))
            
            # Contar integrações
            total = sum(len(items) for items in all_integrations.values())
            
            print(f"      ✓ {files_analyzed} arquivos analisados")
            print(f"      ✓ {total} integrações detectadas")
            
            if all_integrations:
                for category, items in all_integrations.items():
                    print(f"         - {category}: {len(items)}")
            
            repo_info = {
                "id": repo["id"],
                "name": repo["name"],
                "language": repo["analysis"]["language"],
                "files_analyzed": files_analyzed,
                "total_integrations": total,
                "integrations": all_integrations
            }
            
            project_integrations["repos"].append(repo_info)
            output["total_integrations"] += total
        
        output["projects"].append(project_integrations)
    
    # Salvar resultado
    output_file = OUTPUT_JSON / "integration_map.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"📄 Arquivo salvo: {output_file}")        
    
    print("\n" + "="*60)
    print("✅ Mapeamento de Integrações concluído!")
    print(f"📄 Arquivo salvo: {output_file}")
    print(f"📊 Total de integrações: {output['total_integrations']}")
    print("="*60 + "\n")
    
    # Gerar resumo
    generate_integration_summary(output)


def generate_integration_summary(data: Dict):
    """Gera resumo consolidado de integrações (console + arquivo)"""

    print("\n" + "="*60)
    print("📊 RESUMO DE INTEGRAÇÕES")
    print("="*60 + "\n")

    category_stats = defaultdict(lambda: {"count": 0, "technologies": set()})

    # Consolidar dados
    for project in data.get("projects", []):
        for repo in project.get("repos", []):
            for category, items in repo.get("integrations", {}).items():
                category_stats[category]["count"] += len(items)
                for item in items:
                    if "technology" in item:
                        category_stats[category]["technologies"].add(item["technology"])

    # ===== CONSOLE =====
    for category, stats in sorted(category_stats.items()):
        print(f"🔹 {category.replace('_', ' ').title()}")
        print(f"   Total: {stats['count']} ocorrências")
        if stats["technologies"]:
            print(f"   Tecnologias: {', '.join(sorted(stats['technologies']))}")
        print()

    # ===== ARQUIVO =====
    summary_file = OUTPUT_REPORTS / "integration_summary.txt"

    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("RESUMO DE INTEGRAÇÕES\n")
        f.write("=" * 60 + "\n\n")

        if not category_stats:
            f.write("Nenhuma integração detectada.\n")
        else:
            for category, stats in sorted(category_stats.items()):
                f.write(f"{category.replace('_', ' ').upper()}\n")
                f.write(f"Total: {stats['count']}\n")

                if stats["technologies"]:
                    f.write("Tecnologias:\n")
                    for tech in sorted(stats["technologies"]):
                        f.write(f"  - {tech}\n")

                f.write("\n")

    print(f"✅ Resumo salvo em: {summary_file}\n")


if __name__ == "__main__":
    run_integration_mapper()