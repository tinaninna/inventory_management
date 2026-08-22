# Deployment guide

Stack stays exactly as-is: React/Vite frontend, FastAPI backend, MySQL database.
No code framework changes — just three free hosting accounts wired together.

- **Database (MySQL):** Aiven — always-free tier, no credit card, no expiry.
- **Backend (FastAPI):** Render — free web service, deploys straight from GitHub.
- **Frontend (React/Vite):** Vercel — free, zero-config for Vite.

Total time if nothing goes wrong: ~30–40 minutes.

---

## 1. Push your project to GitHub

Render and Vercel both deploy from a GitHub repo. If you haven't already:

```bash
git init
git add .
git commit -m "Ready for deployment"
gh repo create inventory-management --private --source=. --push
```

(Or create the repo on github.com and `git push` normally.)

---

## 2. Create the database on Aiven

1. Go to https://aiven.io/free-mysql-database and sign up (no card needed).
2. Create a new service → **MySQL** → free plan → pick any region.
3. Once it's running, open the service and copy:
   - **Host**, **Port**, **User**, **Password**, **Database name**
   - The **CA certificate** (download it — you'll need it for TLS).
4. Build your connection string:
   ```
   mysql+pymysql://<user>:<password>@<host>:<port>/<database>?charset=utf8mb4
   ```

---

## 3. Deploy the backend on Render

1. Go to https://render.com → sign up with GitHub.
2. **New → Blueprint** → pick your repo. Render will read `render.yaml` at the repo root automatically.
3. When prompted for environment variables, set:
   - `DATABASE_URL` → the connection string from step 2
   - `CORS_ORIGINS` → leave blank for now, you'll set it after step 4
4. Under the service's **Environment → Secret Files**, add the Aiven CA cert:
   - Filename: `/etc/secrets/aiven-ca.pem`
   - Contents: paste the CA cert you downloaded
   - Then set env var `DB_SSL_CA=/etc/secrets/aiven-ca.pem`
5. Deploy. Render will run `alembic upgrade head` automatically (from `render.yaml`) to create your tables on the new database.
6. Once live, test it: visit `https://<your-service>.onrender.com/healthz` — should return `{"status": "ok", ...}`.

**Free tier note:** the service sleeps after ~15 minutes idle and takes 30–60s to wake on the next request. Hit the URL once before you need it live.

---

## 4. Deploy the frontend on Vercel

1. Go to https://vercel.com → sign up with GitHub → **New Project** → pick your repo.
2. Set **Root Directory** to `frontend`.
3. Framework preset should auto-detect as **Vite**. Leave build command/output as default.
4. Add environment variable:
   - `VITE_API_BASE_URL` → `https://<your-render-service>.onrender.com/api`
5. Deploy. You'll get a URL like `https://inventory-management.vercel.app`.

---

## 5. Close the loop: allow the frontend to call the backend

1. Back in Render, set the `CORS_ORIGINS` env var to your Vercel URL:
   ```
   CORS_ORIGINS=https://inventory-management.vercel.app
   ```
2. Save — Render will redeploy the backend automatically.

---

## 6. Verify

- Open the Vercel URL.
- Load the Dashboard — it should pull real data (empty tables are fine if the new DB has no rows yet).
- Try Import Excel with a real workbook to confirm the full path: frontend → Render → Aiven MySQL.
- If it's a demo/presentation, load the Vercel URL a minute early so the Render backend is already awake.

---

## Rollback / troubleshooting

- **500 errors on load:** check Render logs — usually a missing env var or the CA cert path being wrong.
- **CORS errors in browser console:** `CORS_ORIGINS` on Render doesn't match your exact Vercel URL (must include `https://`, no trailing slash).
- **Tables missing:** confirm `alembic upgrade head` ran during the Render build — check the deploy logs.
- **Local dev unaffected:** none of this touches your `.env` locally; local MySQL/XAMPP setup keeps working as before.
