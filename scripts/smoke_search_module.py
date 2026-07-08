from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import src.db as db
from src.search import (
    create_search_task,
    generate_search_keywords,
    import_search_results_to_companies,
    run_search_provider,
    save_search_query,
    save_search_results,
    update_task_counts,
)

TEST_DB = ROOT / "work" / "search_smoke.sqlite3"


def main() -> None:
    TEST_DB.unlink(missing_ok=True)
    db.DB_PATH = TEST_DB
    db.init_db()

    product_id = db.execute(
        """
        INSERT INTO products(product_name_cn, product_name_en, category, status)
        VALUES (?, ?, ?, ?)
        """,
        ("塑料收纳箱", "plastic storage box", "塑料小件制品", "在售"),
    )
    product = db.query_df("SELECT * FROM products WHERE id = ?", (product_id,)).iloc[0].to_dict()
    keyword_rows = generate_search_keywords(product, ["Kazakhstan"], ["英语"])
    task_id = create_search_task(product_id, product["product_name_cn"], ["Kazakhstan"], ["英语"], "Mock")

    inserted_total = 0
    for row in keyword_rows[:2]:
        query_id = save_search_query(task_id, product_id, row, "Mock")
        results = run_search_provider("Mock", row["keyword"], row["country"], row["language"], limit=3)
        stats = save_search_results(task_id, query_id, results)
        inserted_total += stats["inserted"]
    update_task_counts(task_id)

    result_ids = [
        int(row.id)
        for row in db.query_df("SELECT id FROM search_results WHERE task_id = ? AND is_duplicate = 0", (task_id,)).itertuples(index=False)
    ]
    import_stats = import_search_results_to_companies(product_id, result_ids)

    assert inserted_total > 0, "expected inserted search results"
    assert import_stats["imported"] > 0, "expected imported companies"
    print(f"search smoke passed: results={inserted_total}, imported={import_stats['imported']}")


if __name__ == "__main__":
    main()
