import json
import os
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# =============================================================================
# Gerador de Apresentação HTML do Assessment
# =============================================================================

class PresentationGenerator:
    """Gera apresentação HTML interativa do assessment completo."""
    
    def __init__(self, base_dir: str = 'outputs'):
        self.base_dir = Path(base_dir)
        self.data = {}
    
    def collect_data(self):
        """Coleta dados de todos os artefatos gerados."""
        print("📊 Coletando dados do assessment...")
        
        # 1. Blueprints AS-IS
        self.data['blueprints'] = self._collect_blueprints()
        
        # 2. Gap Analysis
        self.data['gap_analysis'] = self._find_latest_file('Gap_Analysis_*.md')
        
        # 3. TO-BE Model
        self.data['to_be'] = self._find_latest_file('TO_BE_Model_*.md')
        
        # 4. Concept NAV 360
        self.data['concept'] = self._find_concept_nav360()
        
        # Estatísticas gerais
        self.data['stats'] = {
            'total_projects': len(self.data['blueprints']),
            'total_apps': sum(len(apps) for apps in self.data['blueprints'].values()),
            'assessment_date': datetime.now().strftime("%d/%m/%Y"),
            'has_gaps': self.data['gap_analysis'] is not None,
            'has_to_be': self.data['to_be'] is not None,
            'has_concept': self.data['concept'] is not None
        }
        
        print(f"   ✅ {self.data['stats']['total_apps']} aplicações encontradas")
        print(f"   ✅ Gap Analysis: {'Sim' if self.data['stats']['has_gaps'] else 'Não'}")
        print(f"   ✅ TO-BE: {'Sim' if self.data['stats']['has_to_be'] else 'Não'}")
    
    def _collect_blueprints(self) -> Dict:
        """Coleta informações dos blueprints."""
        blueprints = {}
        
        for project_dir in self.base_dir.iterdir():
            if not project_dir.is_dir() or project_dir.name in ['json', 'to_be_parts']:
                continue
            
            blueprints_dir = project_dir / 'blueprints'
            if not blueprints_dir.exists():
                continue
            
            project_name = project_dir.name
            blueprints[project_name] = []
            
            for blueprint_file in blueprints_dir.glob('*_blueprint.md'):
                blueprints[project_name].append({
                    'name': blueprint_file.stem.replace('_blueprint', ''),
                    'file': str(blueprint_file.relative_to(self.base_dir))
                })
        
        return blueprints
    
    def _find_latest_file(self, pattern: str) -> str:
        """Encontra o arquivo mais recente que corresponde ao padrão."""
        files = list(self.base_dir.glob(pattern))
        if not files:
            return None
        
        latest = max(files, key=lambda p: p.stat().st_mtime)
        return str(latest.relative_to(self.base_dir))
    
    def _find_concept_nav360(self) -> str:
        """Encontra o Concept NAV 360."""
        possible_names = [
            'Concept_NAV_360.md',
            'concept_nav_360.md',
            'Concept NAV 360.md'
        ]
        
        for name in possible_names:
            file_path = self.base_dir / name
            if file_path.exists():
                return name
        
        return None
    
    def generate_html(self) -> str:
        """Gera o HTML da apresentação."""
        
        stats = self.data['stats']
        blueprints = self.data['blueprints']
        
        # Lista de aplicações com informação do projeto
        apps_list = []
        for project_name, project_apps in blueprints.items():
            for app in project_apps:
                apps_list.append({
                    'project': project_name,
                    'name': app['name'],
                    'file': app['file']
                })
        
        # Construir HTML da lista de apps
        apps_html = ''
        for app_item in apps_list:
            apps_html += f'''
                        <div class="mb-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                            <p class="font-semibold text-gray-900">{app_item['name']}</p>
                            <p class="text-sm text-gray-500">Projeto: {app_item['project']}</p>
                        </div>
            '''
        
        html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Assessment de Arquitetura - Resultados</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @keyframes slideInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .slide-in {{
            animation: slideInUp 0.6s ease-out forwards;
        }}
        
        .section {{
            opacity: 0;
        }}
        
        .section.active {{
            opacity: 1;
            animation: slideInUp 0.6s ease-out;
        }}
        
        /* Smooth scroll */
        html {{
            scroll-behavior: smooth;
        }}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f1f1;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #6366f1;
            border-radius: 5px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #4f46e5;
        }}
    </style>
