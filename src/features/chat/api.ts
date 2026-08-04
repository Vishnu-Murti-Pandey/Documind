import { apiFetch } from "@/lib/api-client";

import type { ChatMessage, ConversationMessagesResponse } from "./types";

export async function getConversationMessages(
  conversationId: string,
  page = 0,
  limit = 100,
): Promise<ConversationMessagesResponse> {
  const searchParams = new URLSearchParams({
    page: String(page),
    limit: String(limit),
  });

  return apiFetch<ConversationMessagesResponse>(
    `/api/conversations/${encodeURIComponent(
      conversationId,
    )}/messages?${searchParams.toString()}`,
  );
}

export function mapPersistedMessages(
  response: ConversationMessagesResponse,
): ChatMessage[] {
  return response.messages.map((message) => ({
    id: message.id,
    role: message.role,
    content: message.content,
    citations: message.citations ?? [],
    figures: message.figures ?? [],
    tables: message.tables ?? [],
    createdAt: message.created_at,
    status: "completed",
  }));
}
