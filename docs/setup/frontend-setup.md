# Frontend Setup

All commands come from [`frontend/package.json`](../../frontend/package.json) or
[`frontend/README.md`](../../frontend/README.md).

## Step 1 — Navigate and check versions

```bash
cd frontend
node -v        # frontend/README.md links the v24.12.0 installer
npm -v
```

Only `package-lock.json` is present — no yarn, pnpm or bun lockfile — so **npm is the package manager**.

## Step 2 — Install dependencies

```bash
npm i
```

> `frontend/README.md` instructs `npm -i`, which is not a valid npm command. The correct form is `npm i`
> (or `npm install`). [AUDIT.md](../../AUDIT.md) issue 23.

## Step 3 — Configure environment variables

Create `frontend/.env.local`. No env file is committed and no `.env.example` exists.

```ini
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/
API_TOKEN=<the same value as backend/.env API_TOKEN>
NEXT_PUBLIC_OLA_MAPS_API_KEY=<your-ola-maps-key>
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=<your-google-maps-key>
```

Three things matter:

**The trailing slash on `NEXT_PUBLIC_API_URL` is required.** Most route handlers concatenate directly:

```ts
await fetch(`${API_URL}product/list`, { ... })
```

Without it you get `http://127.0.0.1:8000product/list`. A few handlers normalise with
`API_URL.replace(/\/$/, "")` and tolerate either form, but most do not.

**`API_TOKEN` must not have a `NEXT_PUBLIC_` prefix.** It is read only inside server-side route handlers,
so Next.js keeps it out of the client bundle. Adding the prefix would publish your shared token to every
visitor.

**The two Maps keys *are* `NEXT_PUBLIC_` and therefore do ship to the browser.** That is inherent to how
they are used (the Google Maps JS SDK is loaded client-side). Restrict them by HTTP referrer in their
respective consoles.

`frontend/README.md` also lists `OLA_MAPS_API_KEY` and `GOOGLE_MAPS_API_KEY` without the prefix — **no
source file reads those two**; only the `NEXT_PUBLIC_` variants are used.

Full inventory: [environment-variables.md](environment-variables.md).

## Step 4 — Start the development server

```bash
npm run dev
```

Serves on **<http://localhost:3002>** — the script is `next dev -p 3002`, not the Next.js default of
3000. The root path redirects to `/home`.

## Step 5 — Build and run production

```bash
npm run build
npm run start
```

## Step 6 — Lint

```bash
npm run lint
```

Runs `eslint` with `eslint-config-next` core-web-vitals plus TypeScript rules.

## Step 7 — Tests and type-checking

**Not verified from the current implementation.** `package.json` defines no `test` and no type-check
script, and no testing framework is installed. TypeScript is present with `strict: true`, so the
following works although the repository does not define it:

```bash
npx tsc --noEmit
```

## Step 8 — Verify

1. <http://localhost:3002> → redirects to `/home`.
2. Open `/uploade` — the primary image-search screen.
3. Browser Network tab: requests go to `localhost:3002/api/...`, **never** directly to `:8000`.
4. No `PK-apiToken` header should be visible in browser requests — it is added server-side.

If pages load but data is empty, the usual causes are a missing trailing slash on
`NEXT_PUBLIC_API_URL` or a mismatched `API_TOKEN`. See
[../troubleshooting/common-issues.md](../troubleshooting/common-issues.md).

## Command reference

| Purpose | Command | Required | Verified from |
| ------- | ------- | -------- | ------------- |
| Node version | `node -v` | Yes | `frontend/README.md` |
| Package manager | `npm -v` | Yes | `package-lock.json` |
| Install | `npm i` | Yes | `frontend/README.md` (shown there as `npm -i`) |
| Development server | `npm run dev` → **port 3002** | Yes | `package.json` |
| Production build | `npm run build` | Optional | `package.json` |
| Production server | `npm run start` | Optional | `package.json` |
| Lint | `npm run lint` | Optional | `package.json` |
| Tests / type check / format | — | — | Not verified from the current implementation |

## Dependencies actually used

| Package | Used for | Imported |
| ------- | -------- | :------: |
| `next`, `react`, `react-dom` | Framework | ✅ |
| `axios` | Several BFF handlers | ✅ |
| `lucide-react`, `@heroicons/react` | Icons | ✅ |
| `react-select` | Multi-select inputs | ✅ |
| `recharts` | Charts | ✅ |
| `olamaps-web-sdk` | Map rendering | ✅ |
| `tailwindcss` | Styling | ✅ |
| `react-hook-form`, `@hookform/resolvers`, `zod` | Forms/validation | ❌ **not imported anywhere** |
| `exceljs`, `mammoth`, `pdf-parse`, `tesseract.js` | Document processing | ❌ |
| `express`, `express-session`, `cookie-parser`, `openid-client` | Server / auth | ❌ |
| `uuid` | IDs | ❌ |

About a third of the dependency tree is unused. It affects install time and audit surface, not runtime.
