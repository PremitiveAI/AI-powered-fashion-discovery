# Frontend Architecture

Next.js 16 App Router application in [`frontend/`](../../frontend/) — 91 files.

## Directory layout

```
frontend/app/
├── layout.tsx              the only layout
├── globals.css
├── (auth)/                 route group — pages (NO layout, NO guard)
│   ├── uploade/                    image search — the primary screen
│   ├── try-on/                     virtual try-on
│   ├── product-list/  add-product/ catalogue management
│   ├── store-list/    add-store/   store management
│   ├── history/                    past searches
│   ├── ola-map/                    nearby stores
│   ├── phase2/{home,loading,look-detail,style-profile}/
│   └── phase3/{home,beauty-profile,look-detail}/
├── (main)/
│   ├── home/                       landing page
│   └── dashboard/                  dashboard + DashboardLayout (the real chrome)
├── api/                    37 Route Handlers — the BFF proxy layer
├── components/       (9)   DocumentUpload, EmployeeRow, SafeImage, StatCard,
│                           button, loader, logout, pagination, toast
├── hooks/            (2)   useContainerReady, useNetworkStatus
├── utils/            (4)   api, crypto, data-dummy, networkFetch
└── lib/              (2)   data, types
```

**18 pages, 37 BFF handlers.**

## Route groups carry no behaviour

`(auth)` and `(main)` are Next.js route groups — parentheses exclude the segment from the URL. Here they
are **naming conventions only**:

- No `layout.tsx` in either group; only `app/layout.tsx` exists.
- No `middleware.ts` anywhere.
- No login page, no route guard.

A page under `(auth)` is exactly as public as one under `(main)`. See
[../security/authentication-and-authorization.md](../security/authentication-and-authorization.md).

## Layout and chrome

`app/layout.tsx` sets fonts and global CSS. The real application chrome is `DashboardLayout`
([`app/(main)/dashboard/DashboardLayout.tsx`](../../frontend/app/(main)/dashboard/DashboardLayout.tsx)),
imported explicitly by each page rather than applied through the router.

`next.config.ts` declares two things:

```ts
async redirects() { return [{ source: "/", destination: "/home", permanent: true }] }
images: { domains: ["images.unsplash.com"] }
```

## The BFF layer

Every handler in `app/api/**/route.ts`:

1. Reads the incoming body or route params.
2. Calls FastAPI with `PK-apiToken` from the server environment.
3. Returns the backend payload, usually verbatim.

Two implementation styles coexist — `fetch` and `axios`. The axios handlers (`history`, `product-list`,
`store-list`, `product-delete`, `store-delete`, `project`-style routes) additionally **unwrap the
envelope** and reshape the payload, so their pages consume a different response shape from the rest.

### Complete route map

| Frontend handler | Backend endpoint | Status |
| ---------------- | ---------------- | ------ |
| `POST /api/search` | `POST /product/search` | ✅ |
| `POST /api/image-upload` | `POST /gallery/upload` | ✅ |
| `POST /api/product-add` | `POST /product/save` | ✅ |
| `POST /api/product-list` | `POST /product/list` | ✅ |
| `GET /api/product-details/[id]` | `GET /product/get/{id}` | ✅ |
| `DELETE /api/product-delete/[id]` | `DELETE /product/delete/{id}` | ✅ |
| `POST /api/history` | `POST /product/historylist` | ✅ |
| `POST /api/try-on` | `POST /photo/try-on` | ✅ |
| `POST /api/add-store` | `POST /store/save` | ✅ |
| `POST /api/store-list` | `POST /store/list` | ✅ |
| `GET /api/store-detail/[id]` | `GET /store/details/{id}` | ✅ |
| `DELETE /api/store-delete/[id]` | `DELETE /store/delete/{id}` | ✅ |
| `POST /api/master/category-list` | `POST /master/category/list` | ✅ |
| `POST /api/master/brand-list` | `POST /master/brand/list` | ✅ |
| `POST /api/master/color-list` | `POST /master/color/list` | ✅ |
| `POST /api/product-type` | `POST /master/product/list` | ✅ |
| `POST /api/master/pattern` | `POST /master/pattern/list` | ❌ **backend route missing** |
| `POST /api/master/sub-type` | `POST /master/subtype/list` | ❌ **backend has `subcategory/list`** |
| `POST /api/nearby-stores` | Ola Maps (direct) | ✅ |
| 8 × `/api/phase2/*` | `/models/*` | ⚠️ **5 of 9 targets exist** |
| 8 × `/api/phase3/*` | `cosmetics/*` | ❌ **no backend router** |

Detail: [../features/phase2-models.md](../features/phase2-models.md),
[../features/phase3-cosmetics.md](../features/phase3-cosmetics.md).

## Configuration

[`app/utils/api.ts`](../../frontend/app/utils/api.ts) exports every configuration value:

```ts
export const API_URL   = process.env.NEXT_PUBLIC_API_URL || "";
export const API_TOKEN = process.env.API_TOKEN || "";
// GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI,
// SESSION_SECRET, ISSUER_URL, CLIENT_ID — exported, never consumed
```

Only the first two are used. Because the file is imported exclusively by server-side handlers,
`API_TOKEN` never reaches the browser — that is the intended design.

Maps keys are read directly in the pages/handlers that need them:
`NEXT_PUBLIC_OLA_MAPS_API_KEY` (nearby-stores, add-store) and `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`
(uploade). Both are `NEXT_PUBLIC_`-prefixed and therefore **do** ship to the browser.

## State management

There is none in the library sense. Every page is a `"use client"` component using `useState`,
`useEffect`, `useRef` and `useCallback`. No Redux, Zustand, React Query or Context provider.

`react-hook-form`, `@hookform/resolvers` and `zod` are dependencies but are **not imported by any source
file** — all forms are manually controlled.

## Error handling

Three layers, applied inconsistently: `res.ok` checks, `Code !== 0` checks, and `console.error`.
[`app/utils/networkFetch.ts`](../../frontend/app/utils/networkFetch.ts) is a richer wrapper offering
offline detection and an `AbortController` timeout, but it is **imported by no page**;
`useNetworkStatus` is likewise unused.

## Build configuration

| File | Purpose |
| ---- | ------- |
| `next.config.ts` | `/` → `/home` redirect; Unsplash image domain |
| `tsconfig.json` | `strict: true`, `@/*` → project root |
| `postcss.config.mjs` | `@tailwindcss/postcss` |
| `eslint.config.mjs` | `eslint-config-next` core-web-vitals + typescript |

`package.json` scripts: `dev` (**`next dev -p 3002`**), `build`, `start`, `lint`. **No `test` and no
type-check script**, though `npx tsc --noEmit` works.

## Unused dependencies

Roughly a third of `package.json` is not imported anywhere: `exceljs`, `mammoth`, `pdf-parse`,
`tesseract.js`, `express`, `express-session`, `cookie-parser`, `openid-client`, `uuid`,
`react-hook-form`, `@hookform/resolvers`, `zod`. They inflate install time and audit surface without
affecting runtime.
