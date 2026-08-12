# Vercel Deployment

Deploy the Next.js frontend after FastAPI has a stable HTTPS URL on Oracle Cloud.

## Deploy

1. Push the frontend repository to a Git provider.
2. Import it as a Vercel project.
3. If frontend and backend share one repository, set the Vercel Root Directory
   to `frontend`. If they are separate repositories, keep the repository root.
4. Let Vercel detect Next.js and run `npm run build`.
5. Add this variable to Production and to any Preview environment that should
   use the production API:

   ```dotenv
   NEXT_PUBLIC_API_URL=https://api.example.com
   ```

6. Deploy, copy the final Vercel origin into the backend's `ALLOWED_ORIGINS`,
   and restart the backend container on Oracle.

`NEXT_PUBLIC_API_URL` is embedded during the Next.js build, so changing it
requires a new Vercel deployment.

## Verify

1. Open `/documents` and confirm its list loads from Oracle.
2. Upload a small PDF and follow ingestion to completion.
3. Start a chat and verify streaming tokens arrive without buffering.
4. Open a cited figure and verify the backend route redirects to R2.
5. Refresh a conversation and confirm messages load from Neon.
6. Test only production and preview origins explicitly permitted by CORS.

Keep secrets out of `NEXT_PUBLIC_*`, configure the custom domain before
finalizing CORS, and enable deployment protection for private previews.

Managed backend service instructions are in `backend/DEPLOYMENT.md`.
