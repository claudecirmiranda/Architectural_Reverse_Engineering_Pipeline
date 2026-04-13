from pathlib import Path
import shutil
import yaml
import json


BASE = Path(__file__).parent
OUTPUT = BASE / "outputs"
DOCS = BASE / "docs"


class InternalDocsPublisher:

    def __init__(self):
        self.nav = []

    # -------------------------
    def reset_docs(self):

        if DOCS.exists():
            shutil.rmtree(DOCS)

        DOCS.mkdir()

    # -------------------------
    def home(self):

        content = """# 📘 Plataforma de Arquitetura

Repositório vivo de conhecimento técnico.

Atualizado automaticamente via pipeline.
"""

        (DOCS / "index.md").write_text(content, encoding="utf-8")

        self.nav.append({"Home": "index.md"})

    # -------------------------
    def platform(self):

        p = DOCS / "platform"
        p.mkdir()

        shutil.copy(OUTPUT / "reports/ONBOARDING.md",
                    p / "onboarding.md")

        self.nav.append({
            "Plataforma": [
                {"Onboarding": "platform/onboarding.md"}
            ]
        })

    # -------------------------
    def as_is(self):

        base = DOCS / "as-is"
        base.mkdir()

        # Scanner
        scan = json.load(open(OUTPUT / "json/azure_scanner.json"))

        text = "# 📦 AS-IS – Repositórios\n\n"

        for prj in scan["projects"]:
            for r in prj["repos"]:
                text += f"- **{r['name']}**\n"

        (base / "scanner.md").write_text(text, encoding="utf-8")

        # Repos
        repos_dir = base / "repos"
        repos_dir.mkdir()

        for f in (OUTPUT / "reports/repos").glob("*.md"):
            shutil.copy(f, repos_dir / f.name)

        self.nav.append({
            "AS-IS": [
                {"Scanner": "as-is/scanner.md"},
                {"Repositórios": "as-is/repos/"}
            ]
        })

    # -------------------------
    def blueprints(self):

        bp = DOCS / "blueprints"
        bp.mkdir()

        for system in (OUTPUT).glob("nav-*"):
            target = bp / system.name
            shutil.copytree(system / "blueprints", target)

        self.nav.append({"Blueprints": "blueprints/"})

    # -------------------------
    def tobe(self):

        t = DOCS / "to-be"
        t.mkdir()

        for f in OUTPUT.glob("TO_BE_Model_*.md"):
            shutil.copy(f, t / "model.md")

        self.nav.append({"TO-BE": "to-be/model.md"})

    # -------------------------
    def gap(self):

        g = DOCS / "gap"
        g.mkdir()

        for f in OUTPUT.glob("Gap_Analysis_*.md"):
            shutil.copy(f, g / "analysis.md")

        self.nav.append({"GAP": "gap/analysis.md"})

    # -------------------------
    def roadmap(self):

        r = DOCS / "roadmap"
        r.mkdir()

        for f in OUTPUT.glob("Adoption_Roadmap_*.md"):
            shutil.copy(f, r / "adoption.md")

        self.nav.append({"Roadmap": "roadmap/adoption.md"})

    # -------------------------
    def concept(self):

        c = DOCS / "concept"
        c.mkdir()

        for f in OUTPUT.glob("Concept_*.md"):
            shutil.copy(f, c / "transcript.md")

        self.nav.append({"Concept": "concept/transcript.md"})

    # -------------------------
    def cross(self):

        c = DOCS / "cross"
        c.mkdir()

        for f in OUTPUT.glob("Cross_*.md"):
            shutil.copy(f, c / "alignment.md")

        self.nav.append({"Cross": "cross/alignment.md"})

    # -------------------------
    def diagrams(self):

        d = DOCS / "diagrams"
        d.mkdir()

        shutil.copy(OUTPUT / "diagrams/dependency_graph.mmd",
                    d / "dependency.mmd")

        self.nav.append({"Diagramas": "diagrams/"})

    # -------------------------
    def config(self):

        cfg = {
            "site_name": "Arquitetura Interna",
            "theme": {"name": "material"},
            "nav": self.nav,
            "markdown_extensions": [
                "admonition",
                "pymdownx.superfences",
                "pymdownx.details"
            ]
        }

        with open(BASE / "mkdocs.yml", "w") as f:
            yaml.dump(cfg, f, sort_keys=False)

    # -------------------------
    def run(self):

        self.reset_docs()

        self.home()
        self.platform()
        self.as_is()
        self.blueprints()
        self.tobe()
        self.gap()
        self.roadmap()
        self.concept()
        self.cross()
        self.diagrams()

        self.config()


if __name__ == "__main__":
    InternalDocsPublisher().run()
