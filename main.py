from __future__ import annotations
from pathlib import Path
from urllib.parse import quote

ALLOWED_EXTS = {".pdf", ".docx", ".xlsx", ".pptx", ".md"}
REPO_BASE_URL = "https://github.com/cheng895/audit/tree/main"


def define_env(env):
    def list_reports(base: Path) -> list[Path]:
        return [p for p in base.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_EXTS]

    def find_projects(client_dir: Path) -> dict[str, list[Path]]:
        projects: dict[str, list[Path]] = {}
        # 仅把客户目录的直接子目录当作“项目”
        for d in sorted([p for p in client_dir.iterdir() if p.is_dir()], key=lambda x: x.name.lower()):
            files = list_reports(d)  # 只列该项目目录下的文件，不递归
            projects[d.name] = sorted(files, key=lambda x: x.name)
        # 如客户根目录直接有报告，也作为一个项目（项目名同客户名）
        root_files = list_reports(client_dir)
        if root_files:
            projects[client_dir.name] = sorted(root_files, key=lambda x: x.name)
        return projects

    def build_catalog_html() -> str:
        root = Path("clients")
        if not root.exists():
            return "<p>暂无 clients 目录。</p>"

        parts: list[str] = []
        for client_dir in sorted([p for p in root.iterdir() if p.is_dir()], key=lambda x: x.name.lower()):
            client = client_dir.name
            parts.append(f"<h2>{client}</h2>")
            projects = find_projects(client_dir)
            if not projects:
                parts.append("<p>暂无项目或报告。</p>")
                continue
            for project_name in sorted(projects.keys(), key=lambda x: x.lower()):
                parts.append(f"<h3>{project_name}</h3>")
                files = projects[project_name]
                if not files:
                    parts.append("<p>暂无报告。</p>")
                else:
                    parts.append("<ul>")
                    for f in files:
                        rel = f.as_posix()
                        url = f"{REPO_BASE_URL}/{quote(rel, safe='/')}"
                        display = f.name
                        parts.append(f"  <li><a href=\"{url}\">{display}</a></li>")
                    parts.append("</ul>")
        return "\n".join(parts)

    @env.macro
    def render_catalog() -> str:
        return build_catalog_html()
