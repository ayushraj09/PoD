# Deploy the backend on a Hostinger VPS

The backend runs in Docker behind [Caddy](https://caddyserver.com), which gets and renews an HTTPS
certificate automatically. HTTPS is required: the widget runs on `https://…vercel.app`, and browsers
block calls from an HTTPS page to an HTTP API.

Files used: `backend/deploy/docker-compose.yml`, `backend/deploy/Caddyfile`, `backend/deploy/update.sh`.

> Needs a Hostinger **VPS** (KVM). Shared web hosting can't run Docker.

## 0. Check the server has room

```bash
ssh root@<server-ip> 'nproc; free -h; df -h /'
```

Measured for this backend (Docker, linux/amd64):

| Resource | Needed | Why |
|---|---|---|
| RAM | **≥ 2 GB total, ≥ 1.2 GB free** | 534 MB at idle (PyTorch 280 MB + voice model), up to ~700 MB while scoring a signup, plus Caddy (~30 MB). Two signups at once can reach ~900 MB. |
| Disk | **≥ 8 GB free** | image ~2 GB, plus build cache during `--build` |
| CPU | 1 vCPU works; 2 is better | one signup takes ~1 s of model time on a real core |

If RAM is short, add swap (`fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile`), but don't rely on it for speed.

## 1. Pick the API hostname

Either a subdomain you own, e.g. `api.yourdomain.com` with an **A record** pointing to the server IP,
or, with no domain, the free wildcard DNS name `<ip-with-dashes>.sslip.io`
(for `187.127.153.250` that is `187-127-153-250.sslip.io`, which already resolves to the IP).

## 2. Install Docker (once)

```bash
ssh root@<server-ip>
curl -fsSL https://get.docker.com | sh
apt-get install -y git
```

Open ports 80 and 443: in hPanel → VPS → **Firewall** (if enabled) and on the server
(`ufw allow 80,443/tcp` if ufw is active). Keep 22 open.

## 3. Get the code and settings

```bash
git clone https://github.com/ayushraj09/PoD.git ~/PoD
```

From your laptop, copy the backend settings (never commit this file):

```bash
scp backend/.env root@<server-ip>:~/PoD/backend/.env
```

Then on the server, check `WEB_ORIGIN` in that file includes the Vercel URL, e.g.
`WEB_ORIGIN=https://po-d-indol.vercel.app,http://localhost:3000`, and set the hostname for Caddy:

```bash
echo "API_DOMAIN=187-127-153-250.sslip.io" > ~/PoD/backend/deploy/.env
```

## 4. Start it

```bash
cd ~/PoD/backend/deploy
docker compose up -d --build        # first build ~5-10 min (PyTorch)
docker compose logs -f              # wait for "Application startup complete" and Caddy's certificate
curl https://187-127-153-250.sslip.io/health   # {"ok":true,"models_loaded":true}
```

Both containers restart automatically after a crash or a server reboot.

## 5. Point the web app at it

In Vercel → Settings → Environment Variables set
`NEXT_PUBLIC_BACKEND_URL=https://187-127-153-250.sslip.io`, then **redeploy** (it's baked in at build).
Suspend the old Render service so nothing talks to two backends.

## Updating after a push

```bash
ssh root@<server-ip> ~/PoD/backend/deploy/update.sh
```

It pulls `main`, rebuilds, restarts and prints the health check.

## Troubleshooting

| Symptom | Check |
|---|---|
| `/health` hangs or 502 | `docker compose ps` (backend `healthy`?), `docker compose logs backend` |
| No certificate | DNS points at the server? ports 80/443 open in hPanel firewall? `docker compose logs caddy` |
| Widget: "Couldn't reach the server" | CORS: startup log line `CORS allowed origins: [...]` must include the Vercel URL |
| Out of memory | `docker stats`; see section 0 |

## Security notes

- The backend container is not published on any port; only Caddy (80/443) is.
- Caddy strips `True-Client-IP` / `CF-Connecting-IP` from visitors, so the rate limit and
  repeat-network check can't be dodged with fake headers (tested: four requests with different
  fake headers all got the same IP hash).
- `backend/.env` and `backend/deploy/.env` are gitignored; keep them only on the server.
