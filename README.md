# Energy Dashboard

Suivi temps réel de la consommation électrique, tarification Flextime ENGIE/ORES, et statut BMW.

## Structure

```
energy-dashboard/
├── backend/      FastAPI + collecteurs (P1 Meter, EPEX, BMW) + SQLite
├── frontend/     Next.js PWA (Vercel)
└── cloudflare/   Config tunnel Cloudflare
```

## Démarrage rapide

### Backend (Lenovo X1)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # remplir les variables
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend (local ou Vercel)

```bash
cd frontend
npm install
cp .env.local.example .env.local   # remplir NEXT_PUBLIC_BACKEND_URL
npm run dev
```

### Cloudflare Tunnel

```bash
cd cloudflare
bash install.sh
cp config.yml.example config.yml   # remplir TUNNEL_ID + hostname
sudo cloudflared service install
```

## Variables d'environnement

| Variable | Description |
|---|---|
| `BMW_EMAIL` | Email compte MyBMW |
| `BMW_PASSWORD` | Mot de passe MyBMW |
| `ENTSO_E_TOKEN` | Token API ENTSO-E Transparency Platform |
| `DISCORD_WEBHOOK_URL` | URL webhook Discord pour alertes |
| `P1_METER_IP` | IP locale du HomeWizard P1 Meter |
| `NEXT_PUBLIC_BACKEND_URL` | URL publique du backend (via Cloudflare) |

## Endpoints API

| Endpoint | Description |
|---|---|
| `GET /api/realtime` | Prix actuel, plage, watts en temps réel |
| `GET /api/bmw` | Statut batterie BMW |
| `GET /api/projection` | Coût mois en cours + projection |
| `GET /api/history` | Historique par quart d'heure/heure |
| `GET /api/analytics` | Analytiques : coût/km, répartition, économies |
