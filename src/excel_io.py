from __future__ import annotations

from io import BytesIO

import pandas as pd

from src.db import get_connection, query_df


PRODUCT_COLUMNS = [
    "product_name_cn",
    "product_name_en",
    "category",
    "sub_category",
    "description_cn",
    "specifications",
    "material",
    "condition",
    "model",
    "brand",
    "quote_price",
    "currency",
    "supplier_name",
    "hs_code",
    "compliance_status",
    "status",
]

COMPANY_COLUMNS = [
    "company_name",
    "country",
    "city",
    "website",
    "email",
    "phone",
    "whatsapp",
    "business_summary",
    "source_url",
    "source_type",
    "related_product_id",
    "match_keywords",
]


def read_tabular(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


def import_products(df: pd.DataFrame) -> int:
    clean = normalize_columns(df, PRODUCT_COLUMNS)
    with get_connection() as conn:
        clean.to_sql("products", conn, if_exists="append", index=False)
    return len(clean)


def import_companies(df: pd.DataFrame) -> int:
    clean = normalize_columns(df, COMPANY_COLUMNS)
    with get_connection() as conn:
        clean.to_sql("companies", conn, if_exists="append", index=False)
    return len(clean)


def normalize_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    clean = df.copy()
    clean.columns = [str(c).strip() for c in clean.columns]
    for col in columns:
        if col not in clean.columns:
            clean[col] = None
    return clean[columns]


def export_table(table: str) -> bytes:
    df = query_df(f"SELECT * FROM {table} ORDER BY id DESC")
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=table[:31])
    return output.getvalue()
