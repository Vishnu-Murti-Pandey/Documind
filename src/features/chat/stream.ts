import { env } from "@/lib/env";
import { extractSseEvents, type ParsedSseEvent } from "@/lib/sse-parser";

import type {
  ChatMetadata,
  ChatRequestPayload,
  ChatStreamStatus,
} from "./types";

type ConversationEvent = {
  conversation_id: string;
  is_new: boolean;
};

type TokenEvent = {
  content: string;
};

type DoneEvent = {
  status: "completed" | "failed";
  conversation_id: string;
};

type ErrorEvent = {
  message: string;
  conversation_id?: string;
};

export type ChatStreamHandlers = {
  onConversation?: (data: ConversationEvent) => void;

  onStatus?: (data: ChatStreamStatus) => void;

  onToken?: (content: string) => void;

  onMetadata?: (data: ChatMetadata) => void;

  onDone?: (data: DoneEvent) => void;

  onError?: (error: Error) => void;
};

function getErrorMessage(body: unknown): string {
  if (
    typeof body === "object" &&
    body !== null &&
    "detail" in body &&
    typeof body.detail === "string"
  ) {
    return body.detail;
  }

  return "Chat request failed.";
}

export async function streamChat(
  payload: ChatRequestPayload,
  handlers: ChatStreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${env.NEXT_PUBLIC_API_URL}/api/chat/stream`, {
    method: "POST",
    headers: {
      Accept: "text/event-stream",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    let body: unknown;

    try {
      body = await response.json();
    } catch {
      body = await response.text();
    }

    throw new Error(getErrorMessage(body));
  }

  if (!response.body) {
    throw new Error("Streaming response body is unavailable.");
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
        handleSseEvent(event, handlers);
      }
    }
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      return;
    }

    const normalizedError =
      error instanceof Error ? error : new Error("Unknown streaming error.");

    handlers.onError?.(normalizedError);

    throw normalizedError;
  } finally {
    reader.releaseLock();
  }
}

function handleSseEvent(
  event: ParsedSseEvent,
  handlers: ChatStreamHandlers,
): void {
  switch (event.event) {
    case "conversation": {
      handlers.onConversation?.(event.data as ConversationEvent);
      break;
    }

    case "status": {
      handlers.onStatus?.(event.data as ChatStreamStatus);
      break;
    }

    case "token": {
      const data = event.data as TokenEvent;

      handlers.onToken?.(data.content ?? "");
      break;
    }

    case "metadata": {
      handlers.onMetadata?.(event.data as ChatMetadata);
      break;
    }

    case "done": {
      handlers.onDone?.(event.data as DoneEvent);
      break;
    }

    case "error": {
      const data = event.data as ErrorEvent;

      handlers.onError?.(new Error(data.message || "Chat request failed."));
      break;
    }

    default:
      break;
  }
}
