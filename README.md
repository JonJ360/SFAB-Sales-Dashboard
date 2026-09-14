# Structural Fab Sales Intelligence

Live salesperson reporting sourced read-only from the Structural Fab Dynamics GP company database. This app preserves the SMI Sales Dashboard interaction and reporting contract while using Structural Fab branding and data.

## Reviewed SQL source

| Setting | Value |
|---|---|
| Company | Structural Fab |
| SQL Server | `192.168.1.25,49934` |
| Database | `SFAB` |
| Source view | `dbo.SalesTransactions` |
| Credential target | `Hermes/ARCRM/SMI-SQL` (Windows Credential Manager; never stored here) |

The source was cross-checked against the neighboring SMI AR CRM company configuration, then verified directly: the database identifies as `SFAB`, `dbo.SalesTransactions` exists as a view, and the configured login has SELECT but no INSERT/UPDATE/DELETE permission on the view and required GP sales tables.

## Report contract

- Posted, normal invoices and returns
- Net sales = invoice `Subtotal` less return `Subtotal`
- Cost guard = 10% of sales when source extended cost exceeds sales
- Profit = sales less guarded cost
- Invoice count = distinct invoice SOP number
- Open orders = remaining subtotal on normal, unposted orders
- Tickets written today = distinct normal orders by GP `Created Date`, with `Subtotal` dollars
- Invoices posted today = distinct normal posted invoices by GP `Posted Date`, with `Subtotal` dollars
- Rolling 30 days (`1M`), YTD, selectable month, and overlapping 2024–2026 monthly columns
- Prior-year comparison for rolling 30-day, YTD, selected month, and salesperson views
- Click-through salesperson detail with net KPIs, monthly columns, YTD sales/profit total pies, and customer detail
- Prior-year Top 25 customer watchlist with last year, this year, and dollar difference
- Visible app version in the top-left brand

## Refresh and local preview

```bash
python scripts/sales_sync.py --output data/sales.json
python -m http.server 8765 --bind 127.0.0.1
```

Open `http://127.0.0.1:8765/`. Localhost reads `data/sales.json` directly. The snapshot and all credentials are ignored by Git.

## Authenticated publishing

The `sfab_sales_*` tables and RPCs are deployed in the shared business Supabase project. The hosted browser reads only `sfab_sales_current_snapshot()` after Supabase authentication. An hourly Hermes job extracts from read-only SQL, publishes, promotes, and verifies the current snapshot.

Manual refresh:

```bash
python scripts/sales_sync.py --output data/sales.json
python scripts/publish_snapshot.py --snapshot data/sales.json --credentials "%LOCALAPPDATA%/hermes/arcrm/credentials/current-ar.json"
```

## Tests

```bash
python -m unittest discover -s tests -q
```
