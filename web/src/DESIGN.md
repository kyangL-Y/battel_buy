# web/src Design

## Goals

- Keep the user-facing UI readable for ordinary users.
- Avoid loading supplier admin, workbench detail, chart, xlsx, and API code before a user reaches those flows.
- Keep compatibility for existing imports from `./api` and `./types`.

## Current Shape

- `api.ts` stays as the public request facade.
- `apiHttpClient.ts` owns axios loading, base URL normalization, and auth headers.
- `apiRequestState.ts` owns request status updates.
- `apiMarketSnapshot.ts` owns static snapshot fallback behavior.
- `apiSupplierRequests.ts` owns supplier quote and settlement endpoints.
- `supplierTypes.ts` owns supplier-specific contracts, re-exported by `types.ts`.

## Decisions

- Keep `api.ts` as a facade so existing components do not need churn.
- Split by ownership first, not by HTTP method or route count.
- Keep type-only compatibility through `types.ts` to avoid broad import rewrites.
- Keep `release/dist` as a local release artifact outside source tracking; deployed legacy hash files are managed by the deployment environment or release scripts.

## Limits

- `types.ts` remains a public barrel and should not regain large domain sections.
- Static snapshot fallback is still part of the API layer; moving it to route-level data loaders would be a separate behavior change.
- `web/src` tests live under `web/tests`, so module scanners that only inspect local child directories may warn about missing tests.
