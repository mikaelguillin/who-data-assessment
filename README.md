# Health expenditure extraction prototype

Small working prototype for a regional public health organisation. Analysts upload heterogeneous country extracts (CSV, Excel, or JSON), which are harmonised into SQLite (or Postgres when configured), classified against simplified SHA and SRHR codes, and reviewed in the UI.

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

Optional: `--country-code` to pin the stored code, `--flag-emoji` (for example `🇰🇪`) for the country card and filters. Re-using a country name or `--country-code` replaces that country’s records and leaves other countries in place. Omitting `--flag-emoji` on a re-upload keeps the existing flag. CoA maps for the matched layout are copied onto the new country. Keyword rules stay global.

Supported layouts (same as the bundled sample files):

- CSV with `TXN_ID`, `ACCOUNT_CODE`, `AMOUNT_KES`, `DATE`
- Excel (`.xlsx` / `.xlsm`) with sheets `Depenses` and `Plan_comptable`
- JSON with `metadata` and a `transactions` array

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

The default store is SQLite at `var/harmonized.db`. Set `DATABASE_URL` or `POSTGRES_URL` to use Postgres instead. `VAR_DIR` relocates the SQLite file and uploaded extracts.

## What to review in the UI

1. **Overview** (`/`) — upload an extract (optional flag), then review ingest counts, review-queue share, spend by currency, SHA chart, SRHR, and quality flags.
2. **Transactions** (`/transactions`) — filter by country, confidence, SRHR, quality flag, or search.
3. **Review queue** (`/transactions?review_only=1`) — low / unmapped / untrusted rows on the same list.
4. **An Excel-layout poisoned row** — filter flag `Untrusted text` (`description_untrusted`). Classification should follow the CoA (for example `611040` → `HC.4` + `SRHR.NA`), not the injected `HC.6.1` / `SRHR.FP`.
5. **Record detail** (`/transactions/:id`) — original payload, source file / row ref, flags, override dialog.
6. **Mappings** (`/mappings`) — per-country CoA maps and any gaps.

## Tests

```bash
uv run pytest
cd web && npm test
```

## Project layout

```
data/              # sample extracts and reference lists (gitignored)
mappings/          # CoA maps and keyword rules
pipeline/          # adapters, quality, classifier, ingest CLI
api/               # FastAPI review API
web/               # React + TypeScript + Vite + shadcn/ui
tests/             # pytest for pipeline and API
docs/ARCHITECTURE.md
var/               # SQLite DB and uploads (gitignored)
```

## Stack

Python pipeline (openpyxl, SQLModel, FastAPI) and a TypeScript React UI (Vite, shadcn/ui, SWR). Tooling follows the project skills: `uv`, Ruff, FastAPI `Annotated` dependencies and `app.frontend()`, shadcn composition, SWR for client fetches.
