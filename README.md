# TradeLead Intel 外贸线索情报系统

版本：V2.0-RC1

本项目是面向 B2B 外贸获客、公司背调、合规筛查、产品落地页和询盘管理的本地版系统。技术栈为 Python + Streamlit + SQLite。

## 功能范围

- 产品资料库：产品录入、查询、Excel/CSV 导入导出。
- 演示数据：生成/清空隔离演示样本，不影响真实数据。
- 自动搜索：按产品、国家、语言生成关键词，调用搜索 API，保存搜索结果，支持 URL/域名去重和一键导入公司线索。
- 官网读取：批量读取公司官网公开页面，提取正文、邮箱、电话、WhatsApp、Telegram 和社交媒体链接。
- 背调证据链：生成可解释评分，保存评分理由、证据片段、来源 URL、命中关键词和置信度。
- 合规风险中心：导入制裁名单 CSV，使用 rapidfuzz 模糊匹配公司名，增强风险关键词库，标记风险池客户。
- 产品落地页与询盘：生成静态 HTML 产品页，接收询盘表单，保存询盘并支持转入 CRM。
- CRM 跟进：记录联系时间、渠道、内容、客户回复、下次跟进和阶段。

## 合规边界

- 不自动群发邮件。
- 不绕过验证码、登录墙、付费墙。
- 不采集 LinkedIn 个人信息。
- 不提供规避制裁、出口管制或报关监管的方案。
- 不替代律师、报关行、货代、银行或专业合规审核。

## 项目目录

```text
.
├─ app.py                         # Streamlit 入口
├─ schema.sql                     # 当前 V2.0 数据库基线
├─ requirements.txt               # Python 依赖
├─ .env.example                   # 环境变量模板
├─ VERSION                        # 当前版本号
├─ data/                          # SQLite 数据库与备份
├─ exports/                       # 用户导出文件目录
├─ logs/                          # 日志目录
├─ migrations/                    # 数据库迁移 SQL
├─ outputs/                       # 生成的用户可用产物
├─ scripts/                       # 迁移、校验、smoke 测试脚本
├─ src/                           # 业务模块
└─ work/                          # 临时文件、隔离测试数据库
```

核心模块位于 `src/`：

```text
compliance.py        合规风险中心
db.py                SQLite 连接和通用查询
demo_data.py         演示数据生成与清空
due_diligence.py     背调证据链
excel_io.py          Excel/CSV 导入导出
landing_pages.py     产品落地页和询盘接收
prompts.py           提示词和关键词模板
risk.py              风险关键词检测
scoring.py           客户评分
search.py            自动搜索
webpage_reader.py    官网读取
```

## 安装

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

如使用 Codex 内置 Python，可将命令中的 `python` 替换为内置 Python 路径。

## 配置 API Key

复制 `.env.example` 为 `.env`，按需填写搜索 API Key：

```powershell
Copy-Item .env.example .env
```

支持的搜索 API：

```text
SERPAPI_API_KEY=
BING_SEARCH_API_KEY=
BING_SEARCH_ENDPOINT=https://api.bing.microsoft.com/v7.0/search
GOOGLE_CSE_API_KEY=
GOOGLE_CSE_ID=
```

未配置真实 API 时，可以在“自动搜索”页面选择 `Mock`，用于本地流程测试。

## 初始化数据库

首次运行应用会自动根据 `schema.sql` 创建数据库：

```text
data/tradelead.sqlite3
```

也可以显式运行 V2.0 迁移和校验脚本：

```powershell
python scripts\migrate_v2_database.py
python scripts\verify_v2_database.py
```

迁移脚本会在升级前自动备份当前 SQLite 数据库到：

```text
data/tradelead_before_v2_*.sqlite3
```

数据库迁移文件保留在：

```text
migrations/001_v2_database_upgrade.sql
```

## 启动 Streamlit

```powershell
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

访问地址：

```text
http://127.0.0.1:8501
```

## 启动产品页询盘服务

在“产品落地页/询盘”页面点击“启动询盘接收服务”。默认服务地址：

```text
http://127.0.0.1:8765
```

生成的静态 HTML 产品页位于：

```text
outputs/landing_pages/
```

## 导入数据

产品导入建议列名：

```text
product_name_cn, product_name_en, category, sub_category, description_cn, specifications,
material, condition, model, brand, quote_price, currency, supplier_name, hs_code,
compliance_status, status
```

公司线索导入建议列名：

```text
company_name, country, city, website, email, phone, whatsapp, business_summary,
source_url, source_type, related_product_id, match_keywords
```

制裁名单 CSV 会自动兼容常见列名：

```text
source, entity_name/name/sdn_name/primary_name/full_name, aliases/alias/aka,
country, address, entity_type/type, program, remarks/notes
```

## 验证与封版检查

数据库结构校验：

```powershell
python scripts\verify_v2_database.py
```

模块 smoke 测试：

```powershell
python scripts\smoke_search_module.py
python scripts\smoke_webpage_reader.py
python scripts\smoke_due_diligence.py
python scripts\smoke_compliance.py
python scripts\smoke_landing_pages.py
python scripts\smoke_demo_data.py
```

## 演示数据

“演示数据”页面可一键生成：

- 10 条产品样本，覆盖塑料制品、普通二手机床、塑料机械。
- 30 条候选公司样本，国家包括俄罗斯、哈萨克斯坦、乌兹别克斯坦、阿联酋、埃及、尼日利亚。
- 5 条风险名单样本。
- 5 条询盘样本。
- 10 条 CRM 跟进样本。

所有演示公司都会明确标记：

```text
演示数据，不可用于真实联系
```

清空演示数据只删除带 `DEMO_DATA`、`source_type = demo`、`DEMO_SANCTIONS` 或 `demo://` 标记的数据，不删除真实数据。

Streamlit 页面加载测试可使用：

```powershell
python -c "from streamlit.testing.v1 import AppTest; app=AppTest.from_file('app.py'); app.run(timeout=15); print(len(app.exception))"
```

## V2.0-RC1 封版状态

- 数据库迁移脚本已保留。
- `data/`、`exports/`、`logs/`、`outputs/`、`work/` 目录已建立。
- `.env.example` 已提供。
- `requirements.txt` 已包含当前运行所需依赖。
- 版本号已标记为 `V2.0-RC1`。
