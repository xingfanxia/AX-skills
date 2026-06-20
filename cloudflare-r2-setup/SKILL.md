---
name: cloudflare-r2-setup
description: >-
  Set up Cloudflare R2 object storage for a Vercel / Next.js app, or migrate off
  Vercel Blob, the de-risked way — proven write-toggle + host-routed-reads
  architecture plus the full pitfall list (wrangler can't mint S3 keys, Vercel
  CLI env corruption, next/image + CSP blocking R2 images, custom-domain CDN
  caching 404s, private-bucket PII reads, sharp/test gotchas). Use when the user
  says "use R2", "Cloudflare R2", "migrate off Vercel Blob", "object storage for
  Vercel", "S3-compatible storage", "image storage that works in mainland China",
  or sets up an R2 bucket for a server app.
---

# Cloudflare R2 setup (for Vercel / Next.js apps)

**Goal:** wire an app's object storage to Cloudflare R2 (zero egress, China-reachable via a custom domain) — either greenfield or migrating off Vercel Blob — without re-hitting the known traps.

**When:** the app runs on Vercel/Node (NOT a Cloudflare Worker — Workers use bindings, this uses the S3 API), and you need image/file storage, or you're replacing Vercel Blob (frequently blocked in mainland China + bills egress).

## Architecture (do it this way — it's reversible and needs no data migration)

- **Access = the S3-compatible API** via `@aws-sdk/client-s3`. Bindings are Workers-only.
  ```ts
  new S3Client({
    region: "auto",
    endpoint: `https://${R2_ACCOUNT_ID}.r2.cloudflarestorage.com`,
    credentials: { accessKeyId: R2_ACCESS_KEY_ID, secretAccessKey: R2_SECRET_ACCESS_KEY },
  });
  ```
  Inject the `S3Client` so unit tests run offline with a fake `send` (no live creds).
- **Writes branch on `STORAGE_PROVIDER`** (`blob` default | `r2`). Deploy with the default → zero behavior change. Flip the env var to cut over; flip back to roll back. No code redeploy needed to roll back, just the env flip + redeploy.
- **Reads/deletes route by URL host/form, not by provider** — accept BOTH legacy Blob hosts AND the R2 public host. Old URLs in the DB keep resolving forever ⇒ **no bulk data migration**, and rollback is safe in both directions.
- **Public objects:** one public bucket, served via a **custom domain** in production (CDN-cached, the only reliable China surface). The `*.r2.dev` dev-url is rate-limited / dev-only.
- **Private (PII) objects:** a SEPARATE **private** bucket (dev-url DISABLED). Store the S3-endpoint URL as the reference; read server-side via `GetObjectCommand` (the S3 host is not anonymously fetchable — SigV4 required). The reference can round-trip through the client safely.
- All storage goes through ONE module (e.g. `lib/images/storage.ts`) + a thin `r2-client.ts`. Don't scatter `put`/`del` calls.

## Env contract

```
STORAGE_PROVIDER=blob            # blob (default/rollback) | r2
R2_ACCOUNT_ID=<account id>       # also the S3 endpoint subdomain
R2_ACCESS_KEY_ID=<token key>     # SECRET — see "minting creds" below
R2_SECRET_ACCESS_KEY=<token secret>
R2_PUBLIC_URL=https://<custom-domain-or-pub-xxx.r2.dev>   # public bucket
# private bucket name is fine as a code constant; it's read server-side only
```

## Procedure

Bucket + domain ops use `wrangler` (an account login is enough). Order only matters where noted.

```bash
# Buckets (apac location = closest to a China audience)
wrangler r2 bucket create <app>-storage --location apac
wrangler r2 bucket create <app>-uploads --location apac   # private PII, if needed

