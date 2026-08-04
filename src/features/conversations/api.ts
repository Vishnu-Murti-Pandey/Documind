import { apiFetch } from "@/lib/api-client";

import type {
  ConversationDetail,
  ConversationListResponse,
  RenameConversationPayload,
} from "./types";

export type GetConversationsParams = {
  page?: number;
  limit?: number;
};

export async function getConversations({
  page = 0,
  limit = 20,
}: GetConversationsParams = {}): Promise<ConversationListResponse> {
  const searchParams = new URLSearchParams({
    page: String(page),
    limit: String(limit),
  });

  return apiFetch<ConversationListResponse>(
    `/api/conversations?${searchParams.toString()}`,
  );
}

export async function getConversation(
  conversationId: string,
): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>(
    `/api/conversations/${encodeURIComponent(conversationId)}`,
  );
}

export async function renameConversation(
  conversationId: string,
  payload: RenameConversationPayload,
): Promise<ConversationDetail> {
  return apiFetch<ConversationDetail>(
    `/api/conversations/${encodeURIComponent(conversationId)}`,
    {
      method: "PATCH",
      body: payload,
    },
  );
}

export async function deleteConversation(
  conversationId: string,
): Promise<void> {
  return apiFetch<void>(
    `/api/conversations/${encodeURIComponent(conversationId)}`,
    {
      method: "DELETE",
    },
  );
}
