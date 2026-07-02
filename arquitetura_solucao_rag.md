# Arquitetura da Solução — Knowledge Base Inteligente com RAG
**POC Devolução de Clientes — Grupo Santa Cruz × FCamara**
Versão: 3.0 | Data: Julho/2026 | Classificação: Uso interno restrito

---

## 1. Visão Geral

A solução extrai conhecimento implícito do código-fonte legado dos sistemas do Grupo Santa Cruz e o disponibiliza para consulta em linguagem natural via agente RAG.

```mermaid
flowchart TB
    subgraph FONTES["Fontes de Código"]
        A1[PFAT PL/SQL\nOracle]
        A2[PFAT Java\nSpring]
        A3[SISFAT\nCOBOL]
        A4[DevWeb\nTypeScript/Java]
    end

    subgraph PIPELINE["Pipeline de Extração"]
        B1[Estágio 1\nColeta]
        B2[Estágio 2\nParsing]
        B3[Estágio 3\nExtração LLM]
        B4[Estágio 4\nArtefatos]
    end

    subgraph RAG["RAG Engine"]
        C1[Chunking\nMarkdown]
        C2[Embedding\nnomic-embed-text]
        C3[ChromaDB\nCosine Similarity]
        C4[LLM\nSymphony/NVIDIA/Ollama]
    end

    subgraph INTERFACES["Interfaces"]
        D1[API REST\nFastAPI]
        D2[Chat Web\nHTML/JS]
    end

    FONTES --> B1 --> B2 --> B3 --> B4
    B4 --> C1 --> C2 --> C3
    C3 --> C4
    C4 --> D1
    D1 --> D2
```

---

## 2. Pipeline de Extração — 4 Estágios

### 2.1 Visão sequencial

```mermaid
sequenceDiagram
    participant AZ as Azure DevOps
    participant E1 as Estágio 1 Coleta
    participant E2 as Estágio 2 Parsing
    participant E3 as Estágio 3 LLM
    participant E4 as Estágio 4 Artefatos
    participant KB as Knowledge Base

    AZ->>E1: PAT read-only (5 repos)
    E1->>E1: 10.703 arquivos coletados
    E1->>E2: output/raw/
    E2->>E2: 4 parsers por linguagem
    E2->>E3: 62.361 chunks JSONL
    E3->>E3: Filtro cirúrgico → 4.199 chunks
    E3->>E3: 4 prompts especializados via Symphony
    E3->>E4: 5.600 extrações JSONL
    E4->>KB: 10 documentos Markdown
```

### 2.2 Estágio 1 — Coleta

```mermaid
flowchart TD
    PAT[PAT Azure DevOps\nread-only] --> COL[azure_client.py]
    GOGS[Token Gogs\nVPN] --> GOG[gogs_client.py]
    COL --> REPO1[SISFAT\n2.276 arquivos]
    COL --> REPO2[PFAT PL/SQL\n1.322 arquivos]
    COL --> REPO3[PFAT Java Legado\n6.918 arquivos]
    COL --> REPO4[DevWeb\n1.854 arquivos]
    GOG --> REPO5[PFAT Java Producao\npendente VPN]
    REPO1 & REPO2 & REPO3 & REPO4 --> RAW[output/raw/\n10.703 arquivos\n0 erros]
```

**Decisões técnicas:**
- PAT por repositório — DevWeb tem PAT dedicado diferente dos demais
- `scope_path` por repo — restringe coleta ao diretório de produção
- Fallback de encoding UTF-8 → latin-1 para arquivos COBOL legados
- Suporte a arquivos sem extensão (91 arquivos COBOL AcuCOBOL)

### 2.3 Estágio 2 — Parsing

```mermaid
flowchart LR
    RAW[output/raw/] --> R1[cobol_parser.py\nAcuCOBOL\nregex por divisão]
    RAW --> R2[plsql_parser.py\nOracle PL/SQL\nBEGIN/END balanceado]
    RAW --> R3[java_parser.py\nJava/Spring\njavalang + regex]
    RAW --> R4[tsql_parser.py\nT-SQL SQL Server\nregex]
    RAW --> R5[typescript_parser.py\nTypeScript/Angular\nregex]
    R1 & R2 & R3 & R4 & R5 --> NORM[normalizer.py\nSchema único JSON]
    NORM --> CHUNKS[output/chunks/\n62.361 chunks JSONL\n0 erros]
```

**Volumes por sistema:**

