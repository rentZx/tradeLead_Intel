#!/usr/bin/env python3
"""
Mock 产品数据录入：保温钉 (Insulation Anchor)
将保温钉产品插入产品资料库
"""

import sqlite3
import sys
from pathlib import Path

# 数据库路径
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tradelead.sqlite3"


def insert_insulation_anchor():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 检查是否已存在同名产品
    existing = cursor.execute(
        "SELECT id, product_name_cn FROM products WHERE product_name_cn = ?",
        ("保温钉（外墙保温锚固钉）",),
    ).fetchone()

    if existing:
        print(f"⚠️  产品已存在: ID={existing['id']}, 名称={existing['product_name_cn']}")
        print("   如需重新录入，请先在数据库中删除该记录。")
        conn.close()
        return

    product = {
        "product_name_cn": "保温钉（外墙保温锚固钉）",
        "product_name_en": "Insulation Anchor / EIFS Wall Anchor",
        "product_name_ru": "дюбель для теплоизоляции (тарельчатый дюбель)",
        "product_name_ar": "مرساة عزل حراري / وتد عزل الجدران",
        "product_name_fr": "Cheville d'isolation / Cheville à rosace",
        "category": "建筑五金",
        "sub_category": "保温锚固件",
        "description_cn": (
            "外墙保温锚固钉（保温钉/膨胀保温钉），由尼龙塑料套管+镀锌钢钉芯组成，"
            "用于EPS/XPS岩棉保温板在外墙基层的机械锚固。广泛适用于民用建筑、"
            "工业厂房外墙外保温系统（EIFS/ETICS）。出口热门品类，中东、俄罗斯、"
            "中亚、非洲市场需求量大。"
        ),
        "description_en": (
            "EIFS insulation anchor (expansion anchor) for exterior wall thermal "
            "insulation systems. Consists of nylon/PP sleeve + galvanized steel nail. "
            "Suitable for fixing EPS/XPS/rock wool insulation boards to concrete, "
            "brick, and hollow block substrates. Hot export category with strong "
            "demand in Middle East, CIS, and Africa markets."
        ),
        "specifications": (
            "套管直径: 8mm/10mm; "
            "长度: 60/80/100/120/140/160/180/200mm; "
            "钢钉直径: 4.5mm/5.0mm; "
            "钉盘直径: 50mm/60mm; "
            "锚固深度: ≥25mm(混凝土)/≥50mm(砖墙)/≥65mm(空心砌块); "
            "单钉拉拔力: ≥0.6kN(混凝土)"
        ),
        "material": "PP/PA6尼龙 + Q235镀锌钢钉",
        "condition": "全新",
        "model": "IA-10×100 (8mm套管×100mm长)",
        "brand": "Demo Hardware",
        "year": "2026",
        "weight": "8-12g/pc (100mm规格)",
        "dimensions": "盘径60mm × 总长80-200mm",
        "moq": "10000 pcs",
        "purchase_price": 0.018,
        "quote_price": 0.035,
        "currency": "USD",
        "supplier_name": "Demo Hardware",
        "supplier_contact": "demo-contact@example.com",
        "hs_code": "3926.9090.90",
        "export_control_note": "无特殊出口管制，普通建筑五金类。如含钢钉需确认目的国对钢铁制品的反倾销政策。",
        "compliance_status": "待复核",
        "status": "在售",
    }

    cursor.execute(
        """
        INSERT INTO products(
            product_name_cn, product_name_en, product_name_ru, product_name_ar, product_name_fr,
            category, sub_category, description_cn, description_en, specifications,
            material, condition, model, brand, year, weight, dimensions,
            moq, purchase_price, quote_price, currency,
            supplier_name, supplier_contact, hs_code, export_control_note,
            compliance_status, status
        ) VALUES (
            :product_name_cn, :product_name_en, :product_name_ru, :product_name_ar, :product_name_fr,
            :category, :sub_category, :description_cn, :description_en, :specifications,
            :material, :condition, :model, :brand, :year, :weight, :dimensions,
            :moq, :purchase_price, :quote_price, :currency,
            :supplier_name, :supplier_contact, :hs_code, :export_control_note,
            :compliance_status, :status
        )
        """,
        product,
    )
    conn.commit()

    product_id = cursor.lastrowid

    # 验证插入
    row = cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()

    print("=" * 60)
    print(f"✅ 保温钉产品已成功录入！")
    print(f"   ID: {product_id}")
    print(f"   中文名: {row['product_name_cn']}")
    print(f"   英文名: {row['product_name_en']}")
    print(f"   品类: {row['category']} > {row['sub_category']}")
    print(f"   采购价: {row['purchase_price']} USD/pc")
    print(f"   报价: {row['quote_price']} USD/pc")
    print(f"   HS编码: {row['hs_code']}")
    print(f"   型号: {row['model']}")
    print(f"   材质: {row['material']}")
    print(f"   起订量: {row['moq']}")
    print(f"   合规状态: {row['compliance_status']}")
    print("=" * 60)

    # 显示产品库总数
    conn = sqlite3.connect(str(DB_PATH))
    count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    conn.close()
    print(f"\n📦 产品库当前总计: {count} 个产品")


if __name__ == "__main__":
    insert_insulation_anchor()
