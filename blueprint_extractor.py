"""
blueprint_extractor.py  —  Parser determinístico dos blueprints.
Etapa 1 do pipeline de análise de gaps.

Lê a estrutura real dos arquivos:
  outputs/<projeto>/<app>.txt                        ← saída do scanner (3 seções JSON)
  outputs/<projeto>/blueprints/<app>_blueprint.md    ← blueprint gerado pelo LLM

O .txt contém TRÊS seções JSON separadas por linhas '===':
  1. scanner           → linguagem, dependências, estrutura de pastas
  2. integration_mapper → integrações detectadas (testes, DBs, auth, cloud...)
  3. layer_analysis    → classes, rotas, padrões arquiteturais

Saída:
  outputs/portfolio_structured.json   ← dados estruturados por app (entrada do gap_analyzer)
  outputs/portfolio_summary.md        ← tabela auditável para revisão humana
"""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict


# ─────────────────────────────────────────────────────────────────────────────
# PADRÕES DE SEÇÃO DO .TXT
# ─────────────────────────────────────────────────────────────────────────────
SECTION_PATTERNS = {
    "scanner": re.compile(
        r"Resultado da etapa de scanner:\s*={10,}\s*(\{.*?\})\s*(?:={10,}|$)",
        re.DOTALL | re.IGNORECASE),
    "integration_mapper": re.compile(
        r"Resultado da etapa de integration mapper:\s*={10,}\s*(\{.*?\})\s*(?:={10,}|$)",
        re.DOTALL | re.IGNORECASE),
    "layer_analysis": re.compile(
        r"Resultado da etapa de layer analysis:\s*={10,}\s*(\{.*?\})\s*(?:={10,}|$)",
        re.DOTALL | re.IGNORECASE),
}

# ─────────────────────────────────────────────────────────────────────────────
# NORMALIZAÇÃO DE NOMES DE TECNOLOGIA (integration_mapper.technology → chave)
# ─────────────────────────────────────────────────────────────────────────────
TECH_NORM = {
    "node.js/typescript": "nodejs", "node.js": "nodejs", "typescript": "typescript",
    "express": "express", "express.js": "express",
    "nestjs": "nestjs", "nest.js": "nestjs",
    "react": "react", "next.js": "nextjs",
    "expo": "expo", "react-native": "expo",
    "mongodb": "mongodb", "mongoose": "mongodb",
    "postgresql": "postgresql", "postgres": "postgresql",
    "redis": "redis",
    "sql server": "mssql", "mssql": "mssql",
    "keycloak": "keycloak",
    "passport.js": "passport", "passport": "passport",
    "jwt (node.js)": "jwt", "jwt": "jwt",
    "jest (javascript)": "jest", "jest": "jest",
    "playwright": "playwright", "supertest": "supertest",
    "dockerfile": "docker", "docker": "docker",
    "kubernetes": "kubernetes",
    "azure app configuration": "azure_appconfig",
    "azure key vault": "azure_keyvault",
    "azure service bus": "azure_servicebus",
    "azure event hubs": "azure_eventhubs",
    "dynatrace": "dynatrace", "elastic apm": "elastic_apm",
    "azure devops": "azure_devops", "github actions": "github_actions",
}

# Sinais esperados em todo app moderno → usados para calcular gaps críticos
CRITICAL_SIGNALS = [
    "health_check", "structured_logging", "apm",
    "jest", "docker", "swagger", "azure_keyvault", "azure_devops",
]

# Dimensões para score de maturidade
DIMENSIONS = {
    "observability":  ["apm", "health_check", "structured_logging"],
    "quality":        ["jest", "playwright", "supertest", "sonarqube"],
    "security":       ["azure_keyvault", "keycloak", "jwt", "passport"],
    "devops":         ["azure_devops", "github_actions", "docker", "kubernetes"],
    "architecture":   ["clean_architecture", "ddd", "event_driven", "graphql_federation", "swagger"],
    "documentation":  ["swagger", "readme_documented"],
}


