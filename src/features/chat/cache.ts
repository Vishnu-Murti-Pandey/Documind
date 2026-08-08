import type { InfiniteData, QueryClient } from "@tanstack/react-query";

import { chatMessageKeys } from "./queries";
import type { ChatMessage, ConversationMessagesResponse } from "./types";

export function cacheOptimisticUserMessage({
  queryClient,
  conversationId,
  message,
  paperName,
}: {
  queryClient: QueryClient;
  conversationId: string;
  message: ChatMessage;
  paperName: string | null;
}): void {
  const queryKey = chatMessageKeys.conversation(conversationId);

  queryClient.setQueryData<
    InfiniteData<ConversationMessagesResponse, string | null>
  >(queryKey, (current) => {
    const optimisticMessage = {
      id: message.id,
      role: message.role,
      content: message.content,
      citations: message.citations,
      figures: message.figures,
      tables: message.tables,
      created_at: message.created_at ?? new Date().toISOString(),
    };

    if (!current) {
      return {
        pages: [
          {
            conversation_id: conversationId,
            title: null,
            paper_name: paperName,
            messages: [optimisticMessage],
            next_cursor: null,
            has_more: false,
          },
        ],
        pageParams: [null],
      };
    }

    if (
      current.pages.some((page) =>
        page.messages.some((item) => item.id === message.id),
      )
    ) {
      return current;
    }

    return {
      ...current,
      pages: current.pages.map((page, index) =>
        index === 0
          ? { ...page, messages: [...page.messages, optimisticMessage] }
          : page,
      ),
    };
  });
}
