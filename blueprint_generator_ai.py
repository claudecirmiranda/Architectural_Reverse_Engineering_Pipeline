import json
import os
from pathlib import Path
from typing import Dict, Any
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


class BlueprintGenerator:
    """Gera blueprints detalhados de aplicações usando Claude AI."""
    
    def __init__(self, api_key: str = None):
        """Inicializa o gerador com a chave da API Anthropic."""
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY não encontrada. Configure via parâmetro ou variável de ambiente.")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = MODEL
    
    def load_repository_data(self, filepath: Path) -> str:
        """Carrega os dados agregados de um repositório."""
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    def load_example_blueprint(self) -> str:
        """Carrega o blueprint de exemplo como referência."""
        example_path = Path('blueprint_example.md')
        if example_path.exists():
            with open(example_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def generate_blueprint(self, repo_data: str, repo_name: str, example_blueprint: str) -> str:
        """Gera o blueprint usando Claude AI."""
        
        prompt = f"""Você é um arquiteto de software especializado em engenharia reversa e documentação técnica.

Sua tarefa é analisar os dados de engenharia reversa de um repositório e gerar um **Blueprint detalhado** seguindo o padrão do exemplo fornecido.

# EXEMPLO DE BLUEPRINT (USE COMO REFERÊNCIA DE ESTRUTURA E ESTILO):

{example_blueprint}

---

# DADOS DO REPOSITÓRIO PARA ANÁLISE:

{repo_data}

---

# INSTRUÇÕES PARA GERAR O BLUEPRINT:

1. **Título e Introdução**: Comece com o nome da aplicação em destaque e uma breve descrição do propósito do sistema.

2. **Visão Geral da Arquitetura**: Descreva o papel da aplicação no ecossistema, seu tipo (BFF, API, Microserviço, etc.) e como ela se posiciona.

3. **Diagramas Mermaid**: Crie diagramas relevantes baseados nos dados:
   - **Diagrama de Contexto (Nível 1)**: Mostra interações com usuários e sistemas externos
   - **Diagrama de Container (Nível 2)**: Detalha a estrutura interna, tecnologias e componentes
   - **Diagramas adicionais** se relevante (fluxos, sequência, etc.)

4. **Tecnologias e Stacks**: Liste as principais tecnologias identificadas nos dados:
   - Linguagem e runtime
   - Frameworks principais
   - Bancos de dados e cache
   - Bibliotecas importantes
   - Ferramentas de build e teste

5. **Padrões de Arquitetura**: Identifique e explique os padrões arquiteturais:
   - Padrões estruturais (MVC, Hexagonal, Clean Architecture, etc.)
   - Padrões de integração
   - Justifique por que esses padrões fazem sentido para este contexto

6. **Estrutura de Código**: Descreva a organização:
   - Camadas identificadas (Controllers, Services, Repositories, Resolvers, etc.)
   - Quantidade de cada tipo de componente
   - Padrão de organização de pastas

7. **Integrações**: Liste e categorize as integrações:
   - APIs externas
   - Bancos de dados
   - Serviços de autenticação
   - Serviços de terceiros
   - Variáveis de ambiente relevantes

8. **Considerações de Infraestrutura**:
   - Containerização (Docker, K8s)
   - CI/CD
   - Estratégias de deployment
   - Escalabilidade e resiliência

9. **Cross-Cutting Concerns**:
   - Segurança
   - Logging e monitoramento
   - Tratamento de erros
   - Validação
   - Health checks

10. **Justificativas Técnicas**: Explique as escolhas arquiteturais com base nos dados analisados.

# IMPORTANTE:
- Use Markdown para formatação
- Todos os diagramas devem estar em blocos ```mermaid
- Seja técnico mas didático
- Baseie-se APENAS nos dados fornecidos
- Se algo não estiver claro nos dados, mencione como "não identificado nos dados disponíveis"
- Mantenha consistência com o estilo do exemplo
- Use a nomenclatura em português quando apropriado

Gere agora o blueprint completo para a aplicação **{repo_name}**:"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=16000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text
        
        except Exception as e:
            print(f"Erro ao gerar blueprint: {e}")
            return f"# Erro ao gerar blueprint\n\nErro: {str(e)}"
    
    def process_repository(self, repo_file: Path, output_dir: Path, example_blueprint: str):
        """Processa um arquivo de repositório e gera seu blueprint."""
        print(f"\n{'='*80}")
        print(f"Processando: {repo_file.name}")
        print(f"{'='*80}")
        
        # Carrega os dados do repositório
        repo_data = self.load_repository_data(repo_file)
        repo_name = repo_file.stem  # Nome sem extensão
        
        # Gera o blueprint
        print(f"Gerando blueprint com IA...")
        blueprint = self.generate_blueprint(repo_data, repo_name, example_blueprint)
        
        # Salva o blueprint
        output_file = output_dir / f"{repo_name}_blueprint.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(blueprint)
        
        print(f"✓ Blueprint gerado: {output_file}")
        print(f"  Tamanho: {len(blueprint):,} caracteres")
    
    def process_all_repositories(self, input_base_dir: str = 'outputs'):
        """Processa todos os repositórios encontrados."""
        input_path = Path(input_base_dir)
        
        if not input_path.exists():
            print(f"Erro: Diretório {input_base_dir} não encontrado!")
            return
        
        # Carrega o blueprint de exemplo
        print("Carregando blueprint de exemplo...")
        example_blueprint = self.load_example_blueprint()
        if not example_blueprint:
            print("Aviso: Blueprint de exemplo não encontrado em 'blueprint_example.md'")
            print("O agente ainda funcionará, mas sem referência de formato.")
        
        # Conta total de arquivos
        total_files = 0
        for project_dir in input_path.iterdir():
            if project_dir.is_dir() and project_dir.name != 'json':
                total_files += len(list(project_dir.glob('*.txt')))
        
        print(f"\n{'='*80}")
        print(f"Total de repositórios encontrados: {total_files}")
        print(f"{'='*80}")
        
        if total_files == 0:
            print("Nenhum arquivo .txt encontrado para processar!")
            return
        
        processed = 0
        
        # Processa cada projeto
        for project_dir in input_path.iterdir():
            if not project_dir.is_dir() or project_dir.name == 'json':
                continue
            
            project_name = project_dir.name
            print(f"\n{'#'*80}")
            print(f"# PROJETO: {project_name}")
            print(f"{'#'*80}")
            
            # Cria diretório de saída para blueprints
            blueprints_dir = project_dir / 'blueprints'
            blueprints_dir.mkdir(exist_ok=True)
            
            # Processa cada repositório do projeto
            repo_files = list(project_dir.glob('*.txt'))
            
            for repo_file in repo_files:
                try:
                    self.process_repository(repo_file, blueprints_dir, example_blueprint)
                    processed += 1
                    print(f"\nProgresso: {processed}/{total_files} repositórios processados")
                
                except Exception as e:
                    print(f"✗ Erro ao processar {repo_file.name}: {e}")
                    continue
        
        print(f"\n{'='*80}")
        print(f"✓ Processamento concluído!")
        print(f"Total processado: {processed}/{total_files} repositórios")
        print(f"{'='*80}")


def main():
    """Função principal."""
    print("="*80)
    print("GERADOR DE BLUEPRINTS COM IA")
    print("="*80)
    
    # Verifica se a API key está configurada
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("\n⚠ ERRO: ANTHROPIC_API_KEY não configurada!")
        print("\nConfigure a variável de ambiente:")
        print("  export ANTHROPIC_API_KEY='sua-chave-aqui'  # Linux/Mac")
        print("  set ANTHROPIC_API_KEY=sua-chave-aqui      # Windows")
        return
    
    print(f"\n✓ API Key configurada")
    print(f"✓ Modelo: claude-sonnet-4-20250514")
    
    # Cria o gerador e processa
    try:
        generator = BlueprintGenerator(api_key)
        generator.process_all_repositories()
    
    except Exception as e:
        print(f"\n✗ Erro fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()