| Sistema | Arquivos | Chunks | Parser |
|---|---|---|---|
| SISFAT (COBOL) | 2.276 | 39.593 | regex AcuCOBOL |
| PFAT Java | 7.105 | 20.106 | javalang + fallback |
| PFAT PL/SQL | 1.322 | 2.662 | sqlparse + BEGIN/END balanceado |
| DevWeb | 1.854 | 2.478 | typescript + java + tsql |

**Descobertas na fase de parsing:**
- SISFAT identificado como COBOL AcuCOBOL (não Java como descrito inicialmente)
- Extensões não convencionais: `.fd` (FILE DESCRIPTION), `.sl` (SELECT), `.cbl/.cob/.mod`
- PFAT PL/SQL: problema inicial de 83% UNKNOWN corrigido com captura balanceada BEGIN/END
- 2.779 chunks de comentários COBOL descartados pelo normalizer

### 2.4 Estágio 3 — Extração via LLM

```mermaid
flowchart TD
    CHUNKS[62.361 chunks] --> FILTER[Filtro cirúrgico\npor sistema + keywords]
    FILTER --> |4.199 chunks| PROMPTS

    subgraph PROMPTS["4 Prompts Especializados"]
        P1[Regras de Negócio\nO que o código implementa]
        P2[Integrações\nSistemas e protocolos]
        P3[Gaps e Riscos\nProcessos manuais]
        P4[Glossário\nTermos técnicos]
    end

    PROMPTS --> SYM[Symphony FCamara\nazure.gpt-5.4-mini\nProvider único por segurança]
    SYM --> EXT[output/extracted/\n5.600 extrações JSONL]
```

**Filtro cirúrgico por sistema:**

| Sistema | Total chunks | Após filtro | Redução |
|---|---|---|---|
| PFAT PL/SQL | 2.662 | 422 | 84% |
| PFAT Java | 20.106 | 2.333 | 88% |
| SISFAT | 39.593 | 1.444 | 96% |
| DevWeb | 2.478 | 246 | 90% |

**Decisão de segurança:** Symphony FCamara exclusivo como provider LLM no pipeline de extração — instância dedicada, DPA contratual com o Grupo SC, dados nunca saem em código bruto (parser sanitiza antes do envio).

**Checkpoint por chunk** — retomada automática em caso de interrupção (token expirado, timeout, Ctrl+C).

### 2.5 Estágio 4 — Geração de Artefatos

```mermaid
flowchart LR
    EXT[5.600 extrações\nJSONL] --> G1[01 Value Stream\nTécnico]
    EXT --> G2[02 Catálogo\nRegras CSV]
    EXT --> G3[03 Mapa\nIntegrações]
    EXT --> G4[04 Gaps e\nWorkarounds]
    EXT --> G5[05 Glossário\nde Termos]
    EXT --> KB[knowledge_base/\n10 arquivos Markdown\npor sistema]

    KB --> |upload| CHROMA[ChromaDB\nRAG Engine]
```

**Artefatos gerados — volumes finais (4 sistemas):**

| Artefato | Entradas |
|---|---|
| 01 Value Stream Técnico | 10.326 regras |
| 02 Catálogo de Regras (CSV) | 10.250 regras |
| 03 Mapa de Integrações | 3.190 integrações |
| 04 Gaps e Workarounds | 9.806 gaps/riscos |
| 05 Glossário de Termos | 14.441 termos |

**Pasta knowledge_base/ — gerada deterministicamente:**
```
output/artifacts/knowledge_base/
├── 02_Regras_PFAT_PLSQL.md     (387 regras)
├── 02_Regras_PFAT_Java.md      (6.285 regras)
├── 02_Regras_SISFAT.md         (3.198 regras)
├── 02_Regras_DevWeb.md         (380 regras)
├── 04_Gaps_PFAT_PLSQL.md
├── 04_Gaps_PFAT_Java.md
├── 04_Gaps_SISFAT.md
├── 04_Gaps_DevWeb.md
├── 03_Map_Integracoes_Impacto.md
└── 05_Glossario_Termos.md
```

---

## 3. RAG Engine

### 3.1 Arquitetura de indexação

```mermaid
flowchart TD
    MD[knowledge_base/\n10 arquivos .md] --> SPLIT[MarkdownTextSplitter\n1.000 chars / 150 overlap]
    SPLIT --> |21.357 chunks| EMB[nomic-embed-text\nvia Ollama local\n768 dimensões]
    EMB --> CHROMA[(ChromaDB\nCosine Similarity\nPersistente em disco)]
    CHROMA --> |checkpoint| CP[indexing_checkpoint.json\nretomada automática]
```

