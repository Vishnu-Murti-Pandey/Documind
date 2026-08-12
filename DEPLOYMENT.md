# Production Deployment

This guide runs the complete FastAPI and multimodal PDF pipeline on an Oracle
Cloud Always Free Ampere A1 VM. Durable data remains in Neon PostgreSQL,
Qdrant Cloud, and Cloudflare R2; the Next.js application remains on Vercel.

## Architecture

```mermaid
flowchart LR
    Browser --> Vercel[Next.js on Vercel]
    Vercel --> Caddy[Caddy HTTPS on Oracle]
    Caddy --> API[FastAPI container]
    API --> Neon[(Neon PostgreSQL)]
    API --> Qdrant[(Qdrant Cloud)]
    API --> R2[(Cloudflare R2)]
    API --> OpenAI[OpenAI APIs]
```

## 0. Rotate exposed credentials

Rotate any Neon password, R2 access key, Qdrant API key, or OpenAI key that was
ever committed or copied into a tracked example file. Put only placeholders in
Git. Production secrets belong only in the VM's untracked `.env.production`.

## 1. Create the Oracle VM

1. Create an Oracle Cloud account and choose the home region carefully.
2. Create an `VM.Standard.A1.Flex` Always Free instance with Ubuntu 24.04.
3. Allocate the full Always Free allowance: 2 OCPUs and 12 GB RAM.
4. Add an SSH public key and download/save the corresponding private key.
5. Reserve the instance's public IP so it does not change.
6. In the subnet security list or network security group, allow inbound TCP
   ports 22, 80, and 443. Do not expose the application port directly.

The A1 shape is ARM64. Build the image on this VM so Docker selects ARM64
packages. Do not pull an x86-only image built elsewhere.

## 2. Install Docker

SSH into the instance and install Docker from Docker's official Ubuntu
repository. Add the Ubuntu user to the `docker` group, then sign out and back
in so the new group applies. Verify with:

```bash
docker version
docker compose version
```

## 3. Copy the backend and configure secrets

Clone the backend branch/repository on the VM, then enter its directory:

```bash
git clone --branch backend BACKEND_GIT_URL documind-backend
cd documind-backend
cp .env.production.example .env.production
chmod 600 .env.production
```

Edit `.env.production` and set every provider credential. In particular:

```dotenv
ENVIRONMENT=production
DEBUG=false
LOW_MEMORY_MODE=false
ALLOWED_ORIGINS=https://documind-labs.vercel.app
DATABASE_URL=postgresql://USER:PASSWORD@NEON_POOLED_HOST/DATABASE?sslmode=require
MINIO_ENDPOINT=ACCOUNT_ID.r2.cloudflarestorage.com
MINIO_ACCESS_KEY=R2_ACCESS_KEY_ID
MINIO_SECRET_KEY=R2_SECRET_ACCESS_KEY
MINIO_BUCKET=documind-documents
MINIO_SECURE=true
MINIO_REGION=auto
QDRANT_URL=https://YOUR_CLUSTER.cloud.qdrant.io:6333
QDRANT_API_KEY=QDRANT_DATABASE_API_KEY
OPENAI_API_KEY=OPENAI_API_KEY
HF_TOKEN=HUGGING_FACE_TOKEN
```

`LOW_MEMORY_MODE=false` preserves the complete ingestion and retrieval
pipeline.

## 4. Build and run FastAPI

Build locally on the ARM VM and run with a restart policy:

```bash
docker build -t documind-api:latest .
docker run -d --name documind-api --restart unless-stopped \
  --env-file .env.production \
  -p 127.0.0.1:10000:10000 \
  documind-api:latest
```

Check startup and health:

```bash
docker logs -f documind-api
curl http://127.0.0.1:10000/api/health
curl http://127.0.0.1:10000/api/health/database
```

Binding to `127.0.0.1` ensures only the HTTPS reverse proxy can reach Uvicorn.

## 5. Add HTTPS with Caddy

Point a DNS record such as `api.example.com` to the VM's reserved public IP.
Install Caddy and create `/etc/caddy/Caddyfile`:

```caddyfile
api.example.com {
    reverse_proxy 127.0.0.1:10000
}
```

Then validate and restart it:

```bash
sudo caddy validate --config /etc/caddy/Caddyfile
sudo systemctl restart caddy
sudo systemctl status caddy
```

Caddy obtains and renews the TLS certificate automatically. Test:

```bash
curl https://api.example.com/api/health
```

## 6. Connect Vercel

1. In Vercel, open the frontend project and go to Settings > Environment
   Variables.
2. Replace `NEXT_PUBLIC_API_URL` with `https://api.example.com`, without a
   trailing slash.
3. Apply it to Production and any desired Preview environments.
4. Redeploy the frontend because `NEXT_PUBLIC_API_URL` is embedded at build
   time.
5. Keep the exact Vercel URL in the backend's `ALLOWED_ORIGINS`. After changing
   the backend environment file, recreate the container.

## 7. Updating the backend

```bash
git pull --ff-only
docker build -t documind-api:latest .
docker rm -f documind-api
docker run -d --name documind-api --restart unless-stopped \
  --env-file .env.production \
  -p 127.0.0.1:10000:10000 \
  documind-api:latest
```

Removing this application container does not remove data in Neon, Qdrant, or
R2.

## Release verification

- Both health endpoints return success over HTTPS.
- The browser reports no CORS or mixed-content errors.
- A PDF completes ingestion with text, tables, and images enabled.
- Qdrant receives points and R2 receives documents and extracted assets.
- A chat streams tokens, retrieves evidence, and persists messages in Neon.
- A cited figure opens through the backend's R2 presigned redirect.
- Reboot the VM once and confirm the container and Caddy return automatically.