# ─────────────────────────────────────────────────────────────────────────────
# EXTRAÇÃO DAS 3 SEÇÕES JSON DO .TXT
# ─────────────────────────────────────────────────────────────────────────────
def extract_sections(txt: str) -> dict:
    result = {}
    for name, pat in SECTION_PATTERNS.items():
        m = pat.search(txt)
        if not m:
            result[name] = None
            continue
        raw = m.group(1).strip()
        try:
            result[name] = json.loads(raw)
        except json.JSONDecodeError:
            # recupera JSON truncado
            depth, end = 0, 0
            for i, ch in enumerate(raw):
                depth += (ch == '{') - (ch == '}')
                if depth == 0:
                    end = i + 1
                    break
            try:
                result[name] = json.loads(raw[:end])
            except Exception as e:
                result[name] = {"_parse_error": str(e)}
    return result


# ─────────────────────────────────────────────────────────────────────────────
# PARSE DAS SEÇÕES
# ─────────────────────────────────────────────────────────────────────────────
def parse_scanner(data):
    if not data or "_parse_error" in data:
        return {"_ok": False}
    a = data.get("analysis", {})
    f = a.get("folder_structure", {})
    d = a.get("dependencies", {})
    fi = data.get("files", {})
    all_deps = d.get("runtime", []) + d.get("dev", []) + d.get("build", [])
    return {
        "_ok": True,
        "id":            data.get("id"),
        "url":           data.get("url"),
        "branch":        data.get("default_branch"),
        "size_kb":       round(data.get("size", 0) / 1024, 1),
        "language":      a.get("language", "Unknown"),
        "build_systems": a.get("build_systems", []),
        "frameworks":    a.get("frameworks", []),
        "project_types": a.get("project_types", []),
        "deps_runtime":  d.get("runtime", []),
        "deps_dev":      d.get("dev", []),
        "all_deps":      all_deps,
        "has_tests":     f.get("has_tests", False),
        "has_docs":      f.get("has_docs", False),
        "has_cicd":      f.get("has_ci_cd", False),
        "has_docker":    f.get("has_docker", False),
        "has_src":       f.get("has_src", False),
        "arch_hints":    f.get("architecture_hints", []),
        "total_files":   fi.get("total_files", 0),
        "total_folders": fi.get("total_folders", 0),
        "important_files": fi.get("important_files", []),
        "sample_files":  list(set(fi.get("sample_files", []))),
        "is_empty":      fi.get("total_files", 0) == 0 and a.get("language", "Unknown") == "Unknown",
    }


def parse_mapper(data):
    if not data or "_parse_error" in data:
        return {"_ok": False, "by_cat": {}, "tech_keys": [], "ext_apis": []}
    integrations = data.get("integrations", {})
    by_cat, tech_keys, ext_apis = {}, [], []
    for cat, items in integrations.items():
        if not isinstance(items, list):
            continue
        if cat == "external_apis":
            ext_apis = [{"url": i.get("url"), "file": i.get("file")} for i in items]
            continue
        entries = []
        for item in items:
            raw = item.get("technology", "").strip()
            key = TECH_NORM.get(raw.lower(), raw.lower().replace(" ", "_"))
            entries.append({"raw": raw, "key": key, "file": item.get("file"),
                            "source": f"integration_mapper.{cat}"})
            if key not in tech_keys:
                tech_keys.append(key)
        by_cat[cat] = entries
    return {"_ok": True, "by_cat": by_cat, "tech_keys": tech_keys, "ext_apis": ext_apis,
            "files_analyzed": data.get("files_analyzed", 0),
            "total_integrations": data.get("total_integrations", 0)}


def parse_layers(data):
    if not data or "_parse_error" in data:
        return {"_ok": False}
    # Deduplica classes e rotas (scanner duplica entradas)
    seen_cls, unique_cls = set(), []
    for c in data.get("classes", []):
        k = (c.get("name"), c.get("file"), c.get("type"))
        if k not in seen_cls:
            seen_cls.add(k)
            unique_cls.append(c)
    seen_rt, unique_rt = set(), []
    for r in data.get("routes", []):
        k = (r.get("method"), r.get("path"), r.get("file"))
        if k not in seen_rt:
            seen_rt.add(k)
            unique_rt.append(r)
    by_type = defaultdict(list)
    for c in unique_cls:
        by_type[c.get("type", "Unknown")].append(
            {"name": c["name"], "file": c["file"], "methods": c.get("methods", [])})
    return {
        "_ok": True,
        "arch_patterns": data.get("architecture_patterns", []),
        "classes_unique": len(unique_cls),
        "classes_raw":    data.get("statistics", {}).get("total_classes", 0),
        "by_type": dict(by_type),
        "routes_unique": unique_rt,
        "routes_count": len(unique_rt),
        "routes_raw": data.get("statistics", {}).get("total_routes", 0),
        "graphql_ops": data.get("graphql_operations", []),
        "dedup_note": "Deduplicado por (name/method, file, type/path) — scanner gera duplicatas",
    }