</head>
<body class="bg-gradient-to-br from-gray-50 to-gray-100 min-h-screen">
    
    <!-- Navigation -->
    <nav class="bg-white shadow-lg fixed w-full top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex items-center">
                    <h1 class="text-2xl font-bold text-indigo-600">📊 Assessment de Arquitetura</h1>
                </div>
                <div class="flex items-center space-x-4">
                    <a href="#overview" class="text-gray-600 hover:text-indigo-600 transition">Visão Geral</a>
                    <a href="#process" class="text-gray-600 hover:text-indigo-600 transition">Processo</a>
                    <a href="#results" class="text-gray-600 hover:text-indigo-600 transition">Resultados</a>
                    <a href="#next-steps" class="text-gray-600 hover:text-indigo-600 transition">Próximos Passos</a>
                </div>
            </div>
        </div>
    </nav>

    <!-- Hero Section -->
    <section id="overview" class="pt-24 pb-12 px-4">
        <div class="max-w-7xl mx-auto">
            <div class="text-center mb-12 slide-in">
                <h2 class="text-5xl font-bold text-gray-900 mb-4">
                    Resultados do Assessment
                </h2>
                <p class="text-xl text-gray-600 mb-8">
                    Análise completa do portfólio de aplicações
                </p>
                <div class="flex justify-center items-center space-x-2 text-sm text-gray-500">
                    <span>📅 Data:</span>
                    <span class="font-semibold">{stats['assessment_date']}</span>
                </div>
            </div>

            <!-- Stats Cards -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
                <!-- Total Apps -->
                <div class="bg-white rounded-xl shadow-lg p-6 slide-in" style="animation-delay: 0.1s">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-500 text-sm font-medium">Total de Aplicações</p>
                            <p class="text-3xl font-bold text-indigo-600 mt-2">{stats['total_apps']}</p>
                        </div>
                        <div class="bg-indigo-100 rounded-full p-3">
                            <svg class="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/>
                            </svg>
                        </div>
                    </div>
                </div>

                <!-- Projects -->
                <div class="bg-white rounded-xl shadow-lg p-6 slide-in" style="animation-delay: 0.2s">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-500 text-sm font-medium">Projetos</p>
                            <p class="text-3xl font-bold text-green-600 mt-2">{stats['total_projects']}</p>
                        </div>
                        <div class="bg-green-100 rounded-full p-3">
                            <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"/>
                            </svg>
                        </div>
                    </div>
                </div>

                <!-- Gap Analysis -->
                <div class="bg-white rounded-xl shadow-lg p-6 slide-in" style="animation-delay: 0.3s">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-500 text-sm font-medium">Gap Analysis</p>
                            <p class="text-3xl font-bold {'text-green-600' if stats['has_gaps'] else 'text-gray-400'} mt-2">
                                {'✓' if stats['has_gaps'] else '○'}
                            </p>
                        </div>
                        <div class="bg-{'green' if stats['has_gaps'] else 'gray'}-100 rounded-full p-3">
                            <svg class="w-8 h-8 text-{'green' if stats['has_gaps'] else 'gray'}-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                            </svg>
                        </div>
                    </div>
                </div>

                <!-- TO-BE Model -->
                <div class="bg-white rounded-xl shadow-lg p-6 slide-in" style="animation-delay: 0.4s">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-500 text-sm font-medium">Modelo TO-BE</p>
                            <p class="text-3xl font-bold {'text-green-600' if stats['has_to_be'] else 'text-gray-400'} mt-2">
                                {'✓' if stats['has_to_be'] else '○'}
                            </p>
                        </div>
                        <div class="bg-{'green' if stats['has_to_be'] else 'gray'}-100 rounded-full p-3">
                            <svg class="w-8 h-8 text-{'green' if stats['has_to_be'] else 'gray'}-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                            </svg>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Process Section -->
    <section id="process" class="py-12 px-4 bg-white">
        <div class="max-w-7xl mx-auto">
            <h2 class="text-4xl font-bold text-gray-900 mb-8 text-center">Processo de Assessment</h2>
            
            <div class="relative">
                <!-- Timeline Line -->
                <div class="absolute left-1/2 transform -translate-x-1/2 h-full w-1 bg-indigo-200"></div>
                
                <!-- Step 1: Coleta de Dados -->
                <div class="relative mb-12 section">
                    <div class="flex items-center justify-between">
                        <div class="w-5/12 text-right pr-8">
                            <div class="bg-gradient-to-r from-indigo-500 to-indigo-600 text-white rounded-xl p-6 shadow-lg">
                                <h3 class="text-2xl font-bold mb-2">1. Coleta de Dados</h3>
                                <p class="text-indigo-100">Scripts Azure DevOps API</p>
                                <ul class="mt-4 space-y-2 text-sm text-indigo-100">
                                    <li>✓ Scan de repositórios</li>
                                    <li>✓ Análise de package.json</li>
                                    <li>✓ Mapeamento de dependências</li>
                                    <li>✓ Identificação de tecnologias</li>
                                </ul>
                            </div>
                        </div>
                        <div class="w-2/12 flex justify-center">
                            <div class="bg-indigo-600 rounded-full w-12 h-12 flex items-center justify-center text-white font-bold text-xl shadow-lg z-10">
                                1
                            </div>
                        </div>
                        <div class="w-5/12"></div>
                    </div>
                </div>

                <!-- Step 2: Blueprints AS-IS -->
                <div class="relative mb-12 section">
                    <div class="flex items-center justify-between">
                        <div class="w-5/12"></div>
                        <div class="w-2/12 flex justify-center">
                            <div class="bg-blue-600 rounded-full w-12 h-12 flex items-center justify-center text-white font-bold text-xl shadow-lg z-10">
                                2
                            </div>
                        </div>
                        <div class="w-5/12 pl-8">
                            <div class="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl p-6 shadow-lg">
                                <h3 class="text-2xl font-bold mb-2">2. Blueprints AS-IS</h3>
                                <p class="text-blue-100">Estado atual documentado</p>
                                <div class="mt-4">
                                    <p class="text-sm text-blue-100 mb-2">✓ {stats['total_apps']} aplicações documentadas</p>
                                    <p class="text-sm text-blue-100">✓ {stats['total_projects']} projetos mapeados</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Step 3: Análise de Gaps -->
                <div class="relative mb-12 section">
                    <div class="flex items-center justify-between">
                        <div class="w-5/12 text-right pr-8">
                            <div class="bg-gradient-to-r from-purple-500 to-purple-600 text-white rounded-xl p-6 shadow-lg">
                                <h3 class="text-2xl font-bold mb-2">3. Análise de Gaps</h3>
                                <p class="text-purple-100">AS-IS vs Boas Práticas</p>
                                <ul class="mt-4 space-y-2 text-sm text-purple-100">
                                    <li>✓ Identificação de anti-patterns</li>
                                    <li>✓ Análise de débito técnico</li>
                                    <li>✓ Priorização de problemas</li>
                                    <li>✓ Matriz de impacto vs esforço</li>
                                </ul>
                            </div>
                        </div>
                        <div class="w-2/12 flex justify-center">
                            <div class="bg-purple-600 rounded-full w-12 h-12 flex items-center justify-center text-white font-bold text-xl shadow-lg z-10">
                                3
                            </div>
                        </div>
                        <div class="w-5/12"></div>
                    </div>
                </div>

                <!-- Step 4: Modelo TO-BE -->
                <div class="relative mb-12 section">
                    <div class="flex items-center justify-between">
                        <div class="w-5/12"></div>
                        <div class="w-2/12 flex justify-center">
                            <div class="bg-green-600 rounded-full w-12 h-12 flex items-center justify-center text-white font-bold text-xl shadow-lg z-10">
                                4
                            </div>
                        </div>
                        <div class="w-5/12 pl-8">
                            <div class="bg-gradient-to-r from-green-500 to-green-600 text-white rounded-xl p-6 shadow-lg">
                                <h3 class="text-2xl font-bold mb-2">4. Modelo TO-BE</h3>
                                <p class="text-green-100">Arquitetura futura baseada em gaps + estratégia</p>
                                <ul class="mt-4 space-y-2 text-sm text-green-100">
                                    <li>✓ Resolve gaps prioritários</li>
                                    <li>✓ Viabiliza Concept NAV 360</li>
                                    <li>✓ Decisões técnicas documentadas</li>
                                    <li>✓ Roadmap de evolução</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Step 5: Roadmap -->
                <div class="relative section">
                    <div class="flex items-center justify-between">
                        <div class="w-5/12 text-right pr-8">
                            <div class="bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-xl p-6 shadow-lg">
                                <h3 class="text-2xl font-bold mb-2">5. Roadmap de Adoção</h3>
                                <p class="text-orange-100">Planejamento em ondas</p>
                                <ul class="mt-4 space-y-2 text-sm text-orange-100">
                                    <li>✓ Priorização por impacto/esforço</li>
                                    <li>✓ Ondas de migração</li>
                                    <li>✓ Timeline realista</li>
                                    <li>✓ Métricas de sucesso</li>
                                </ul>
                            </div>
                        </div>
                        <div class="w-2/12 flex justify-center">
                            <div class="bg-orange-600 rounded-full w-12 h-12 flex items-center justify-center text-white font-bold text-xl shadow-lg z-10">
                                5
                            </div>
                        </div>
                        <div class="w-5/12"></div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- Results Section -->
    <section id="results" class="py-12 px-4 bg-gray-50">
        <div class="max-w-7xl mx-auto">
            <h2 class="text-4xl font-bold text-gray-900 mb-8 text-center">Resultados e Artefatos</h2>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                
                <!-- Blueprints AS-IS -->
                <div class="bg-white rounded-xl shadow-lg p-6">
                    <div class="flex items-center mb-4">
                        <div class="bg-blue-100 rounded-lg p-3 mr-4">
                            <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                            </svg>
                        </div>
                        <div>
                            <h3 class="text-xl font-bold text-gray-900">Blueprints AS-IS</h3>
                            <p class="text-sm text-gray-500">{stats['total_apps']} aplicações documentadas</p>
                        </div>
                    </div>
                    <div class="mt-4 max-h-64 overflow-y-auto">
                        {apps_html}
                    </div>
                </div>

                <!-- Gap Analysis -->
                <div class="bg-white rounded-xl shadow-lg p-6">
                    <div class="flex items-center mb-4">
                        <div class="bg-purple-100 rounded-lg p-3 mr-4">
                            <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                            </svg>
                        </div>
                        <div>
                            <h3 class="text-xl font-bold text-gray-900">Análise de Gaps</h3>
                            <p class="text-sm text-gray-500">AS-IS vs Boas Práticas</p>
                        </div>
                    </div>
                    """ + (f'<div class="mt-4 space-y-3">' if stats['has_gaps'] else '<div class="mt-4">') + """
                        """ + (f'<a href="{self.data["gap_analysis"]}" target="_blank" class="block p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition border-2 border-purple-200"><div class="flex items-center justify-between"><span class="font-semibold text-purple-900">📄 Ver Análise Completa</span><svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg></div></a>' if stats['has_gaps'] else '<p class="text-gray-500 italic">Análise de gaps não disponível</p>') + """
                        """ + ('<div class="grid grid-cols-2 gap-3"><div class="p-3 bg-red-50 rounded-lg border border-red-200"><p class="text-sm text-gray-600">Gaps Críticos</p><p class="text-2xl font-bold text-red-600">-</p></div><div class="p-3 bg-orange-50 rounded-lg border border-orange-200"><p class="text-sm text-gray-600">Gaps Altos</p><p class="text-2xl font-bold text-orange-600">-</p></div></div>' if stats['has_gaps'] else '') + """
                    </div>
                </div>

                <!-- TO-BE Model -->
                <div class="bg-white rounded-xl shadow-lg p-6">
                    <div class="flex items-center mb-4">
                        <div class="bg-green-100 rounded-lg p-3 mr-4">
                            <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                            </svg>
                        </div>
                        <div>
                            <h3 class="text-xl font-bold text-gray-900">Modelo TO-BE</h3>
                            <p class="text-sm text-gray-500">Arquitetura Futura</p>
                        </div>
                    </div>
                    <div class="mt-4">
                        """ + (f'<a href="{self.data["to_be"]}" target="_blank" class="block p-4 bg-green-50 rounded-lg hover:bg-green-100 transition border-2 border-green-200"><div class="flex items-center justify-between"><span class="font-semibold text-green-900">📄 Ver Modelo Completo</span><svg class="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg></div></a>' if stats['has_to_be'] else '<p class="text-gray-500 italic">Modelo TO-BE não disponível</p>') + """
                        """ + ('<div class="mt-3 p-3 bg-gray-50 rounded-lg"><p class="text-sm text-gray-600 mb-2">Decisões Arquiteturais</p><ul class="space-y-1 text-sm text-gray-700"><li>• Stack Tecnológico</li><li>• Padrões Arquiteturais</li><li>• APIs e Integração</li><li>• Observabilidade</li></ul></div>' if stats['has_to_be'] else '') + """
                    </div>
                </div>

                <!-- Concept NAV 360 -->
                <div class="bg-white rounded-xl shadow-lg p-6">
                    <div class="flex items-center mb-4">
                        <div class="bg-indigo-100 rounded-lg p-3 mr-4">
                            <svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                            </svg>
                        </div>
                        <div>
                            <h3 class="text-xl font-bold text-gray-900">Concept NAV 360</h3>
                            <p class="text-sm text-gray-500">Visão Estratégica</p>
                        </div>
                    </div>
                    <div class="mt-4">
                        """ + (f'<a href="{self.data["concept"]}" target="_blank" class="block p-4 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition border-2 border-indigo-200"><div class="flex items-center justify-between"><span class="font-semibold text-indigo-900">📄 Ver Concept</span><svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg></div></a>' if stats['has_concept'] else '<p class="text-gray-500 italic">Concept NAV 360 não disponível</p>') + """
                        """ + ('<div class="mt-3 p-3 bg-gray-50 rounded-lg"><p class="text-sm text-gray-600 mb-2">Funcionalidades Estratégicas</p><ul class="space-y-1 text-sm text-gray-700"><li>• Hero Personalizado</li><li>• Gestão Familiar</li><li>• Busca Inteligente</li><li>• Calendário Vacinal</li></ul></div>' if stats['has_concept'] else '') + """
                    </div>
                </div>

            </div>
        </div>
    </section>

    <!-- Next Steps -->
    <section id="next-steps" class="py-12 px-4 bg-white">
        <div class="max-w-7xl mx-auto">
            <h2 class="text-4xl font-bold text-gray-900 mb-8 text-center">Próximos Passos</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Step 1 -->
                <div class="bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl shadow-xl p-6 text-white">
                    <div class="text-5xl mb-4">📋</div>
                    <h3 class="text-2xl font-bold mb-3">1. Validação</h3>
                    <p class="text-indigo-100 mb-4">
                        Revisar os artefatos gerados com stakeholders técnicos e de negócio
                    </p>
                    <ul class="space-y-2 text-sm text-indigo-100">
                        <li>✓ Gap Analysis</li>
                        <li>✓ Modelo TO-BE</li>
                        <li>✓ Prioridades</li>
                    </ul>
                </div>

                <!-- Step 2 -->
                <div class="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-xl p-6 text-white">
                    <div class="text-5xl mb-4">🗺️</div>
                    <h3 class="text-2xl font-bold mb-3">2. Roadmap</h3>
                    <p class="text-purple-100 mb-4">
                        Criar roadmap detalhado de implementação em ondas
                    </p>
                    <ul class="space-y-2 text-sm text-purple-100">
                        <li>✓ Definir ondas</li>
                        <li>✓ Apps por onda</li>
                        <li>✓ Timeline</li>
                    </ul>
                </div>

                <!-- Step 3 -->
                <div class="bg-gradient-to-br from-green-500 to-green-600 rounded-xl shadow-xl p-6 text-white">
                    <div class="text-5xl mb-4">🚀</div>
                    <h3 class="text-2xl font-bold mb-3">3. Execução</h3>
                    <p class="text-green-100 mb-4">
                        Iniciar implementação começando por Quick Wins
                    </p>
                    <ul class="space-y-2 text-sm text-green-100">
                        <li>✓ Onda 1: Fundação</li>
                        <li>✓ Métricas</li>
                        <li>✓ Evolução contínua</li>
                    </ul>
                </div>
            </div>

            <!-- Call to Action -->
            <div class="mt-12 text-center">
                <div class="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl shadow-2xl p-8 text-white">
                    <h3 class="text-3xl font-bold mb-4">Pronto para Começar?</h3>
                    <p class="text-xl text-indigo-100 mb-6">
                        Entre em contato para discutir os próximos passos do assessment
                    </p>
                    <button class="bg-white text-indigo-600 font-bold py-3 px-8 rounded-lg hover:bg-gray-100 transition transform hover:scale-105">
                        Agendar Reunião
                    </button>
                </div>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="bg-gray-900 text-white py-8 px-4">
        <div class="max-w-7xl mx-auto text-center">
            <p class="text-gray-400">
                Assessment de Arquitetura • {stats['assessment_date']}
            </p>
            <p class="text-gray-500 text-sm mt-2">
                Gerado automaticamente via Azure DevOps API + Claude AI
            </p>
        </div>
    </footer>

    <script>
        // Intersection Observer para animações
        const observerOptions = {{
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        }};

        const observer = new IntersectionObserver((entries) => {{
            entries.forEach(entry => {{
                if (entry.isIntersecting) {{
                    entry.target.classList.add('active');
                }}
            }});
        }}, observerOptions);

        document.querySelectorAll('.section').forEach(section => {{
            observer.observe(section);
        }});

        // Smooth scroll para links de navegação
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{
                        behavior: 'smooth',
                        block: 'start'
                    }});
                }}
            }});
        }});
    </script>

