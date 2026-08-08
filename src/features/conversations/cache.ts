import type { QueryClient } from "@tanstack/react-query";

import { conversationKeys } from "./queries";
import type { ConversationItem, ConversationListResponse } from "./types";

type AddOptimisticConversationArgs = {
  queryClient: QueryClient;
  conversationId: string;
  title: string;
  paperName: string | null;
};

export function addOptimisticConversation({
  queryClient,
  conversationId,
  title,
  paperName,
}: AddOptimisticConversationArgs): void {
  queryClient.setQueriesData<ConversationListResponse>(
    {
      queryKey: conversationKeys.lists(),
    },
    (current) => {
      if (!current) {
        return current;
      }

      const alreadyExists = current.items.some(
        (conversation) => conversation.conversation_id === conversationId,
      );

      if (alreadyExists) {
        return current;
      }

      const now = new Date().toISOString();

      const optimisticConversation: ConversationItem = {
        conversation_id: conversationId,

        title: title.trim().slice(0, 80) || "New conversation",

        paper_name: paperName,

        created_at: now,
        updated_at: now,
      };

      return {
        ...current,

        items: [optimisticConversation, ...current.items],

        total: current.total + 1,
      };
    },
  );
}
