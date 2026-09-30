# Monthly rebar pounds (release 1.2)

This extends the existing authenticated SFAB snapshot; it is not a static data export.

- **Commodity rebar:** explicitly reviewed 20-foot items.
- **Fabricated rebar:** explicitly reviewed 40-foot items and coils.
- Sold (SOP type 3) and returned (type 4) pounds are separate positive quantities; net is signed sold minus returned.
- Direct-LBS only, posted, nonvoid, non-component, QTYBSUOM=1 and an unambiguous item schedule LBS-to-LBS factor of 1. No pieces/feet/weight conversions. Membership uses an explicit reviewed item allowlist, keyed by item-ID digest. This is a maintainable allowlist, not an anonymization guarantee.
- Unknown/non-LBS/missing schedule evidence remains unknown. A month/group/kind with no validated lines and unresolved monthly candidates displays unknown, not zero. Otherwise amounts are the validated subset, never full production totals. Candidate discovery is bounded REBAR-class/description/coil matching, not proof of complete membership.
- Prepaid remains included; included prepaid sold/returned pounds are separately reported. No management-report or ton reconciliation is asserted.
- History starts 2024-01-01 through the source as-of date. Source-line identities must be unique; cap or validation failures cannot yield truncated totals. Partial current months are only through the displayed as-of date.
- Decimal strings preserve exact numeric detail in the table and CSV; Chart.js numeric values are visualization only.
- Financial YTD/month controls do not scope rebar; its explicit year selector does. Existing reports, hosted Auth/RPC loading and refresh behavior are preserved.
- SFAB retains its own absolute-header-cost policy (cost above subtotal replaced with 10% of subtotal). This is not SMI cost policy or GL net income.

## Runtime and failure behavior

`scripts/sales_sync.py` adds `rebar` and `rebar_status` to the normal hash-validated payload. The unchanged publisher transports that JSON through existing stage/promote/current RPCs. A rebar source-query or validation error makes only rebar unavailable; the established financial refresh continues. A missing rebar property from an old payload is visibly unavailable, never zero. No database migration is required by the checked repository JSONB object contract; deployment must still confirm the live contract.

Private data/sales.json remains Git-ignored and must not be committed or uploaded as a Pages asset. No captures or evidence files belong in the public release.

## Verification

`python -m unittest discover -s tests -v`

`node --check rebar.js`

`git diff --check`

For a **read-only** local source smoke test only: `python scripts/sales_sync.py --output data/sales.json`.
This does not publish. Do not run the installed refresh wrapper during prepublication review: it also publishes.

A bounded private Playwright harness and independent all-month Decimal reconciliation are retained in the FAB preview evidence directory, outside this repository. Deployment requires a real authenticated hosted workflow, exact served payload/metadata readback and a natural scheduled refresh check.