**Decisões de indexação:**
- `MarkdownTextSplitter` em vez de splitter genérico — respeita estrutura de seções `###`
- Cosine similarity em vez de L2 — normaliza vetores, valores entre 0-2 independente da dimensão
- Checkpoint por batch de 100 chunks — retomada se Ollama cair durante indexação
- 21.357 chunks totais indexados

### 3.2 Fluxo de consulta

```mermaid
sequenceDiagram
    participant U as Usuário
    participant API as FastAPI
    participant EMB as Ollama\nnomic-embed-text
    participant VDB as ChromaDB
    participant LLM as LLM Provider

    U->>API: POST /consultar {pergunta, perfil, historico}
    API->>EMB: embed(pergunta)
    EMB-->>API: vetor 768 dims
    API->>VDB: query(vetor, top_k=6)
    VDB-->>API: chunks + metadados + distâncias
    API->>API: monta contexto + prompt
    API->>LLM: prompt com chunks relevantes
    LLM-->>API: resposta com citações
    API-->>U: {resposta, fontes, chunks_usados, tempo_ms}
```

### 3.3 Seleção de provider LLM

```mermaid
flowchart TD
    START[Consulta recebida] --> CHECK_SYM{SYMPHONY_TOKEN\ndefinido?}
    CHECK_SYM --> |Sim| SYM[Symphony FCamara\nazure.gpt-5.4-mini\n~15-20s]
    CHECK_SYM --> |Não| CHECK_NV{NVIDIA_API_KEY\ndefinido?}
    CHECK_NV --> |Sim| NV[NVIDIA NIM\ndeepseek-v4-flash\n~15-20s]
    CHECK_NV --> |Não| OLL[Ollama local\nqwen2.5:7b\n~2-4 min]

    SYM & NV & OLL --> RESP[Resposta com citação de fonte]
```

**Importante:** o embedding é **sempre local** via Ollama (`nomic-embed-text`) — os chunks da base de conhecimento nunca saem da máquina. Só o prompt com os trechos já recuperados vai para o provider externo.

### 3.4 Prompt de consulta

```
Sistema: Você é o assistente de conhecimento técnico do processo de
Devolução de Clientes do Grupo Santa Cruz.

Regras:
1. Cite sempre a fonte (sistema e arquivo de origem)
2. Se não estiver nos trechos, diga claramente
3. Não avalie qualidade de código
4. Destaque gaps e riscos quando relevantes

Contexto (chunks recuperados):
[Fonte: 02_Regras_PFAT_Java.md, Sistema: PFAT_Java]
{chunk_1}
---
[Fonte: 04_Gaps_SISFAT.md, Sistema: SISFAT]
{chunk_2}
...

Pergunta: {pergunta_do_usuario}
```

---

## 4. API REST

```mermaid
flowchart LR
    CW[chat_web.html] --> |POST /consultar| API[FastAPI\napi_proxy.py\n:8000]
    SYS[Sistemas externos] --> |POST /consultar| API
    API --> |GET /health| HEALTH[Status + Stats]
    API --> |POST /admin/reindex| REINDEX[Re-indexa KB]
    API --> RAG[rag_engine.py]
    RAG --> EMB[Ollama\nEmbedding]
    RAG --> LLM[Provider LLM\nSymphony/NVIDIA/Ollama]
    RAG --> VDB[(ChromaDB)]
```

**Endpoints:**

| Método | Endpoint | Descrição |
|---|---|---|
| GET | `/health` | Status da API e stats do RAG (chunks indexados, provider ativo) |
| POST | `/consultar` | Envia pergunta, retorna resposta com fontes |
| POST | `/admin/reindex` | Re-indexa documentos após atualizar artefatos |

**Request /consultar:**
```json
{
  "pergunta": "O que valida o CFOP na devolução?",
  "perfil": "TI",
  "historico": []
}
```

**Response /consultar:**
```json
{
  "resposta": "O CFOP é validado pela rotina NfEspecialCore.validarCFOP... [Fonte: 02_Regras_PFAT_Java.md]",
  "fontes": [{"source": "02_Regras_PFAT_Java.md", "sistema": "PFAT_Java", "distancia": 0.21}],
  "chunks_usados": 6,
  "tempo_ms": 15139,
  "fonte_disponivel": true
}
```

---

## 5. Chat Web

