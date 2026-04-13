import json
import os
from pathlib import Path
from typing import Dict
from datetime import datetime
import anthropic
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL = "claude-sonnet-4-20250514"

if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY não configurada.")

class RoadmapGenerator:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def find_latest_files(self, base_dir: str = 'outputs') -> Dict[str, Path]:
        base_path = Path(base_dir)
        to_be_files = list(base_path.glob('TO_BE_Model_*.md'))
        gap_files = list(base_path.glob('Gap_Analysis_*.md'))

        result = {}
        if to_be_files:
            result['to_be'] = max(to_be_files, key=lambda p: p.stat().st_mtime)
        if gap_files:
            result['gap_analysis'] = max(gap_files, key=lambda p: p.stat().st_mtime)
        return result

    def summarize_content(self, content: str, max_lines: int = 800) -> str:
        """Cria resumo rápido para caber melhor no contexto."""
        lines = content.splitlines()
        summary = []
        for line in lines[:max_lines]:
            if line.strip() and (line.startswith('#') or ':' in line or 'gap' in line.lower() or 'aplicação' in line.lower()):
                summary.append(line)
        return '\n'.join(summary)

    def generate_part(self, part_number: int, total_parts: int,
                      to_be_summary: str, gap_summary: str,
                      previous_parts_summary: str = "") -> str | None:
        """Gera UMA parte específica do roadmap."""

        base_prompt = f"""Você é um Consultor de Transformação Digital sênior e Gerente de Programa.

# REGRAS ANTI-ALUCINAÇÃO (obrigatórias em TODAS as partes)
1. Toda iniciativa DEVE citar explicitamente o gap que endereça
2. Use APENAS aplicações, gaps e informações presentes nos resumos fornecidos
3. É PROIBIDO inventar valores monetários, custos, budgets ou ROI
4. Só mencione valores financeiros se estiverem EXPLICITAMENTE descritos nos resumos
5. Na ausência de base financeira comprovável, use OBRIGATORIAMENTE:
   - "⚠️ Financeiro: TBD"
   - ou "⚠️ Financeiro: Fora de escopo deste estudo"
6. Nunca faça estimativas financeiras implícitas (ex: baixo/médio/alto custo)
7. Nunca invente nomes de aplicações, gaps, tecnologias, prazos ou números
8. Sempre que mencionar uma aplicação, certifique-se de que ela está presente no resumo TO-BE
9. Sempre que mencionar um gap, certifique-se de que ele está presente no resumo de análise de gaps 

# AUTOCHECAGEM OBRIGATÓRIA ANTES DE RESPONDER
Antes de escrever, valide mentalmente:
- Existe base factual explícita nos resumos para cada afirmação feita?
- Existe base documental para qualquer menção a custo, investimento ou impacto financeiro?
Se a resposta for NÃO, marque como "TBD" ou "Fora de escopo".

# Resumo TO-BE:
{to_be_summary}

# Resumo Análise de Gaps:
{gap_summary}

# Contexto das partes anteriores (resumido):
{previous_parts_summary if previous_parts_summary else "Nenhuma parte anterior gerada ainda."}

Você está gerando a **PARTE {part_number} de {total_parts}** do Roadmap de Adoção.

Gere APENAS o conteúdo solicitado abaixo. Não repita seções anteriores. Termine com:

--- FIM DA PARTE {part_number} ---
"""

        part_instructions = [
            # Parte 1
            """Gere APENAS:
## 1. SUMÁRIO EXECUTIVO DO ROADMAP
## 2. ABORDAGEM ESTRATÉGICA
## 3. ESTRUTURA DO ROADMAP (incluindo diagrama Mermaid gantt)""",

            # Parte 2
            """Gere APENAS:
## 4. ROADMAP DETALHADO POR ONDA
Até o final da Onda 2 (incluindo iniciativas, recursos, riscos e resumo de cada onda)""",

            # Parte 3
            """Gere APENAS:
Continuação da seção 4:
- Onda 3 (e eventuais ondas seguintes)
## 5. PLANO DE RECURSOS CONSOLIDADO
- Recursos humanos (perfis e papéis, sem quantificação financeira)
- Orçamento: APENAS indicação qualitativa ou "TBD", sem valores
- Ferramentas e plataformas (sem custos estimados)

⚠️ IMPORTANTE:
- Não incluir valores monetários
- Não estimar custos
- Não classificar custos como baixo/médio/alto
""",

            # Parte 4
            """Gere APENAS:
## 6. GESTÃO DE MUDANÇA E ADOÇÃO
## 7. GOVERNANÇA DO PROGRAMA
## 8. MÉTRICAS DE SUCESSO E KPIS""",

            # Parte 5
            """Gere APENAS:
## 9. GESTÃO DE RISCOS E CONTINGÊNCIAS
## 10. MARCOS E CELEBRAÇÕES
## 11. CONCLUSÃO E PRÓXIMOS PASSOS
Faça uma revisão final breve confirmando aderência às regras anti-alucinação."""
        ]

        if part_number < 1 or part_number > len(part_instructions):
            raise ValueError(f"Parte {part_number} inválida")

        prompt = base_prompt + "\n\n" + part_instructions[part_number - 1]

        try:
            message = self.client.messages.create(
                model=MODEL,
                max_tokens=12000,          # menor que 16k para margem de segurança
                temperature=0.25,
                messages=[{"role": "user", "content": prompt}]
            )
            text = message.content[0].text.strip()
            # Remove marcador de fim para limpeza
            if "--- FIM DA PARTE" in text:
                text = text.split("--- FIM DA PARTE")[0].strip()
            return text
        except Exception as e:
            print(f"❌ Erro na parte {part_number}: {str(e)}")
            return None

    def generate_roadmap(self, to_be_content: str, gap_analysis_content: str) -> str | None:
        to_be_summary = self.summarize_content(to_be_content, 600)
        gap_summary = self.summarize_content(gap_analysis_content, 1000)

        total_parts = 5
        parts = []
        accumulated_summary = ""

        print(f"Gerando roadmap em {total_parts} partes...")

        for part_n in range(1, total_parts + 1):
            print(f"  → Parte {part_n}/{total_parts} ... ", end="", flush=True)
            part_content = self.generate_part(
                part_number=part_n,
                total_parts=total_parts,
                to_be_summary=to_be_summary,
                gap_summary=gap_summary,
                previous_parts_summary=accumulated_summary
            )

            if not part_content:
                print("falhou")
                return None

            parts.append(part_content)
            # Atualiza resumo acumulado (limita tamanho)
            accumulated_summary += f"\n\n### Resumo Parte {part_n}\n" + "\n".join(
                line for line in part_content.splitlines() if line.strip() and (line.startswith('#') or 'Onda' in line or 'Gap' in line)
            )[:1500]

            print(f"ok ({len(part_content):,} chars)")
            time.sleep(1.2)  # evita rate limit

        print("Concatenando partes...")
        body = "\n\n".join(parts)

        header = f"""# 🗺️ ROADMAP DE ADOÇÃO - TRANSFORMAÇÃO ARQUITETURAL
**Organização**: NAV Dasa
**Data de Geração**: {datetime.now().strftime("%d/%m/%Y %H:%M")}
**Versão**: 1.0

---
"""

        return header + body

    def save_roadmap(self, content: str, output_dir: str = 'outputs'):
        """Salva o roadmap."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Adoption_Roadmap_{timestamp}.md"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    
    def generate(self):
        """Executa o processo completo de geração do roadmap."""
        print("="*80)
        print("🗺️  GERADOR DE ROADMAP DE ADOÇÃO (Versão Anti-Alucinação)")
        print("="*80)
        
        # 1. Encontra arquivos necessários
        print("\n📖 Procurando arquivos necessários...")
        files = self.find_latest_files()
        
        if 'to_be' not in files:
            print("❌ Modelo TO BE não encontrado!")
            print("   Execute to_be_generator.py primeiro.")
            return
        
        if 'gap_analysis' not in files:
            print("❌ Análise de Gaps não encontrada!")
            print("   Execute gap_analyzer.py primeiro.")
            return
        
        print(f"✅ TO BE: {files['to_be'].name}")
        print(f"✅ Gap Analysis: {files['gap_analysis'].name}")
        
        # 2. Carrega conteúdos
        print("\n📖 Carregando documentos...")
        
        with open(files['to_be'], 'r', encoding='utf-8') as f:
            to_be_content = f.read()
        
        with open(files['gap_analysis'], 'r', encoding='utf-8') as f:
            gap_analysis_content = f.read()
        
        print("✅ Documentos carregados")
        
        # 3. Gera roadmap
        print(f"\n🗺️  Gerando roadmap de adoção...")
        print("   ⚠️  Modo rigoroso: Iniciativas baseadas em gaps reais")
        roadmap = self.generate_roadmap(to_be_content, gap_analysis_content)
        
        if not roadmap:
            print("❌ Falha ao gerar roadmap")
            return
        
        # 4. Salva roadmap
        print("\n💾 Salvando roadmap...")
        filepath = self.save_roadmap(roadmap)
        
        print(f"✅ Roadmap gerado com sucesso!")
        print(f"📄 Arquivo: {filepath}")
        print(f"📊 Tamanho: {len(roadmap):,} caracteres")
        
        print("\n" + "="*80)
        print("✅ GERAÇÃO CONCLUÍDA!")
        print("="*80)
        print(f"\n📖 Revise o arquivo: {filepath.name}")
        print("   ⚠️  IMPORTANTE: Verifique se iniciativas têm gaps correspondentes")
        print("   ⚠️  IMPORTANTE: Confirme que aplicações são reais dos blueprints")
        print("🎯 Você agora tem a documentação completa:")
        print("   1. Blueprints AS-IS (por aplicação)")
        print("   2. Modelo TO-BE (estado futuro)")
        print("   3. Análise de Gaps (o que precisa mudar)")
        print("   4. Roadmap de Adoção (como chegar lá)")
        print("\n🚀 Pronto para validação e apresentação!")


def main():
    """Função principal."""
    if not ANTHROPIC_API_KEY:
        print("❌ ERRO: ANTHROPIC_API_KEY não configurada!")
        return
    
    try:
        generator = RoadmapGenerator()
        generator.generate()
    
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()