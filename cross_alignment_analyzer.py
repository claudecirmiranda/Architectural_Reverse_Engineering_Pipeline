import os
import time
from pathlib import Path
from datetime import datetime
import anthropic

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-20250514"

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY não configurada.")


class CrossAlignmentAnalyzer:
    """
    Analisa alinhamento e tensões entre:
    - Concept NAV 360
    - Modelo TO-BE
    - Análise de GAP
    - Roadmap de Adoção
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def find_latest_files(self, base_dir: str = "outputs") -> dict:
        base = Path(base_dir)

        files = {
            "concept": list(base.glob("Concept_NAV_360_Transcript_Analysis_*.md")),
            "to_be": list(base.glob("TO_BE_Model_*.md")),
            "gap": list(base.glob("Gap_Analysis_*.md")),
            "roadmap": list(base.glob("Adoption_Roadmap_*.md")),
        }

        latest = {}
        for key, items in files.items():
            if not items:
                raise FileNotFoundError(f"Arquivo {key} não encontrado em {base_dir}")
            latest[key] = max(items, key=lambda p: p.stat().st_mtime)

        return latest

    def summarize(self, content: str, max_lines: int = 800) -> str:
        lines = content.splitlines()
        summary = []
        for line in lines[:max_lines]:
            if line.strip() and (
                line.startswith("#")
                or "gap" in line.lower()
                or "onda" in line.lower()
                or "intenção" in line.lower()
                or "risco" in line.lower()
                or "arquitet" in line.lower()
            ):
                summary.append(line)
        return "\n".join(summary)

    def generate_cross_analysis(
        self,
        concept_summary: str,
        to_be_summary: str,
        gap_summary: str,
        roadmap_summary: str,
    ) -> str | None:

        prompt = f"""
Você é um Consultor Sênior de Estratégia Digital e Arquitetura Corporativa.

Sua missão é REALIZAR UMA ANÁLISE CRUZADA entre quatro artefatos formais,
com o objetivo de identificar ALINHAMENTOS, TENSÕES, ASSUNÇÕES IMPLÍCITAS
e RISCOS ESTRATÉGICOS.

⚠️ Este trabalho NÃO cria soluções, NÃO redefine arquitetura e NÃO altera roadmap.
Ele apenas ANALISA e EXPLÍCITA relações e desalinhamentos.

# REGRAS OBRIGATÓRIAS (ANTI-ALUCINAÇÃO)

1. NÃO inventar fatos, decisões ou intenções
2. NÃO assumir causalidade onde só há correlação
3. NÃO corrigir ou “melhorar” os artefatos
4. NÃO propor soluções técnicas
5. Usar linguagem analítica, neutra e rastreável
6. Toda afirmação deve referenciar claramente o artefato de origem
7. Se algo não puder ser determinado, declarar explicitamente

# ARTEFATO 1 — CONCEPT NAV 360 (Resumo)
{concept_summary}

# ARTEFATO 2 — MODELO TO-BE (Resumo)
{to_be_summary}

# ARTEFATO 3 — ANÁLISE DE GAP (Resumo)
{gap_summary}

# ARTEFATO 4 — ROADMAP DE ADOÇÃO (Resumo)
{roadmap_summary}

Gere um documento em Markdown com EXATAMENTE as seções abaixo,
na ordem definida, sem criar seções adicionais.

---

## 1. SUMÁRIO EXECUTIVO DE ALINHAMENTO
Visão geral do nível de alinhamento entre intenção estratégica, direcionamento futuro,
lacunas identificadas e plano de execução.

## 2. ALINHAMENTOS CLAROS ENTRE OS ARTEFATOS
Liste pontos onde há coerência explícita entre Concept, TO-BE, GAP e Roadmap.

## 3. TENSÕES E POTENCIAIS DESALINHAMENTOS
Identifique onde:
- O Roadmap avança além do Concept
- O TO-BE formaliza algo não intencionado
- Gaps reconhecidos não são tratados

## 4. ASSUNÇÕES IMPLÍCITAS IDENTIFICADAS
Liste decisões implícitas assumidas em algum artefato
que não foram explicitamente declaradas no Concept.

## 5. GAPS DECLARADOS VS INICIATIVAS PLANEJADAS
Analise se os gaps mapeados estão:
- Totalmente endereçados
- Parcialmente endereçados
- Não endereçados

## 6. RISCOS ESTRATÉGICOS DE EXECUÇÃO
Riscos que emergem da combinação dos artefatos,
especialmente relacionados a:
- Arquitetura
- Governança
- Dependências externas
- Complexidade organizacional

## 7. PONTOS QUE REQUEREM DECISÃO EXECUTIVA
Liste temas que claramente exigem decisão formal,
com base nas tensões identificadas.

## 8. LIMITAÇÕES DA ANÁLISE
Explique limites do exercício com base na natureza dos artefatos.

Use linguagem executiva, analítica e objetiva.
"""

        try:
            message = self.client.messages.create(
                model=MODEL,
                max_tokens=12000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip()

        except Exception as e:
            print(f"❌ Erro ao gerar cross-analysis: {e}")
            return None

    def save(self, content: str, output_dir: str = "outputs") -> Path:
        output = Path(output_dir)
        output.mkdir(exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = output / f"Cross_Analysis_Concept_TOBE_GAP_Roadmap_{ts}.md"

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path

    def generate(self):
        print("=" * 80)
        print("🔎 CROSS-AGENT — ALINHAMENTO ESTRATÉGICO")
        print("=" * 80)

        files = self.find_latest_files()
        print("\n📂 Artefatos encontrados:")
        for k, v in files.items():
            print(f"  ✅ {k}: {v.name}")

        contents = {}
        for k, path in files.items():
            with open(path, "r", encoding="utf-8") as f:
                contents[k] = f.read()

        summaries = {
            "concept": self.summarize(contents["concept"], 900),
            "to_be": self.summarize(contents["to_be"], 800),
            "gap": self.summarize(contents["gap"], 1000),
            "roadmap": self.summarize(contents["roadmap"], 900),
        }

        print("\n🧠 Gerando análise cruzada...")
        analysis = self.generate_cross_analysis(
            summaries["concept"],
            summaries["to_be"],
            summaries["gap"],
            summaries["roadmap"],
        )

        if not analysis:
            print("❌ Falha na análise cruzada")
            return

        path = self.save(analysis)

        print("\n✅ Cross-analysis concluída!")
        print(f"📄 Arquivo: {path}")
        print(f"📊 Tamanho: {len(analysis):,} caracteres")

        print("\n🎯 Documento pronto para:")
        print("   - Steering Committee")
        print("   - Decisão Executiva")
        print("   - Ajustes conscientes de Roadmap")
        print("=" * 80)


def main():
    try:
        CrossAlignmentAnalyzer().generate()
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