# ─────────────────────────────────────────────────────────────────────────────
# DETECÇÃO DE SINAIS  (cruza as 3 seções + blueprint)
# ─────────────────────────────────────────────────────────────────────────────
def detect_signals(sc, mp, ly, bp_text):
    """
    Para cada sinal retorna: found (bool), source (onde veio), evidence (trecho).
    Prioridade de fonte: scanner.deps > mapper > scanner.files > blueprint
    """
    deps     = [d.lower() for d in sc.get("all_deps", [])]   if sc.get("_ok") else []
    files    = [f.lower() for f in (sc.get("important_files", []) + sc.get("sample_files", []))] if sc.get("_ok") else []
    mp_keys  = mp.get("tech_keys", [])                        if mp.get("_ok") else []
    routes   = ly.get("routes_unique", [])                    if ly.get("_ok") else []
    arch_pat = ly.get("arch_patterns", [])                    if ly.get("_ok") else []
    bp       = bp_text.lower()

    def dep(*terms):
        for t in terms:
            for d in deps:
                if t.lower() in d:
                    return True, f"dep:{d}"
        return False, ""

    def fil(*terms):
        for t in terms:
            for f in files:
                if t.lower() in f:
                    return True, f"file:{f}"
        return False, ""

    def mpr(*keys):
        for k in keys:
            if k in mp_keys:
                return True, f"mapper:{k}"
        return False, ""

    def bpl(*terms):
        for t in terms:
            if t.lower() in bp:
                idx = bp.find(t.lower())
                snip = bp_text[max(0,idx-30):idx+80].replace("\n"," ").strip()
                return True, f'blueprint:"{snip}"'
        return False, ""

    S = {}

    # Stack
    lang = sc.get("language", "Unknown") if sc.get("_ok") else "Unknown"
    def sig(found, source, evidence):
        return {"found": found, "source": source, "evidence": evidence}

    if "node" in lang.lower():
        S["nodejs"] = sig(True, "scanner.language", lang)
    else:
        f, e = dep("express", "@nestjs", "ts-node")
        S["nodejs"] = sig(f, "scanner.deps", e)

    if "typescript" in lang.lower():
        S["typescript"] = sig(True, "scanner.language", lang)
    else:
        f, e = dep("typescript", "ts-jest", "tsconfig")
        S["typescript"] = sig(f, "scanner.deps", e)

    # Frameworks
    f,e = dep("express"); S["express"] = sig(f, "scanner.deps", e)
    f,e = dep("@nestjs/","nestjs"); S["nestjs"] = sig(f, "scanner.deps", e)
    f,e = dep("react","react-dom"); f2,e2 = bpl("react") if not f else (False,""); S["react"] = sig(f or f2, "scanner.deps or blueprint", e or e2)
    f,e = dep("expo","react-native"); S["expo"] = sig(f, "scanner.deps", e)
    f,e = dep("\"next\"","next.js"); S["nextjs"] = sig(f, "scanner.deps", e)

    # APIs
    f,e = dep("graphql","@apollo/","apollo-server"); f2,e2 = mpr("graphql") if not f else (False,""); S["graphql"] = sig(f or f2, "scanner.deps or mapper", e or e2)
    f,e = bpl("graphql federation","buildfederatedschema","apollo federation","@apollo/subgraph"); f2,e2 = dep("@apollo/federation","@apollo/subgraph") if not f else (False,""); S["graphql_federation"] = sig(f or f2, "blueprint or scanner.deps", e or e2)

    # Swagger: verifica deps + rotas /docs
    f,e = dep("swagger-ui-express","@nestjs/swagger","swagger-ui","swagger-jsdoc")
    if not f:
        for r in routes:
            if "docs" in r.get("path","").lower():
                f, e = True, f"route:{r['method']} {r['path']} ({r['file']})"
                break
    S["swagger"] = sig(f, "scanner.deps or layer_analysis.routes", e)

    f,e = dep("@grpc/","protobufjs","@grpc/proto-loader"); S["grpc"] = sig(f, "scanner.deps", e)

    # Databases
    f,e = dep("mongodb","mongoose"); f2,e2 = mpr("mongodb") if not f else (False,""); S["mongodb"] = sig(f or f2, "scanner.deps or mapper", e or e2)
    f,e = dep("pg","postgresql","typeorm","prisma","sequelize"); S["postgresql"] = sig(f, "scanner.deps", e)
    f,e = dep("redis","ioredis","cache-manager-redis"); S["redis"] = sig(f, "scanner.deps", e)
    f,e = dep("mssql","tedious"); S["mssql"] = sig(f, "scanner.deps", e)
    f,e = dep("@azure/cosmos","cosmosdb"); S["cosmosdb"] = sig(f, "scanner.deps", e)

    # Cloud / Infra
    has_docker = sc.get("has_docker", False) if sc.get("_ok") else False
    f,e = fil("dockerfile","docker-compose"); f2,e2 = mpr("docker") if not f else (False,"")
    S["docker"] = sig(has_docker or f or f2, "scanner.folder or files or mapper", f"has_docker={has_docker}" if has_docker else (e or e2))

    yaml_env = [f for f in files if ".yaml" in f and any(k in f for k in ["dev.","hml.","prd."])]
    f,e = bpl("kubernetes","k8s")
    S["kubernetes"] = sig(bool(yaml_env) or f, "scanner.files (env yamls) or blueprint",
                          f"{len(yaml_env)} env yamls" if yaml_env else e)

    f,e = dep("@azure/app-configuration"); f2,e2 = mpr("azure_appconfig") if not f else (False,""); S["azure_appconfig"] = sig(f or f2, "scanner.deps or mapper", e or e2)
    f,e = dep("@azure/keyvault","keyvault","@azure/identity"); f2,e2 = bpl("key vault","keyvault") if not f else (False,""); S["azure_keyvault"] = sig(f or f2, "scanner.deps or blueprint", e or e2)
    f,e = dep("@azure/service-bus","servicebus"); S["azure_servicebus"] = sig(f, "scanner.deps", e)
    f,e = dep("@azure/event-hubs","eventhubs"); S["azure_eventhubs"] = sig(f, "scanner.deps", e)
    f,e = dep("dotenv","dotenv-flow"); S["dotenv"] = sig(f, "scanner.deps", e)

    # Observability
    f,e = dep("dynatrace","dt-oneagent"); f2,e2 = mpr("dynatrace") if not f else (False,""); f3,e3 = bpl("dynatrace") if not (f or f2) else (False,""); S["dynatrace"] = sig(f or f2 or f3, "scanner.deps or mapper or blueprint", e or e2 or e3)
    f,e = dep("@elastic/apm","elastic-apm-node"); S["elastic_apm"] = sig(f, "scanner.deps", e)
    f,e = dep("@opentelemetry/","opentelemetry"); S["opentelemetry"] = sig(f, "scanner.deps", e)
    # APM agregado
    apm_found = S["dynatrace"]["found"] or S["elastic_apm"]["found"] or S["opentelemetry"]["found"]
    apm_ev = S["dynatrace"]["evidence"] or S["elastic_apm"]["evidence"] or S["opentelemetry"]["evidence"]
    S["apm"] = sig(apm_found, "derived: dynatrace|elastic_apm|opentelemetry", apm_ev)

    f,e = dep("pino","winston","bunyan","@dasa-logs/","dasa-logs","plte-log"); f2,e2 = bpl("logging estruturado","structured log","@dasa-logs") if not f else (False,""); S["structured_logging"] = sig(f or f2, "scanner.deps or blueprint", e or e2)

    health_routes = [r for r in routes if "health" in r.get("path","").lower() or "health" in r.get("file","").lower()]
    f,e = dep("@nestjs/terminus","terminus"); f2,e2 = bpl("health check","/server-health","readiness","liveness") if not f else (False,"")
    S["health_check"] = sig(bool(health_routes) or f or f2,
                             "layer_analysis.routes or scanner.deps or blueprint",
                             f"routes:{[r['path'] for r in health_routes]}" if health_routes else (e or e2))

    # Security
    f,e = dep("keycloak-connect","keycloak-js","keycloak-admin"); f2,e2 = mpr("keycloak") if not f else (False,""); f3,e3 = bpl("keycloak") if not (f or f2) else (False,""); S["keycloak"] = sig(f or f2 or f3, "scanner.deps or mapper or blueprint", e or e2 or e3)
    f,e = dep("passport","passport-jwt"); f2,e2 = mpr("passport") if not f else (False,""); S["passport"] = sig(f or f2, "scanner.deps or mapper", e or e2)
    f,e = dep("jsonwebtoken","@nestjs/jwt","jwks-rsa"); f2,e2 = mpr("jwt") if not f else (False,""); S["jwt"] = sig(f or f2, "scanner.deps or mapper", e or e2)
    f,e = dep("snyk","semgrep","checkmarx"); f2,e2 = fil(".snyk","snyk") if not f else (False,""); S["sast"] = sig(f or f2, "scanner.deps or files", e or e2)

    # CI/CD
    has_cicd = sc.get("has_cicd", False) if sc.get("_ok") else False
    f,e = fil("azure-pipelines","azure-pipelines.yml")
    S["azure_devops"] = sig(has_cicd or f, "scanner.folder.has_cicd or scanner.files", f"has_cicd={has_cicd}" if has_cicd else e)
    f,e = fil(".github/workflows","github-actions"); S["github_actions"] = sig(f, "scanner.files", e)
    f,e = bpl("argocd","argo cd","fluxcd","gitops"); S["gitops"] = sig(f, "blueprint", e)

    # Quality
    has_tests = sc.get("has_tests", False) if sc.get("_ok") else False
    f,e = dep("jest","jest-sonar","ts-jest","@types/jest"); f2,e2 = fil("jest.config") if not f else (False,""); f3,e3 = mpr("jest") if not (f or f2) else (False,"")
    S["jest"] = sig(has_tests or f or f2 or f3, "scanner.folder or deps or files or mapper",
                    f"has_tests={has_tests}" if has_tests else (e or e2 or e3))
    f,e = dep("@playwright/test","playwright"); S["playwright"] = sig(f, "scanner.deps", e)
    f,e = dep("supertest"); f2,e2 = mpr("supertest") if not f else (False,""); S["supertest"] = sig(f or f2, "scanner.deps or mapper", e or e2)
    f,e = fil("sonar-project.properties","sonar-project"); f2,e2 = dep("jest-sonar-reporter","sonarqube") if not f else (False,""); S["sonarqube"] = sig(f or f2, "scanner.files or scanner.deps", e or e2)

    # Architecture
    f,e = bpl("clean architecture","hexagonal","ports and adapters","domain layer"); S["clean_architecture"] = sig(f, "blueprint", e)
    f,e = bpl("domain-driven"," ddd","aggregate root","bounded context"); S["ddd"] = sig(f, "blueprint", e)
    f,e = bpl("event-driven","event sourcing","cqrs","pub/sub","message broker"); S["event_driven"] = sig(f, "blueprint", e)

    # Documentation
    has_docs = sc.get("has_docs", False) if sc.get("_ok") else False
    f,e = bpl("getting started","como executar","how to run","pré-requisitos","prerequisites")
    S["readme_documented"] = sig(has_docs or f, "scanner.folder.has_docs or blueprint", f"has_docs={has_docs}" if has_docs else e)
    f,e = bpl("architecture decision record","decision record","docs/adr","/adr/"); S["adr"] = sig(f, "blueprint", e)

    return S


