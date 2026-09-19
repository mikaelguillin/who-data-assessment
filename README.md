# Health expenditure extraction prototype

Small working prototype for a regional public health organisation. Analysts upload heterogeneous country extracts (CSV, Excel, or JSON), which are harmonised into SQLite, classified against simplified SHA and SRHR codes, and reviewed in the UI.

Classification is **chart-of-account first**. Free-text descriptions are not trusted as the primary signal — the Excel layout includes prompt-injection strings in `libelle`. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design, assumptions, and how uncertainty is handled.

## Requirements

- Python 3.11+ with [uv](https://docs.astral.sh/uv/)
- Node.js 20+ for the analyst UI

## Ingest

The app starts empty. Upload a country extract from **Overview**, or from the CLI:

```bash
uv sync --extra dev
uv run python -m pipeline --file data/country_a_expenditure.csv --country-name "Country A"
uv run python -m pipeline --file data/country_b_depenses.xlsx --country-name "Country B"
uv run python -m pipeline --file data/country_c_expenditure.json --country-name "Country C"
```

Supported layouts (same as the bundled sample files):

- CSV with `TXN_ID`, `ACCOUNT_CODE`, `AMOUNT_KES`, `DATE`
- Excel with sheets `Depenses` and `Plan_comptable`
- JSON with `metadata` and a `transactions` array

Re-using a country name or `--country-code` replaces that country’s records and leaves other countries in place. CoA maps for the matched layout are copied onto the new country. Keyword rules stay global.

Expected result on the three sample files: 7,000 expenditures (2,500 + 2,000 + 2,500), quality flags for missing/negative amounts, duplicate IDs, future dates, sub-transactions, and four untrusted Excel-layout descriptions.

## Run the analyst app

Development (API + Vite):

```bash
uv run fastapi dev
# in another terminal
cd web && npm install && npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to FastAPI on port 8000.

Production-style (API serves the built SPA):

```bash
cd web && npm run build
uv run fastapi run
```

Then open http://127.0.0.1:8000.

## What to review in the UI

1. **Overview** — upload an extract, then review ingest counts, review-queue share, spend by currency, SHA chart.
2. **Review queue** — low / unmapped / untrusted rows.
3. **An Excel-layout poisoned row** — filter flag `description_untrusted`. Classification should follow the CoA (for example `611040` → `HC.4` + `SRHR.NA`), not the injected `HC.6.1` / `SRHR.FP`.
4. **Record detail** — original payload, source file / row ref, flags, override dialog.
5. **Mappings** — per-country CoA maps and any gaps.

## Project layout

```
data/              # immutable source extracts and reference lists
mappings/          # CoA maps and keyword rules
pipeline/          # adapters, quality, classifier, ingest CLI
api/               # FastAPI review API
web/               # React + TypeScript + Vite + shadcn/ui
docs/ARCHITECTURE.md
var/harmonized.db  # created by ingest (gitignored)
```

## Stack

Python pipeline (openpyxl, SQLModel, FastAPI) and a TypeScript React UI (Vite, shadcn/ui, SWR). Tooling follows the project skills: `uv`, Ruff, FastAPI `Annotated` dependencies and `app.frontend()`, shadcn composition, SWR for client fetches.
