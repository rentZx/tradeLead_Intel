from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_PATHS = [
    "app.py",
    "schema.sql",
    "requirements.txt",
    "README.md",
    ".env.example",
    "VERSION",
    "data",
    "exports",
    "logs",
    "migrations/001_v2_database_upgrade.sql",
    "outputs",
    "scripts",
    "scripts/smoke_demo_data.py",
    "src",
    "src/demo_data.py",
    "work",
]

REQUIRED_REQUIREMENTS = [
    "streamlit",
    "pandas",
    "openpyxl",
    "requests",
    "beautifulsoup4",
    "openai",
    "rapidfuzz",
]

README_KEYWORDS = [
    "安装",
    "配置 API Key",
    "初始化数据库",
    "启动 Streamlit",
    "导入数据",
    "migrate_v2_database.py",
    "verify_v2_database.py",
]


def main() -> None:
    missing_paths = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    if missing_paths:
        raise SystemExit(f"Missing release paths: {', '.join(missing_paths)}")

    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if version != "V2.0-RC1":
        raise SystemExit(f"Unexpected VERSION: {version}")

    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    missing_requirements = [name for name in REQUIRED_REQUIREMENTS if name not in requirements]
    if missing_requirements:
        raise SystemExit(f"Missing requirements: {', '.join(missing_requirements)}")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    missing_readme = [keyword for keyword in README_KEYWORDS if keyword not in readme]
    if missing_readme:
        raise SystemExit(f"README missing sections/keywords: {', '.join(missing_readme)}")

    print("V2.0-RC1 release verification passed.")


if __name__ == "__main__":
    main()