# ─────────────────────────────────────────────────────────────────────────────
# SCORES DE DIMENSÃO
# ─────────────────────────────────────────────────────────────────────────────
def score_dimension(signals, dim):
    relevant = DIMENSIONS.get(dim, [])
    if not relevant:
        return {"score": 0.0, "found": 0, "total": 0, "calc": "N/A"}
    found = [s for s in relevant if signals.get(s, {}).get("found", False)]
    score = round(len(found) / len(relevant) * 5, 2)
    return {
        "score": score, "found": len(found), "total": len(relevant),
        "signals_found": found, "signals_missing": [s for s in relevant if s not in found],
        "calc": f"{len(found)}/{len(relevant)} × 5 = {score}",
    }


# ─────────────────────────────────────────────────────────────────────────────
# PARSE COMPLETO DE UM APP
# ─────────────────────────────────────────────────────────────────────────────
def parse_app(project, txt_path, blueprint_path):
    name = txt_path.stem
    warnings = []

    txt = txt_path.read_text(encoding="utf-8", errors="replace") if txt_path.exists() else ""
    if not txt:
        warnings.append(f".txt não encontrado: {txt_path}")

    bp = ""
    if blueprint_path and blueprint_path.exists():
        bp = blueprint_path.read_text(encoding="utf-8", errors="replace")
    else:
        warnings.append(f"Blueprint não encontrado (procurado em: {blueprint_path})")

    sections = extract_sections(txt)
    sc = parse_scanner(sections.get("scanner"))
    mp = parse_mapper(sections.get("integration_mapper"))
    ly = parse_layers(sections.get("layer_analysis"))
    signals = detect_signals(sc, mp, ly, bp)

    dim_scores = {d: score_dimension(signals, d) for d in DIMENSIONS}
    critical_gaps = [
        {"signal": k, "label": k.replace("_"," ").title()}
        for k in CRITICAL_SIGNALS if not signals.get(k, {}).get("found", False)
    ]
    found_list = [k for k,v in signals.items() if v.get("found")]
    not_found  = [k for k,v in signals.items() if not v.get("found")]

    return {
        "app_name": name, "project": project,
        "sources_read": [str(p) for p in [txt_path, blueprint_path] if p and Path(str(p)).exists()],
        "parse_warnings": warnings,
        "is_empty_repo": sc.get("is_empty", False),
        "scanner": sc, "integration_mapper": mp, "layer_analysis": ly,
        "signals": signals,
        "signals_summary": {
            "total_checked": len(signals),
            "total_found": len(found_list),
            "found": found_list, "not_found": not_found,
        },
        "dimension_scores": dim_scores,
        "critical_gaps": critical_gaps,
        "critical_gap_count": len(critical_gaps),
    }


