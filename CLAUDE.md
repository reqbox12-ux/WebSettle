# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**WebSettle** is an accounting settlement dashboard for managing financial data across 22 branches of a fitness/golf facility business (라온스포츠). The app aggregates sales, expenses, and payroll data from multiple sources (credit cards, bank accounts, payroll systems) and provides branch-level profitability analysis with automatic transaction classification.

**Tech Stack:**
- Frontend: Streamlit (Python web UI)
- Database: SQLite (`data/settlement.db`)
- Data processing: Pandas + Openpyxl
- Language: Korean (UI), Mixed (Code)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app locally
python -m streamlit run app.py
# OR
./run.bat  # Windows batch wrapper

# Create backup (7 most recent retained)
python backup.py

# Restore from backup
python restore.py
```

## Architecture & Data Flow

### Core Application Flow
```
Excel Files (uploaded by user)
    ↓
[modules/parser.py] Parse Excel files
    ↓ (카드, 통장, 급여 데이터)
[modules/classifier.py] Auto-classify transactions
    ↓ (branch, category 규칙 적용)
[modules/db.py] Store in SQLite
    ↓
[app.py] Dashboard visualization
    ↓ (5 menu pages, branch/monthly aggregation)
```

### Module Responsibilities

**modules/db.py**
- Database initialization and schema management
- Upsert operations: `upsert_card_sales()`, `upsert_bank_transactions()`, `upsert_payroll()`
- Query functions: `get_card_by_branch()`, `get_branch_cash_revenue()`, `get_expense_by_category()`, etc.
- Keyword rule management for auto-classification
- Constants: `REVENUE_CATEGORIES`, `EXPENSE_CATEGORIES` (defines all valid transaction types)

**modules/parser.py**
- Excel file parsing for 5 data sources:
  - `parse_card_aggregate()`: 카드사 결과 집계 조회 (columns: O=합계, P=수수료, Q=입금액, S=가맹점명)
  - `parse_credit_card()`: 신용카드 (columns: G=거래금액, H=공급가액, I=부가세, L=수수료)
  - `parse_hana()`, `parse_shinhan()`: Bank transaction files (dynamic column handling for Shinhan)
  - `parse_payroll_freelance()`, `parse_payroll_insured()`: Payroll from separate tabs
- All return DataFrames with consistent columns: branch, amount, category, vat, etc.
- VAT calculation: `vat = amount ÷ 11` (Korean tax standard)

**modules/classifier.py**
- Keyword-based auto-classification of bank transactions
- `classify_transactions()`: Maps description keywords to branch/category
- `add_rule()`: Creates new classification rules based on user feedback
- Rules stored in database with hit_count tracking

**app.py**
- Streamlit application with 5 menu pages
- Page 1: 전체 집계 (Full Summary) - monthly tabs, KPI dashboard
- Page 2: 지점별 상세 (Branch Detail) - branch selection, trend charts
- Page 3: 📤 데이터 업로드 (Data Upload) - bulk upload interface
- Page 4: 🔍 미분류 검토 (Unclassified Review) - manual classification UI
- Page 5: ⚙️ 분류 규칙 관리 (Rule Management) - view/edit auto-classification rules
- Core function: `build_summary()` - aggregates revenue/expense for each branch

## Critical Business Logic

### Revenue Calculation (Per Branch, Monthly)
```
총매출 = 카드실수령 + 현금공급가액
where:
  카드실수령 = 카드공급가액 - 카드수수료 (already net of fees)
  현금공급가액 = 현금입금액 - 현금부가세 (not gross, supply price)
```

### Expense Calculation (Per Branch, Monthly)
```
총지출 = 부가세합계 + 인건비합계 + 기타지출
NOTE: 카드수수료 NOT included (already deducted from revenue)
      인건비 separates "insured" (4대보험) from "freelance" (사업소득자)
