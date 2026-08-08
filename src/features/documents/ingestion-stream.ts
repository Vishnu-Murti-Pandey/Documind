import { env } from "@/lib/env";
import { extractSseEvents } from "@/lib/sse-parser";

import type { IngestionEventData, IngestionEventType } from "./types";

export type IngestionStreamHandlers = {
  onEvent?: (eventType: IngestionEventType, data: IngestionEventData) => void;

  onError?: (error: Error) => void;
};

export async function cancelDocumentIngestion(
  documentId: string,
): Promise<void> {
  const response = await fetch(
    `${env.NEXT_PUBLIC_API_URL}/api/ingestion/${encodeURIComponent(documentId)}/cancel`,
    { method: "POST" },
  );

  if (!response.ok && response.status !== 404) {
    throw new Error("Could not stop document ingestion.");
  }
}

function extractErrorMessage(body: unknown): string {
  if (
    typeof body === "object" &&
    body !== null &&
    "detail" in body &&
    typeof body.detail === "string"
  ) {
    return body.detail;
  }

  if (typeof body === "string") {
    return body;
  }

  return "Document ingestion failed.";
}

export async function streamDocumentIngestion(
  file: File,
  handlers: IngestionStreamHandlers,
  options?: {
    overwrite?: boolean;
    signal?: AbortSignal;
  },
): Promise<void> {
  const formData = new FormData();

  formData.append("file", file);

  const overwrite = options?.overwrite ?? false;

  const searchParams = new URLSearchParams({
    overwrite: String(overwrite),
  });

  const response = await fetch(
    `${env.NEXT_PUBLIC_API_URL}/api/ingestion/stream?${searchParams.toString()}`,
    {
      method: "POST",
      body: formData,
      headers: {
        Accept: "text/event-stream",
      },
      signal: options?.signal,
    },
  );

  if (!response.ok) {
    let body: unknown;

    try {
      body = await response.json();
    } catch {
      body = await response.text();
    }

    throw new Error(extractErrorMessage(body));
  }

  if (!response.body) {
    throw new Error("Ingestion response stream is unavailable.");
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();

  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();

      if (done) {
        break;
      }

      buffer += value;

      const parsed = extractSseEvents(buffer);

      buffer = parsed.remainingBuffer;

      for (const event of parsed.events) {
        const eventType = event.event as IngestionEventType;

        const data = event.data as IngestionEventData;

        handlers.onEvent?.(eventType, data);

        if (eventType === "error") {
          const error = new Error(
            data.detail || data.message || "Document ingestion failed.",
          );

          handlers.onError?.(error);
        }
      }
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw error;
    }

    const normalizedError =
      error instanceof Error ? error : new Error("Unknown ingestion error.");

    handlers.onError?.(normalizedError);

    throw normalizedError;
  } finally {
    reader.releaseLock();
  }
}