# ─────────────────────────────────────────────────────────────────────────────
# AGREGAÇÃO DO PORTFÓLIO
# ─────────────────────────────────────────────────────────────────────────────
def aggregate(apps):
    total = len(apps)
    all_keys = list(apps[0]["signals"].keys()) if apps else []

    coverage = {}
    for key in all_keys:
        with_list, without_list = [], []
        for a in apps:
            s = a["signals"].get(key, {})
            if s.get("found"):
                with_list.append({"app": a["app_name"], "project": a["project"],
                                   "source": s.get("source",""), "evidence": s.get("evidence","")})
            else:
                without_list.append(a["app_name"])
        cw = len(with_list)
        coverage[key] = {
            "label": key.replace("_"," ").title(),
            "count_with": cw, "count_without": total - cw, "total": total,
            "pct_with":    round(cw / total * 100, 1) if total else 0,
            "pct_without": round((total - cw) / total * 100, 1) if total else 0,
            "apps_with":    with_list,
            "apps_without": without_list,
        }

    dim_avg = {}
    for dim, keys in DIMENSIONS.items():
        scores = [a["dimension_scores"][dim]["score"] for a in apps]
        avg = round(sum(scores) / len(scores), 2) if scores else 0
        parts = [f"{coverage.get(k,{}).get('label',k)}: {coverage.get(k,{}).get('pct_with',0)}%" for k in keys]
        avg_pct = round(sum(coverage.get(k,{}).get("pct_with",0) for k in keys) / len(keys), 1) if keys else 0
        dim_avg[dim] = {
            "avg_score": avg, "avg_coverage_pct": avg_pct, "signals": keys,
            "per_signal": parts,
            "calc": f"({' + '.join(parts)}) / {len(keys)} = {avg_pct}% → {avg}/5",
        }

    by_project = defaultdict(list)
    for a in apps:
        by_project[a["project"]].append(a["app_name"])

    top_debt = sorted(apps, key=lambda a: a["critical_gap_count"], reverse=True)[:15]

    return {
        "generated_at": datetime.now().isoformat(),
        "total_apps": total,
        "total_projects": len(by_project),
        "projects": dict(by_project),
        "empty_repos": [a["app_name"] for a in apps if a["is_empty_repo"]],
        "empty_repos_count": sum(1 for a in apps if a["is_empty_repo"]),
        "signal_coverage": coverage,
        "dimension_averages": dim_avg,
        "top_debt_apps": [
            {"app": a["app_name"], "project": a["project"],
             "critical_gap_count": a["critical_gap_count"],
             "critical_gaps": [g["signal"] for g in a["critical_gaps"]],
             "is_empty_repo": a["is_empty_repo"]}
            for a in top_debt
        ],
        "apps": apps,
    }