```

### Profit Calculation
```
손익 = 총매출 - 총지출
```

## Data Model

### card_sales Table
- source: "카드사 결과 집계" or "신용카드"
- Columns: branch, raw_merchant, card_company, total_amount, vat, supply_amount, fee, net_amount, sale_date

### bank_transactions Table
- bank: "hana" or "shinhan"
- Columns: tx_date, description, counterpart, deposit, withdrawal, balance, branch, content, category, vat, is_excluded, needs_review
- category: Auto-filled by classifier, can be marked "제외" to exclude from totals

### payroll Table
- type: "insured" (정규직) or "freelance" (프리랜서)
- Columns: branch, gross_pay, net_pay, insurance, income_tax, local_tax, headcount

### keyword_rules Table
- Auto-populated from `mapping/keyword_rules.json`
- Columns: bank, keyword, branch, category, hit_count
- Used for classification in Page 4 (Rule Management)

## File Organization

```
WEBAPP/
├── app.py                      # Main Streamlit app
├── modules/
│   ├── db.py                   # Database layer
│   ├── parser.py               # Excel parsing logic
│   ├── classifier.py           # Auto-classification
│   └── __init__.py
├── mapping/
│   ├── branch_mapping.json     # Card merchant → branch mapping
│   └── keyword_rules.json      # Auto-classification rules (JSON array)
├── data/
│   └── settlement.db           # SQLite database (auto-created)
├── backups/                    # Daily backups (auto-created)
├── backup.py                   # Backup creation script
├── restore.py                  # Backup restoration script
├── run.bat                     # Windows batch wrapper
└── requirements.txt
```

## Development Notes

### Data Upload & Processing
1. User uploads Excel file in Page 3
2. App detects file type (카드/신용카드/통장/급여) based on columns
3. Parser extracts data into standardized DataFrame
4. Classifier auto-assigns branch/category for bank transactions
5. Upsert into SQLite (deletes old month's data, inserts new)
6. Dashboard updates automatically

### Month-based Overwrites
- Uploading new data for a month completely replaces old data for that month
- Backup is recommended before large uploads (use `python backup.py`)

### Currency & Formatting
- All amounts stored as integers (원 units)
- Display uses Korean number format: `{v:,}` (comma-separated)

### Streamlit Gotchas
- State persists across page navigation (use `st.session_state` for sharing)
- `st.experimental_rerun()` replaced with `st.rerun()` in newer versions
- DataFrame filters use boolean indexing, not SQL WHERE clauses

## Common Tasks

### Adding a New Data Source
1. Create parser function in `modules/parser.py` following existing patterns
2. Add upsert function call in `app.py` data upload section
3. Update file detection logic to recognize new file type
4. Test with sample file and verify database schema

### Adding a New Dashboard Metric
1. Query data in `build_summary()` or branch detail page
2. Format using `fmt()` helper for thousands separator
3. Display in Streamlit table or metric card

### Modifying Classification Rules
- Edit `mapping/keyword_rules.json` directly (JSON array of rule objects)
- Or use Page 5 UI to add rules (stores in database, export manually if needed)
- Rules are loaded into database on app startup via `load_keyword_rules()`

## Git & Backup

**Git Usage:**
```bash
git add .
git commit -m "Description in Korean or English"
git push
```

**Backup System:**
- Automated: Run `python backup.py` manually or via Windows Task Scheduler
- Retains 7 most recent backups in `backups/` folder
- Restore: `python restore.py` (interactive selection)
- Failed DB saves as `broken_TIMESTAMP.db` during restore

See `BACKUP_GUIDE.md` for detailed backup procedures.

## Known Limitations & TODOs

- SQLite does not support concurrent writes; multi-user editing requires migration to PostgreSQL
- Streamlit Cloud deployment requires database migration (Neon/Railway for PostgreSQL)
- No authentication layer (assumes single-user or trusted network)
- All transaction dates stored as strings (optimize to datetime if needed for performance)

## Troubleshooting

**Streamlit won't start:**
- Check Python path: `python -c "import streamlit; print(streamlit.__version__)"`
- Run batch file instead: `./run.bat`

**"No such table" error:**
- Database schema not initialized; `modules/db.py` should auto-create on first run
- Delete `data/settlement.db` and restart app if corruption suspected

**Data not appearing after upload:**
- Check `needs_review` flag in bank_transactions (Page 4 classification)
- Verify category is not "제외" (excluded category)
- Confirm year/month selector matches uploaded data

**Import errors:**
- Run `pip install -r requirements.txt` if dependencies missing
- Check Python version (3.8+)
