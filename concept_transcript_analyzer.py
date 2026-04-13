import os
import time
from pathlib import Path
from typing import Dict
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


class ConceptTranscriptAnalyzer:
    """
    Analisa transcrições de reuniões/workshops (txt) e gera
    um artefato estruturado de Concept para análise posterior
    junto a TO-BE, GAP e Roadmap.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def find_latest_transcript(self, base_dir: str = "inputs") -> Path | None:
        """Localiza o arquivo de transcrição mais recente."""
        base_path = Path(base_dir)
        transcripts = list(base_path.glob("*.txt"))
        if not transcripts:
            return None
        return max(transcripts, key=lambda p: p.stat().st_mtime)

    def summarize_transcript(self, content: str, max_lines: int = 1200) -> str:
        """
        Cria um resumo fiel da transcrição para caber no contexto,
        preservando falas relevantes, intenções e exclusões.
        """
        lines = content.splitlines()
        summary = []

        for line in lines[:max_lines]:
            line_l = line.lower()
            if any(
                keyword in line_l
                for keyword in [
                    "intenção",
                    "contexto",
                    "não",
                    "fora",
                    "escopo",
                    "visão",
                    "produto",
                    "complexidade",
                    "frente",
                    "espera",
                    "ideia",
                    "concept",
                ]
            ):
                summary.append(line.strip())

        return "\n".join(summary)

    def generate_analysis(self, transcript_summary: str) -> str | None:
        """Gera o documento estruturado de análise do Concept."""

        prompt = f"""
Você é um Analista Sênior de Produto e Arquitetura Corporativa,
especializado em transformar transcrições de reuniões executivas
e workshops exploratórios em artefatos estruturados e auditáveis.

O conteúdo a seguir é uma TRANSCRIÇÃO REAL de um encontro sobre
o Concept NAV 360. O material é exploratório e NÃO representa
decisões formais, roadmap fechado ou definição final de produto.

# REGRAS OBRIGATÓRIAS (ANTI-ALUCINAÇÃO)

1. NÃO assumir decisões que não foram explicitamente verbalizadas
2. NÃO transformar intenção em definição final
3. NÃO inventar funcionalidades, escopo, arquitetura ou roadmap
4. NÃO inferir prioridades, prazos ou investimentos
5. Usar linguagem condicional quando apropriado:
   - "foi mencionado"
   - "indicou-se"
   - "foi explicitado que"
6. Preservar o caráter exploratório e provocativo do Concept
7. Toda afirmação relevante deve ser rastreável à transcrição
8. Se algo não estiver claro, declare explicitamente a limitação

# TRANSCRIÇÃO (RESUMIDA)
{transcript_summary}

Gere um documento estruturado em Markdown com EXATAMENTE as seções abaixo,
respeitando a ordem, os títulos e o conteúdo solicitado.

---

## 1. CONTEXTO GERAL DO CONCEPT
- Objetivo declarado do Concept
- Natureza da iniciativa (exploratória, provocativa, pré-decisão)
- Público-alvo mencionado
- Nível de maturidade percebido

## 2. VISÃO DE PRODUTO DISCUTIDA
- Como o produto foi descrito pelos participantes
- Existência (ou não) de visão unificada
- Elementos centrais de experiência mencionados
- Frases-chave representativas (curtas e fiéis à fala)

## 3. ESCOPO EXPLÍCITO DO CONCEPT
Liste APENAS o que foi claramente incluído.
Para cada item:
- Descrição
- Evidência textual resumida

## 4. NÃO-ESCOPO / EXCLUSÕES DECLARADAS
Liste itens explicitamente excluídos.
Para cada item:
- Item excluído
- Motivo (se citado)
- Observações relevantes

## 5. FRENTES PARALELAS MENCIONADAS
- Iniciativas ou frentes citadas como paralelas ou separadas
- Grau de complexidade atribuído (se mencionado)
- Relação percebida com o Concept

## 6. HIPÓTESES, PREMISSAS E INTENÇÕES
Extraia frases que indiquem intenção futura.
Classifique cada uma como:
- Hipótese
- Premissa
- Intenção estratégica

## 7. PONTOS DE ATENÇÃO E TENSÕES
- Ambiguidades
- Complexidades mencionadas
- Alertas implícitos
- Riscos percebidos (sem extrapolar)

## 8. ELEMENTOS POTENCIALMENTE RELEVANTES PARA TO-BE / GAP / ROADMAP
- Capacidades futuras mencionadas
- Mudanças de abordagem sugeridas
- Novos conceitos de experiência
(NÃO cruzar, apenas sinalizar)

## 9. LIMITAÇÕES DA TRANSCRIÇÃO
- Decisões não tomadas
- Pontos não discutidos
- Ambiguidades remanescentes
- Dependências externas

Use linguagem clara, objetiva e rastreável.
Não adicionar seções extras.
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
            print(f"❌ Erro ao gerar análise: {e}")
            return None

    def save_analysis(self, content: str, output_dir: str = "outputs") -> Path:
        """Salva o documento final."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Concept_NAV_360_Transcript_Analysis_{timestamp}.md"
        filepath = output_path / filename

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath

    def generate(self):
        """Executa o processo completo."""
        print("=" * 80)
        print("🧠 CONCEPT NAV 360 - TRANSCRIPT ANALYZER")
        print("=" * 80)

        print("\n📖 Procurando transcrição...")
        transcript_path = self.find_latest_transcript()

        if not transcript_path:
            print("❌ Nenhum arquivo .txt encontrado em /inputs")
            return

        print(f"✅ Transcrição encontrada: {transcript_path.name}")

        print("\n📖 Carregando transcrição...")
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript_content = f.read()

        print("✅ Transcrição carregada")

        print("\n🧠 Criando resumo controlado...")
        transcript_summary = self.summarize_transcript(transcript_content)

        print("🧠 Gerando análise estruturada do Concept...")
        analysis = self.generate_analysis(transcript_summary)

        if not analysis:
            print("❌ Falha na geração da análise")
            return

        print("\n💾 Salvando análise...")
        filepath = self.save_analysis(analysis)

        print("✅ Análise gerada com sucesso!")
        print(f"📄 Arquivo: {filepath}")
        print(f"📊 Tamanho: {len(analysis):,} caracteres")

        print("\n" + "=" * 80)
        print("✅ PROCESSO CONCLUÍDO")
        print("=" * 80)
        print("📌 Artefato pronto para:")
        print("   - Análise junto ao TO-BE")
        print("   - Cruzamento com GAP Analysis")
        print("   - Validação do Roadmap de Adoção")
        print("\n🚀 Próximo passo: cross-agent analysis")


def main():
    if not ANTHROPIC_API_KEY:
        print("❌ ERRO: ANTHROPIC_API_KEY não configurada!")
        return

    try:
        analyzer = ConceptTranscriptAnalyzer()
        analyzer.generate()
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
