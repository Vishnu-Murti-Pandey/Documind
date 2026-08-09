# Documind Frontend

Enterprise document chat UI built with Next.js. Users can upload PDF documents, follow ingestion progress, start document-bound conversations, stream grounded answers, inspect citations and figures, and revisit infinite conversation history.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for state ownership, component boundaries, and streaming data flows.
See [DEPLOYMENT.md](./DEPLOYMENT.md) for Vercel production deployment.

## Features

- Streaming chat with stopped, failed, retry, and regenerate states
- Persistent conversation history with cursor-based infinite loading
- Optimistic conversation rename and deletion
- PDF upload with live ingestion progress and cancellation
- Conversation-specific source document binding
- Markdown, code, table, equation, citation, and figure rendering
- Copy response, timestamps, citation accordion, and figure preview
- Responsive sidebar drawer and mobile-safe composer
- Light, dark, and system themes
- Toast action feedback plus page-level critical errors
- Route loading states and error boundaries

## Technology

- Next.js 16 App Router
- React 19 and TypeScript
- Tailwind CSS 4
- Vercel AI Elements and Streamdown
- TanStack Query for server state
- Zustand for small client-side stores
- Base UI/shadcn components
- next-themes and Sonner
- Manrope and Newsreader variable fonts

## Prerequisites

- Node.js 20 or newer
- npm
- The Documind backend running locally

## Local setup

1. Install dependencies:

   ```powershell
   cd frontend
   npm install
   ```

2. Create `.env.local` from the checked-in example:

   ```powershell
   Copy-Item .env.example .env.local
   ```

3. Ensure it points to the backend:

   ```dotenv
   NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
   ```

4. Start the development server:

   ```powershell
   npm run dev
   ```

Open `http://localhost:3000`. The root route redirects to `/chat`.

## Scripts

| Command | Purpose |
| --- | --- |
| `npm run dev` | Start the Next.js development server |
| `npm run build` | Create a production build and run type validation |
| `npm run start` | Serve a previously created production build |
| `npm run lint` | Run ESLint |

## Routes

| Route | Purpose |
| --- | --- |
| `/chat` | Start a new conversation and select an available document |
| `/chat/[conversationId]` | Load a persisted, document-bound conversation |
| `/documents` | Upload, monitor, cancel, inspect, and delete documents |

The dashboard layout supplies the desktop sidebar and mobile drawer. Chat and document routes have dedicated loading and error UI, with `global-error.tsx` as the root fallback.

## Environment configuration

`NEXT_PUBLIC_API_URL` is validated at application startup by `src/lib/env.ts` and must be a valid absolute URL. Because it is a public Next.js variable, never put secrets in it or in any other `NEXT_PUBLIC_*` value.

## Working with the backend

The frontend calls JSON endpoints through `src/lib/api-client.ts`. Chat and ingestion use streaming helpers that parse SSE incrementally.

For local development:

- Frontend: `http://localhost:3000`
- Backend: `http://127.0.0.1:8000`
- Backend OpenAPI: `http://127.0.0.1:8000/docs`

If requests fail in the browser but work directly, confirm the backend CORS origin includes the frontend URL.

## Repository layout

```text
frontend/
├── src/
│   ├── app/                    # App Router pages, layouts, loading, and errors
│   ├── components/
│   │   ├── ai-elements/        # Vercel AI-oriented rendering primitives
│   │   ├── chat/               # Chat history and assistant response composition
│   │   ├── conversations/      # Sidebar, rename, and delete interactions
│   │   ├── documents/          # Upload, selection, progress, and document cards
│   │   ├── layout/             # App shell, sidebar state, and theme controls
│   │   └── ui/                 # Shared Base UI/shadcn primitives
│   ├── features/
│   │   ├── chat/               # Chat API, SSE, types, queries, and cache helpers
│   │   ├── conversations/      # Conversation API, queries, types, and cache helpers
│   │   └── documents/          # Document API, ingestion stream, queries, and store
│   └── lib/                    # Environment, API client, providers, and utilities
├── public/
├── package.json
└── next.config.ts
```

## UI conventions

- Prefer existing components in `components/ui` and `components/ai-elements` before introducing a new primitive.
- Use design tokens and semantic Tailwind colors so light and dark themes remain consistent.
- Interactive controls must have visible hover/focus states and a pointer cursor.
- Use toasts for action feedback; keep progress and blocking errors in the page.
- Existing conversations always display their persisted source document. The document selected on `/documents` only seeds a new chat.
- Code and wide tables scroll horizontally; dialogs and the composer must fit 320 px screens.

## Troubleshooting

- **Environment configuration is invalid:** check that `NEXT_PUBLIC_API_URL` includes `http://` or `https://` and restart the dev server after changing it.
- **System theme appears incorrect:** make sure the root theme provider uses `enableSystem` and no component forces a theme before hydration.
- **Existing conversation says its source is unavailable:** confirm document matching uses the persisted document identity, not only a display name or the current document-page selection.
- **A stream continues after navigation:** navigation should detach the view without corrupting the conversation cache; ingestion cancellation additionally requires the backend cancellation request.
- **Duplicate optimistic user messages:** reconcile streamed/persisted messages by stable ID and keep one cache writer for each conversation.
- **Production build fails in generated AI Elements:** align the AI Elements components with the installed `ai`, `streamdown`, and React package versions; do not suppress TypeScript errors globally.

## Verification checklist

Before merging UI changes:

```powershell
npm run lint
npm run build
```

Also exercise the application at 320, 375, 768, and 1024 px widths, in light/dark/system themes, and with successful, failed, stopped, and unavailable-document conversations.