</body>
</html>'''

        # No final de generate_html(), antes de return html:
        import re
        if '""" + (f' in html or "''' + (f" in html:
            raise ValueError("❌ Template contém concatenação inválida! Revise generate_html().")
        if 'cdn.tailwindcss.com  ' in html:
            raise ValueError("❌ CDN URL com espaços detectada!")
        print("✅ HTML validado - pronto para salvar")
        
        return html

    
    def save_presentation(self, html: str) -> Path:
        """Salva a apresentação HTML."""
        output_path = self.base_dir
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Assessment_Presentation_{timestamp}.html"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return filepath
    
    def generate(self):
        """Gera a apresentação completa."""
        print("="*80)
        print("🎨 GERADOR DE APRESENTAÇÃO - Assessment de Arquitetura")
        print("="*80)
        
        # 1. Coleta dados
        self.collect_data()
        
        # 2. Gera HTML
        print("\n🎨 Gerando apresentação HTML...")
        html = self.generate_html()
        
        # 3. Salva
        print("\n💾 Salvando apresentação...")
        filepath = self.save_presentation(html)
        
        print(f"\n✅ Apresentação gerada com sucesso!")
        print(f"📄 Arquivo: {filepath}")
        print(f"📊 Tamanho: {len(html):,} caracteres")
        
        print("\n" + "="*80)
        print("✅ APRESENTAÇÃO CONCLUÍDA!")
        print("="*80)
        
        print(f"\n📖 Como visualizar:")
        print(f"   1. Abra o arquivo: {filepath}")
        print(f"   2. Ou use: python -m http.server 8000")
        print(f"   3. Acesse: http://localhost:8000/{filepath.name}")
        
        print(f"\n💡 RECURSOS:")
        print(f"   ✅ Design responsivo")
        print(f"   ✅ Animações suaves")
        print(f"   ✅ Timeline interativa")
        print(f"   ✅ Cards de resultados")
        print(f"   ✅ Links para artefatos")
        
        return filepath


def main():
    """Função principal."""
    try:
        generator = PresentationGenerator()
        generator.generate()
    
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()