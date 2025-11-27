from __future__ import annotations
from pathlib import Path
from urllib.parse import quote
import re

ALLOWED_EXTS = {".pdf", ".docx", ".xlsx", ".pptx", ".md"}
REPO_BASE_URL = "https://github.com/cheng895/audit/tree/main"


def define_env(env):
    month_names = {
        "jan": "Jan", "january": "Jan",
        "feb": "Feb", "february": "Feb",
        "mar": "Mar", "march": "Mar",
        "apr": "Apr", "april": "Apr",
        "may": "May",
        "jun": "Jun", "june": "Jun",
        "jul": "Jul", "july": "Jul",
        "aug": "Aug", "august": "Aug",
        "sep": "Sep", "sept": "Sep", "september": "Sep",
        "oct": "Oct", "october": "Oct",
        "nov": "Nov", "november": "Nov",
        "dec": "Dec", "december": "Dec",
    }

    def list_reports(base: Path) -> list[Path]:
        return [p for p in base.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_EXTS]

    def find_projects(client_dir: Path) -> dict[str, list[Path]]:
        projects: dict[str, list[Path]] = {}
        # 叶子目录内若包含报告文件，则视为一个项目
        for d in sorted(client_dir.rglob("*")):
            if not d.is_dir():
                continue
            files = list_reports(d)
            if files:
                projects[d.name] = sorted(files, key=lambda x: x.name)
        # 客户根目录自身若有文件，也作为一个项目，项目名=目录名
        root_files = list_reports(client_dir)
        if root_files:
            projects[client_dir.name] = sorted(root_files, key=lambda x: x.name)
        return projects

    def split_camel_case(name: str) -> str:
        # Insert spaces before capital letters in CamelCase tokens, but keep acronyms together
        # Examples: PerpetualsExchange -> Perpetuals Exchange, XMooncake -> X Mooncake
        name = re.sub(r"(?<=[a-z0-9])([A-Z])", r" \1", name)
        # Collapse multiple spaces
        return re.sub(r"\s+", " ", name).strip()

    def format_display_name(filename: str, client: str) -> str:
        """
        Convert filenames like:
          Jupiter-PerpetualsExchange-May-2025-OffsideLabs.pdf
        to display:
          Perpetuals Exchange — May 2025
        Heuristics:
          - Drop leading client name (case-insensitive)
          - Drop trailing 'OffsideLabs' (case-insensitive)
          - Detect tail (Month, Year) if present
          - CamelCase -> spaced words for project part
        """
        name_no_ext = filename.rsplit(".", 1)[0]
        parts = [p for p in name_no_ext.split("-") if p]
        if not parts:
            return filename
        # Drop client prefix
        if parts and parts[0].lower() == client.lower():
            parts = parts[1:]
        # Drop 'OffsideLabs' suffix
        if parts and parts[-1].lower() == "offsidelabs":
            parts = parts[:-1]
        if not parts:
            return filename
        # Detect Month Year at tail
        month = None
        year = None
        if len(parts) >= 2:
            maybe_month = parts[-2].lower()
            maybe_year = parts[-1]
            if maybe_year.isdigit() and len(maybe_year) == 4 and maybe_month in month_names:
                month = month_names[maybe_month]
                year = maybe_year
                parts = parts[:-2]
        project = split_camel_case(" ".join(parts))
        if month and year:
            return f"{project} — {month} {year}"
        return project

    def count_reports_for_client(client_dir: Path) -> int:
        count = 0
        for d in client_dir.rglob("*"):
            if d.is_file() and d.suffix.lower() in ALLOWED_EXTS:
                count += 1
        return count

    def build_catalog_html() -> str:
        root = Path("clients")
        if not root.exists():
            return "<p>暂无 clients 目录。</p>"

        parts: list[str] = []
        for client_dir in sorted([p for p in root.iterdir() if p.is_dir()], key=lambda x: x.name.lower()):
            client = client_dir.name
            # Add id for anchor navigation
            parts.append(f'<section class="client-block" id="{client}">')
            parts.append(f"<h2>{client}</h2>")
            projects = find_projects(client_dir)
            if not projects:
                parts.append("<p>暂无项目或报告。</p>")
            else:
                for project_name in sorted(projects.keys(), key=lambda x: x.lower()):
                    parts.append(f"<h3 class=\"project-title\">{project_name}</h3>")
                    files = projects[project_name]
                    if not files:
                        parts.append("<p>暂无报告。</p>")
                    else:
                        parts.append("<ul>")
                        for f in files:
                            rel = f.as_posix()
                            url = f"{REPO_BASE_URL}/{quote(rel, safe='/')}"
                            display = format_display_name(f.name, client)
                            parts.append(f"  <li><a href=\"{url}\">{display}</a></li>")
                        parts.append("</ul>")
            parts.append('</section>')
        return "\n".join(parts)

    @env.macro
    def render_catalog() -> str:
        return build_catalog_html()

    @env.macro
    def render_featured(client_list: list[str]) -> str:
        """
        Render a featured clients grid with logo, name and report count.
        Links jump to the anchors on the audits page.
        """
        root = Path("clients")
        items: list[str] = []
        items.append('<div class="featured-clients">')
        for client in client_list:
            client_dir = root / client
            count = count_reports_for_client(client_dir) if client_dir.exists() else 0
            logo_src = f"assets/logos/{client.lower()}.svg"
            link = f"audits.md#{client}"
            items.append('<a class="featured-client" href="{link}">'.format(link=link))
            items.append(f'  <img class="featured-client__logo" src="{logo_src}" alt="{client} logo" />')
            items.append(f'  <div class="featured-client__meta">')
            items.append(f'    <div class="featured-client__name">{client}</div>')
            items.append(f'    <div class="featured-client__count">{count} reports</div>')
            items.append('  </div>')
            items.append('</a>')
        items.append('</div>')
        return "\n".join(items)