# Public access — dev only (rate-limited):
wrangler r2 bucket dev-url enable <app>-storage --force
# PRODUCTION public surface — custom domain (CDN-cached, China-grade):
ZONE=$(curl -s "https://api.cloudflare.com/client/v4/zones?name=<your-domain>" \
  -H "Authorization: Bearer $(grep '^oauth_token' ~/Library/Preferences/.wrangler/config/default.toml | sed -E 's/.*"([^"]+)".*/\1/')" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['result'][0]['id'])")
wrangler r2 bucket domain add <app>-storage --domain img.<your-domain> --zone-id "$ZONE" --min-tls 1.2 --force

# PII retention (bound how long private uploads live):
wrangler r2 bucket lifecycle add <app>-uploads pii-expire uploads/ --expire-days 90 --abort-multipart-days 7

# Confirm the private bucket stays private:
wrangler r2 bucket dev-url get <app>-uploads   # must say "disabled"
```

## Pitfalls (this is the point of the skill)

1. **wrangler CANNOT mint the S3 access key.** `wrangler r2` has no token command, and a wrangler-OAuth token returns `9109 Unauthorized` even *listing* tokens. → The operator creates ONE **R2 API token** in the dashboard (R2 → Manage R2 API Tokens → Create, "Object Read & Write"). The Access Key ID + Secret are shown ONCE. The SAME token works for every bucket in the account. This is the one unavoidable human step. (You can also drive the dashboard via browser automation if the operator is logged in.)
2. **The Vercel CLI corrupts env values** — `vercel env add` (and `echo "v" | …`) silently writes empty values or appends a trailing `\n`. NEVER use it. Set env via the **REST API**: `POST https://api.vercel.com/v10/projects/{id}/env?teamId={team}&upsert=true` with a JSON body (`json.dumps` can't introduce trailing whitespace). Read back and assert `value == value.strip()` and no `\r`/`\n`.
3. **The Vercel CLI token expires mid-session** → REST API returns `403 forbidden / Not authorized`. Fix: run any `vercel` CLI read command (e.g. `vercel env ls`) — it refreshes and re-persists the token to `auth.json` — then re-read the token and retry the REST call.
4. **`next/image` + CSP block R2 images — a real prod break the storage smoke can't catch.** If the app uses `next/image` (without `unoptimized`), the R2 host must be in `next.config` `images.remotePatterns`. If the app sends a CSP, the R2 host must be in `img-src` (and `connect-src` if any client `fetch()` hits it). Symptom: generated images 400 from the optimizer or get CSP-blocked AFTER cutover. **Only a browser load catches this** — always load a page in a real browser and check the console for CSP violations. (Plain `<img>` / `<Image unoptimized>` / no-CSP apps are unaffected.)
5. **Custom domains CDN-cache 404s** (`cache-control: max-age=14400`). If anything requests an object key BEFORE it exists, the negative 404 sticks for hours. Real app flows are safe (the object is written before its URL is ever used). For manual testing, use a fresh never-requested key or a `?cb=<ts>` cache-buster. Deletes also stay edge-cached briefly — don't assert "404 after delete" against a cached custom domain.
6. **`wrangler r2 object put --file=…` can store a ~1-byte object.** Upload via the S3 API (`PutObjectCommand`), not the wrangler CLI flag.
7. **Private/PII bucket safety:** keep its dev-url DISABLED, read server-side via GetObject. Add a negative assertion to your smoke: an unauthenticated `fetch()` of the private reference MUST return 401/403, never 200. Document "dev-url must stay disabled" as a hard requirement.
8. **`sharp` can't decode a hand-crafted minimal JPEG** (`VipsJpeg: Quantization table not defined`). Generate smoke-test images WITH sharp, e.g. `sharp({create:{width:16,height:16,channels:3,background:{r,g,b}}}).jpeg().toBuffer()`.
9. **Switching the public host later (r2.dev → custom domain):** keep the OLD host allowed for READS (a transitional `LEGACY_HOSTS` allowlist) until objects written under it age out — otherwise their downloads/validation break. Writes go to the new host; reads accept both.
10. **`import "server-only"`** in a helper that any test imports will crash the test at import time. Only add it to modules that are never imported by the test environment.

## Verification (do all three)

- **Cheap, repeatable:** a `smoke:r2` script — preflight (creds present) + full round-trip (save → public fetch 200 → delete), self-cleaning, plus the private-path GetObject round-trip and the anon-fetch-401/403 assertion. Run it with the prod env to confirm the live config.
- **Browser:** load a real page in Chrome, check the console — **no CSP violations, no image errors**. This is the only thing that catches pitfall #4.
- **Full e2e (when possible):** drive the real upload → process → serve path (API with a test auth header, or Playwright) and assert the returned URLs are the R2 host and fetch 200.

## Acceptance criteria

- Production env has `STORAGE_PROVIDER=r2` + R2 creds + the public-URL custom domain (verified whitespace-clean).
- A live write lands on R2 and fetches 200 via the custom domain; a private write is NOT anonymously fetchable.
- A real browser loads a page that renders an R2 image with zero CSP/console errors.
- Rollback is one env flip (`STORAGE_PROVIDER=blob`) — old URLs still resolve because reads are host-routed.
- Docs state it's LIVE (not "migrating"); the time-gated cleanups (disable r2.dev dev-url, remove legacy-host shim, drop the old SDK) are tracked with their trigger (old URLs aged out), not done prematurely.