# ─────────────────────────────────────────────────────────────────────────────
# RESUMO MARKDOWN AUDITÁVEL
# ─────────────────────────────────────────────────────────────────────────────
def summary_md(portfolio):
    L = [
        "# Portfolio Summary — Extração Determinística",
        f"**Gerado em:** {portfolio['generated_at']}",
        f"**Total:** {portfolio['total_apps']} apps em {portfolio['total_projects']} projetos\n",
    ]
    for proj, apps in portfolio["projects"].items():
        L.append(f"**{proj}** ({len(apps)} apps): " + ", ".join(apps))
    L.append("")

    if portfolio["empty_repos"]:
        L += ["\n## ⚠️ Repos Vazios\n",
              "> Gaps podem estar sub-reportados. Validação manual necessária.\n"]
        L += [f"- {r}" for r in portfolio["empty_repos"]]
        L.append("")

    L += ["\n## Cobertura — Sinais Críticos\n",
          "| Sinal | Com ✅ | Sem ❌ | Total | % Com | % Sem |",
          "|-------|--------|--------|-------|-------|-------|"]
    for key in CRITICAL_SIGNALS:
        c = portfolio["signal_coverage"].get(key, {})
        L.append(f'| {c.get("label",key)} | {c.get("count_with",0)} | {c.get("count_without",0)} | {c.get("total",0)} | {c.get("pct_with",0)}% | {c.get("pct_without",0)}% |')

    L += ["\n## Cobertura Completa\n",
          "| Sinal | Com ✅ | Sem ❌ | Total | % Com | Apps com sinal |",
          "|-------|--------|--------|-------|-------|----------------|"]
    for key, c in portfolio["signal_coverage"].items():
        apps_str = ", ".join(e["app"] for e in c["apps_with"]) or "—"
        L.append(f'| {c.get("label",key)} | {c["count_with"]} | {c["count_without"]} | {c["total"]} | {c["pct_with"]}% | {apps_str} |')

    L += ["\n## Scores de Maturidade\n",
          "| Dimensão | Score /5 | Cobertura Média | Cálculo |",
          "|----------|---------|-----------------|---------|"]
    for dim, d in portfolio["dimension_averages"].items():
        L.append(f'| {dim.capitalize()} | {d["avg_score"]} | {d["avg_coverage_pct"]}% | {d["calc"]} |')

    L += ["\n## Top Apps por Débito Técnico\n",
          "| # | App | Projeto | Gaps Críticos | Gaps Ausentes |",
          "|---|-----|---------|--------------|---------------|"]
    for i, a in enumerate(portfolio["top_debt_apps"], 1):
        gaps = ", ".join(a["critical_gaps"]) or "—"
        flag = " ⚠️" if a["is_empty_repo"] else ""
        L.append(f'| {i} | {a["app"]}{flag} | {a["project"]} | {a["critical_gap_count"]} | {gaps} |')

    L.append("\n## Detalhe por App\n")
    for a in portfolio["apps"]:
        L.append(f"### {a['app_name']} ({a['project']})")
        if a["is_empty_repo"]: L.append("> ⚠️ Repo vazio")
        for w in a.get("parse_warnings", []): L.append(f"> ⚠️ {w}")
        dim_str = " | ".join(f"{d.capitalize()}: {v['score']}/5" for d, v in a["dimension_scores"].items())
        L.append(f"**Scores:** {dim_str}")
        L.append(f"**Sinais encontrados ({a['signals_summary']['total_found']}):** " + ", ".join(a["signals_summary"]["found"]))
        if a["critical_gaps"]:
            L.append(f"**Gaps críticos ({a['critical_gap_count']}):** " + ", ".join(g["signal"] for g in a["critical_gaps"]))
        else:
            L.append("**Gaps críticos:** nenhum ✅")

        # Evidências dos sinais encontrados
        L.append("\n**Evidências dos sinais detectados:**")
        for k in a["signals_summary"]["found"]:
            s = a["signals"][k]
            L.append(f"- `{k}` | fonte: {s.get('source','')} | evidência: {s.get('evidence','')[:100]}")
        L.append("")

    return "\n".join(L)


