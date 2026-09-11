# Deploying TrackShift

You already have a partial deployment in place — `frontend/.env` points at
`https://trackshift-oirc.onrender.com/`, meaning a backend was deployed to
Render before this update. That deployment is still running the **old**
backend and doesn't know about `/tyre-intel/*` yet. The steps below cover
both "update what's already there" and "set it up from scratch" in case you
need to redo it.

Two paths:

- **Path A — Update the existing Render + Vercel/Netlify deployment.**
  Fastest if you already have accounts set up (~5 minutes).
- **Path B — Fresh setup from scratch.** Full walkthrough if Path A doesn't
  apply to you, or as a backup on a different account.
- **Path C — ngrok tunnel.** 2-minute temporary public URL from your own
  laptop, good as a live backup on demo day.

---

## Path A: Update the existing deployment

### 1. Push this updated code to GitHub

```bash
cd trackshift
git add .
git commit -m "Add Tyre Intelligence module"
git push
```

If this folder isn't already a git repo connected to your GitHub remote:
```bash
git init
git remote add origin https://github.com/<your-username>/TRACKSHIFT.git
git add .
git commit -m "Add Tyre Intelligence module"
git branch -M main
git push -u origin main --force   # only if the remote history diverged
```

### 2. Redeploy the backend on Render

- Go to your Render dashboard → the `trackshift` (or similarly named) web
  service.
- If **Auto-Deploy** is on, pushing to GitHub already triggered a rebuild —
  check the **Logs** tab for `Application startup complete`.
- If not, click **Manual Deploy → Deploy latest commit**.
- Confirm the new routes are live:
  `https://trackshift-oirc.onrender.com/tyre-intel/meta` should return JSON
  (not a 404). Give it ~60 seconds if the service was asleep (Render free
  tier spins down after 15 minutes idle).

### 3. Redeploy the frontend

- Vercel/Netlify auto-deploys on push by default — check your dashboard for
  a new deployment matching your latest commit.
- No environment variable changes needed; `.env`'s `VITE_API_BASE` already
  points at the right backend URL.

### 4. Verify

Open your deployed frontend URL and click through: Overview, Tyre
Intelligence, Degradation Analysis, Lap Forensics, Strategy Simulator, Race
Engineer, and the **Race Ops ▾** dropdown pages. If anything shows "API
OFFLINE" in the nav, the backend redeploy either hasn't finished or failed —
check Render's logs.

---

## Path B: Fresh setup from scratch

Use this if you're setting up new Render/Vercel accounts, or the existing
services were deleted.

### Step 1 — GitHub

Same as Path A step 1 — get the code pushed to a GitHub repo.

### Step 2 — Backend on Render

1. Go to https://render.com → sign up (GitHub sign-in is fastest).
2. **New +** → **Web Service** → connect your GitHub repo.
3. Settings:
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free
4. **Create Web Service**. Wait for `Application startup complete` in the
   logs (1–3 minutes).
5. Test: open `<your-render-url>/tyre-intel/meta` and `/docs` (Swagger UI).

**Free-tier note:** spins down after ~15 min idle, ~30–60s cold-start on the
next request. Hit the URL once before a live demo to warm it up.

### Step 3 — Point the frontend at the backend

Edit `frontend/.env`:
```
VITE_API_BASE=https://<your-render-url>
```
Commit and push.

### Step 4 — Frontend on Vercel

1. https://vercel.com → sign up → **Add New… → Project** → import your repo.
2. **Root Directory**: `frontend` (click Edit to set this)
3. Framework Preset: Vite (auto-detected) — leave build command/output dir
   at their defaults (`npm run build` / `dist`).
4. **Environment Variables** → add `VITE_API_BASE` = your Render URL (this
   overrides `.env` at build time, which is the more standard approach).
5. **Deploy**.

`frontend/vercel.json` is already configured with the SPA rewrite rule
needed for React Router to survive a page refresh on `/tyre-intelligence`,
`/lap-forensics`, etc. — nothing else to configure there.

### Step 5 — Lock down CORS (optional, recommended)

In Render → your backend service → **Environment**, add:
```
ALLOWED_ORIGINS = https://<your-vercel-url>
```
(comma-separate multiple origins if you have more than one). Render
redeploys automatically when you save.

---

## Path C: ngrok (fast, temporary, good as a live backup)

1. Install ngrok, sign up free, run `ngrok config add-authtoken <token>`.
2. Run the backend locally:
   ```bash
   cd backend && uvicorn main:app --port 8000
   ```
3. Tunnel it: `ngrok http 8000` → copy the printed URL.
4. Point the frontend at it — edit `frontend/.env`:
   ```
   VITE_API_BASE=https://<your-ngrok-url>
   ```
   restart `npm run dev` (Vite reads `.env` at startup only).
5. Tunnel the frontend too so judges can open it on their own device:
   `ngrok http 5173`.

Free-plan ngrok URLs expire after a few hours or when you close the tunnel —
re-run right before your demo slot.

---

## Alternative hosts

- **Backend**: Railway (railway.app), Fly.io (fly.io), or any VM running
  `uvicorn main:app --host 0.0.0.0` behind `systemd`/`pm2`.
- **Frontend**: Netlify — `frontend/netlify.toml` is already configured;
  "Import from Git" → base directory `frontend` → add the same
  `VITE_API_BASE` env var in Netlify's site settings.

---

## Troubleshooting

- **"API OFFLINE" banner** → backend asleep (wait ~60s, Render free tier) or
  `VITE_API_BASE` wrong. Check the Network tab for the actual failing URL.
- **Blank page** → open the browser console. The app now has an error
  boundary (`ErrorBoundary.jsx`) that shows a readable error box instead of
  a silent blank screen — read what it says.
- **404 on refresh at `/lap-forensics` etc.** → the SPA rewrite rule isn't
  active on your host. Confirm `vercel.json` / `netlify.toml` made it into
  the deployed build.
- **CORS errors in console** → `ALLOWED_ORIGINS` on Render doesn't exactly
  match your frontend URL (needs `https://`, no trailing slash).
- **`/tyre-intel/*` routes 404 but root `/` works** → the backend redeploy
  didn't pick up the new code. Check Render's deploy logs for the actual
  commit hash it built from.