```mermaid
flowchart TD
    U[Usuário] --> CW[chat_web.html\nstandalone HTML]
    CW --> SEL[Seletor de perfil\nNegócio / TI / Operação]
    CW --> INP[Campo de pergunta\n+ sugestões rápidas]
    INP --> |fetch POST /consultar| API[API REST :8000]
    API --> CW
    CW --> BUBBLE[Bolha de resposta\ncom badge de fonte]
    CW --> HIST[Histórico de conversa\núltimas 5 trocas]
```

**Características:**
- HTML standalone — abre direto no browser sem servidor web
- Seletor de perfil (Negócio / TI / Operação) — contextualiza o LLM
- Histórico de conversa mantido no browser (últimas 5 trocas)
- Badge visual quando resposta não tem citação de fonte
- Sugestões de prompt pré-configuradas por caso de uso

---

## 6. Decisões Arquiteturais — Resumo

| Decisão | Escolha | Motivação |
|---|---|---|
| Provider LLM extração | Symphony FCamara exclusivo | DPA contratual, instância dedicada, segurança |
| Provider LLM RAG | Symphony > NVIDIA > Ollama | Prioridade por disponibilidade |
| Embedding | nomic-embed-text local | Zero egress — chunks nunca saem da máquina |
| Vector store | ChromaDB persistente | Local, sem servidor separado, cosine similarity |
| Similarity metric | Cosine | Normaliza vetores 768 dims, valores intuitivos 0-2 |
| Chunking | MarkdownTextSplitter 1.000/150 | Respeita estrutura semântica dos artefatos |
| Filtro de chunks | TOP_K=6 sem filtro artificial | Fonte da verdade sem diversidade forçada |
| Checkpoint indexação | Por batch de 100 | Retomada automática se Ollama cair |
| Parsers | 1 por linguagem, schema único | COBOL/PL-SQL/Java/TypeScript/T-SQL |

---

## 7. Estrutura de Arquivos

```
scanner/
├── config/settings.py              # PAT, tokens, modelos, extensões
├── src/
│   ├── collector/                  # Estágio 1
│   │   ├── azure_client.py
│   │   ├── gogs_client.py
│   │   └── collector.py
│   ├── parser/                     # Estágio 2
│   │   ├── cobol_parser.py
│   │   ├── plsql_parser.py
│   │   ├── java_parser.py
│   │   ├── tsql_parser.py
│   │   ├── typescript_parser.py
│   │   └── stage2_parser.py
│   ├── normalizer/
│   │   └── normalizer.py
│   ├── extractor/                  # Estágio 3
│   │   ├── symphony_client.py
│   │   ├── nvidia_client.py
│   │   ├── ollama_client.py
│   │   ├── llm_router.py
│   │   ├── prompts.py
│   │   └── stage3_extractor.py
│   └── generator/                  # Estágio 4
│       └── stage4_generator.py
├── output/
│   ├── raw/                        # Arquivos brutos
│   ├── chunks/                     # Chunks JSONL
│   ├── extracted/                  # Extrações LLM
│   ├── artifacts/                  # Artefatos finais
│   │   └── knowledge_base/         # 10 .md para RAG
│   └── chromadb/                   # Índice vetorial
├── rag_engine.py                   # Motor RAG
├── api_proxy.py                    # API REST FastAPI
├── validate_connection.py
├── run_scan.py
└── requirements.txt

chat_web.html                       # Frontend standalone
```

---

## 8. Métricas da POC

| Métrica | Valor |
|---|---|
| Arquivos coletados | 10.703 |
| Chunks gerados | 62.361 |
| Chunks enviados ao LLM | 4.199 (filtro -93%) |
| Extrações geradas | 5.600 |
| Regras de negócio | 10.250 |
| Integrações mapeadas | 3.190 |
| Gaps e riscos | 9.806 |
| Termos no glossário | 14.441 |
| Chunks no índice RAG | 21.357 |
| Taxa de relevância LLM | ~90% |
| Tempo de resposta RAG | 15-20s (Symphony/NVIDIA) |

---

## 9. Pendências em Aberto

| Item | Status | Ação |
|---|---|---|
| Bug Symphony — agente KB | Reportado ao time FCamara | Testar quando corrigido |
| Acesso Gogs via VPN | Pendente com infra GrupoSC | PFAT Java produção atual |
| Validação com especialistas | Pendente | Erika/Heloisa (PL/SQL), Marcos Jioti/Paulo Paduani (SISFAT) |
| Deploy produção | Pendente | Hardware adequado para embedding local |

---

*FCamara × Grupo Santa Cruz — uso interno restrito*
