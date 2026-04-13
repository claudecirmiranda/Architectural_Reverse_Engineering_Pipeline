from pathlib import Path
import json
import shutil
import yaml
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs"))

OUTPUT = BASE_DIR / OUTPUT_DIR
DOCS = BASE_DIR / "docs"


class MkDocsBuilder:

    def __init__(self):
        self.docs = DOCS
        self.nav = []

    # -------------------------
    # INIT
    # -------------------------

    def prepare(self):

        if self.docs.exists():
            shutil.rmtree(self.docs)

        self.docs.mkdir(parents=True, exist_ok=True)

        assets = self.docs / "assets"
        assets.mkdir(exist_ok=True)

        mermaid_js = assets / "mermaid.js"

        mermaid_js.write_text("""
    window.addEventListener("DOMContentLoaded", function () {
    if (window.mermaid) {
        mermaid.initialize({
        startOnLoad: true,
        theme: "default",
        securityLevel: "loose"
        });
    }
    });
    """, encoding="utf-8")

    # -------------------------
    # HOME
    # -------------------------
    def build_home(self):

        stats = {
            "as_is": len(list((self.docs / "as-is").glob("*.md"))) if (self.docs / "as-is").exists() else 0,
            "blueprints": len(list((self.docs / "blueprints").rglob("*.md"))),
            "to_be": len(list((self.docs / "to-be").glob("*.md"))),
            "gap": len(list((self.docs / "gap").glob("*.md"))),
            "roadmap": len(list((self.docs / "roadmap").glob("*.md"))),
            "concept": len(list((self.docs / "concept").glob("*.md"))),
            "cross": len(list((self.docs / "cross").glob("*.md")))
        }

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        content = f"""# 📚 Plataforma NAV 360

    > Documentação técnica gerada automaticamente  
    > Última atualização: **{now}**

    ---

    ## 🎯 Objetivo

    Este portal consolida a visão arquitetural completa da plataforma NAV 360:

    - Estado Atual (AS-IS)
    - Blueprints por sistema
    - Arquitetura Futura (TO-BE)
    - Análise de GAP
    - Roadmap de Adoção
    - Concept NAV 360
    - Cross Alignment

    ---

    ## 📊 Status da Base

    | Domínio | Arquivos |
    |---------|----------|
    | AS-IS | {stats['as_is']} |
    | Blueprints | {stats['blueprints']} |
    | TO-BE | {stats['to_be']} |
    | GAP | {stats['gap']} |
    | Roadmap | {stats['roadmap']} |
    | Concept | {stats['concept']} |
    | Cross | {stats['cross']} |

    ---

    ## 📁 Navegação Rápida

    ### 🔹 Arquitetura Atual
    - [AS-IS](as-is/scanner.md)

    ### 🔹 Sistemas
    - [Blueprints](blueprints/)

    ### 🔹 Evolução
    - [TO-BE](to-be/)
    - [GAP](gap/)
    - [Roadmap](roadmap/)

    ### 🔹 Estratégia
    - [Concept](concept/)
    - [Cross Analysis](cross/)

    ---

    ## ⚙️ Pipeline

    Esta documentação é produzida automaticamente a partir do pipeline:

    1. Scanner Azure DevOps
    2. Integration Mapping
    3. Layer Analysis
    4. AI Blueprints
    5. TO-BE Generator
    6. GAP Analyzer
    7. Roadmap Generator
    8. Concept Analyzer
    9. Cross Alignment

    ---

    ## 🛡️ Governança

    Uso interno — Engenharia & Arquitetura.

    """

        (self.docs / "index.md").write_text(content, encoding="utf-8")

        self.nav.append({"Home": "index.md"})


    def _copy_md_group(self, pattern, target_dir, title):

        section = self.docs / target_dir
        section.mkdir(exist_ok=True)

        entries = []

        for f in sorted(OUTPUT.glob(pattern)):

            target = section / f.name
            shutil.copy(f, target)

            entries.append(
                {f.stem.replace("_", " "): f"{target_dir}/{f.name}"}
            )

        if entries:
            self.nav.append({title: entries})

    # -------------------------
    # AS-IS
    # -------------------------

    def build_as_is(self):

        asis = self.docs / "as-is"
        asis.mkdir(exist_ok=True)

        scanner_file = OUTPUT / "json" / "azure_scanner.json"

        if not scanner_file.exists():
            return

        with open(scanner_file, encoding="utf-8") as f:
            scan = json.load(f)

        file = asis / "scanner.md"

        text = "# 📦 AS-IS – Repositórios\n\n"

        for p in scan.get("projects", []):
            for r in p.get("repos", []):
                lang = r.get("analysis", {}).get("language", "N/A")
                text += f"- **{r['name']}** ({lang})\n"

        file.write_text(text, encoding="utf-8")

        self.nav.append({
            "AS-IS": [
                {"Scanner": "as-is/scanner.md"}
            ]
        })

    # -------------------------
    # BLUEPRINTS
    # -------------------------

    def build_blueprints(self):

        base = OUTPUT / "*"

        bp_root = self.docs / "blueprints"
        bp_root.mkdir(exist_ok=True)

        sections = []

        for app in OUTPUT.glob("*/blueprints"):

            app_name = app.parent.name

            app_dir = bp_root / app_name
            app_dir.mkdir(exist_ok=True)

            pages = []

            for f in app.glob("*.md"):

                shutil.copy(f, app_dir / f.name)

                pages.append({
                    f.stem: f"blueprints/{app_name}/{f.name}"
                })

            if pages:
                sections.append({app_name: pages})

        if sections:
            self.nav.append({"Blueprints": sections})

    # -------------------------
    # STANDARD GROUPS
    # -------------------------

    def build_tobe(self):
        self._copy_md_group("TO_BE_Model_*.md", "to-be", "TO-BE")

    def build_gap(self):
        self._copy_md_group("Gap_Analysis_*.md", "gap", "GAP")

    def build_roadmap(self):
        self._copy_md_group("Adoption_Roadmap_*.md", "roadmap", "Roadmap")

    def build_concept(self):
        self._copy_md_group("Concept_*_Analysis_*.md", "concept", "Concept")

    def build_cross(self):
        self._copy_md_group(
            "Cross_Analysis_*.md",
            "cross",
            "Cross Analysis"
        )

    # -------------------------
    # CONFIG
    # -------------------------

    def build_config(self):

        cfg = {
            "site_name": "NAV 360 Docs",

            "theme": {
                "name": "material",
                "features": [
                    "navigation.tabs",
                    "navigation.top",
                    "content.code.copy"
                ]
            },

            "nav": self.nav,

            "markdown_extensions": [
                "admonition",
                "pymdownx.details",
                "pymdownx.highlight",
                {
                    "pymdownx.superfences": {
                        "custom_fences": [
                            {
                                "name": "mermaid",
                                "class": "mermaid"
                            }
                        ]
                    }
                }
            ],

            "extra_javascript": [
                "https://unpkg.com/mermaid@10/dist/mermaid.min.js",
                "assets/mermaid.js"
            ],

            "plugins": [
                "search"
            ]
        }

        with open(BASE_DIR / "mkdocs.yml", "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, sort_keys=False, allow_unicode=True)



    # -------------------------
    # PIPELINE
    # -------------------------

    def run(self):

        self.prepare()

        self.build_home()
        self.build_as_is()
        self.build_blueprints()

        self.build_tobe()
        self.build_gap()
        self.build_roadmap()
        self.build_concept()
        self.build_cross()

        self.build_config()


if __name__ == "__main__":
    MkDocsBuilder().run()
