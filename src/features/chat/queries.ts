import { useInfiniteQuery } from "@tanstack/react-query";

import { getConversationMessages } from "./api";

export const chatMessageKeys = {
  all: ["chat-messages"] as const,

  conversation: (conversationId: string) =>
    [...chatMessageKeys.all, conversationId] as const,
};

export function useInfiniteConversationMessages(conversationId?: string) {
  return useInfiniteQuery({
    queryKey: conversationId
      ? chatMessageKeys.conversation(conversationId)
      : [...chatMessageKeys.all, "disabled"],

    enabled: Boolean(conversationId),

    // A conversation can receive messages while its route is not mounted.
    // Always reconcile optimistic/cache state when the user opens it again.
    refetchOnMount: "always",

    initialPageParam: null as string | null,

    queryFn: ({ pageParam }) =>
      getConversationMessages(conversationId as string, pageParam, 20),

    getNextPageParam: (lastPage) =>
      lastPage.has_more ? lastPage.next_cursor : undefined,
  });
}
