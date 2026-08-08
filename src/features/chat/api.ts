import { apiFetch } from "@/lib/api-client";

import type { ChatMessage, ConversationMessagesResponse } from "./types";

export async function getConversationMessages(
  conversationId: string,
  cursor?: string | null,
  limit = 20,
): Promise<ConversationMessagesResponse> {
  const searchParams = new URLSearchParams({
    limit: String(limit),
  });

  if (cursor) {
    searchParams.set("cursor", cursor);
  }

  return apiFetch<ConversationMessagesResponse>(
    `/api/conversations/${encodeURIComponent(
      conversationId,
    )}/messages?${searchParams.toString()}`,
  );
}

export function mapPersistedMessages(
  response: ConversationMessagesResponse,
): ChatMessage[] {
  return response.messages.flatMap((message): ChatMessage[] => {
    if (message.role !== "user" && message.role !== "assistant") {
      return [];
    }

    return [
      {
        id: message.id,
        role: message.role,
        content: message.content,
        citations: message.citations ?? [],
        figures: message.figures ?? [],
        tables: message.tables ?? [],
        created_at: message.created_at,
        status: "completed",
      },
    ];
  });
}