# ─────────────────────────────────────────────────────────────────────────────
# DISCOVERY
# ─────────────────────────────────────────────────────────────────────────────
def discover(base_dir):
    base = Path(base_dir)
    found = []
    for proj_dir in sorted(base.iterdir()):
        if not proj_dir.is_dir() or proj_dir.name == "json":
            continue
        for txt in sorted(proj_dir.glob("*.txt")):
            stem = txt.stem
            bp = next((p for p in [
                proj_dir / "blueprints" / f"{stem}_blueprint.md",
                proj_dir / f"{stem}_blueprint.md",
                proj_dir / "blueprints" / f"{stem}.md",
            ] if p.exists()), None)
            found.append({"project": proj_dir.name, "stem": stem, "txt": txt, "bp": bp})
    return found


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-dir", default="outputs")
    p.add_argument("--out",      default="outputs/portfolio_structured.json")
    p.add_argument("--summary",  default="outputs/portfolio_summary.md")
    args = p.parse_args()

    print("=" * 70)
    print("📦 BLUEPRINT EXTRACTOR — Parser Determinístico")
    print("=" * 70)

    entries = discover(args.base_dir)
    if not entries:
        print(f"❌ Nenhum .txt em '{args.base_dir}'")
        return

    print(f"\n🔍 {len(entries)} app(s) descoberto(s):")
    for e in entries:
        bp_ok = "✅ blueprint" if e["bp"] else "⚠️  sem blueprint"
        print(f"   {e['project']}/{e['stem']}  [{bp_ok}]")

    print("\n📄 Processando...")
    apps = []
    for e in entries:
        a = parse_app(e["project"], e["txt"], e["bp"])
        status = "⚠️  VAZIO" if a["is_empty_repo"] else "✅"
        print(f"   {status} {a['app_name']}: "
              f"{a['signals_summary']['total_found']}/{a['signals_summary']['total_checked']} sinais | "
              f"{a['critical_gap_count']} gap(s) crítico(s)")
        for w in a["parse_warnings"]:
            print(f"         ⚠️  {w}")
        apps.append(a)

    print("\n📊 Agregando...")
    portfolio = aggregate(apps)

    out = Path(args.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(portfolio, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"   ✅ JSON: {out} ({out.stat().st_size:,} bytes)")

    sm = Path(args.summary)
    sm.write_text(summary_md(portfolio), encoding="utf-8")
    print(f"   ✅ MD:   {sm}")

    print("\n📈 Cobertura crítica:")
    for key in CRITICAL_SIGNALS:
        c = portfolio["signal_coverage"].get(key, {})
        pct = c.get("pct_with", 0)
        bar = "█" * int(pct/10) + "░" * (10 - int(pct/10))
        print(f"   {bar} {pct:5.1f}%  {c.get('label',key)} ({c.get('count_with',0)}/{c.get('total',0)})")

    print(f"\n✅ Concluído! Próximo passo:")
    print(f"   python gap_analyzer_v3.py --portfolio {out}")

if __name__ == "__main__":
    main()