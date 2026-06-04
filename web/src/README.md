# web/src

Frontend source for the purchasing, supplier, and admin screens.

## Responsibilities

- Route users into the correct shell: purchasing app, supplier portal, supplier backend, or platform admin.
- Keep first-screen loading small by deferring heavy workbench, chart, xlsx, API, and message modules until needed.
- Keep API request contracts in typed modules while preserving the existing `./types` and `./api` import surface.

## Key Files

- `api.ts`: public API facade used by existing callers.
- `apiHttpClient.ts`: lazy axios client and auth header handling.
- `apiMarketSnapshot.ts`: static market snapshot fallback helpers.
- `apiSupplierRequests.ts`: supplier quote and settlement requests.
- `types.ts`: shared public type barrel.
- `supplierTypes.ts`: supplier domain request and response types.
- `lazyApi.ts`, `lazyXlsx.ts`: lazy import entry points for heavier modules.

## Tests

Run from `web/`:

```powershell
npm run typecheck
npm run build
npx playwright test --config=playwright.current-ui.config.ts --workers=1
```
