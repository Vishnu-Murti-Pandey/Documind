import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  deleteConversation,
  getConversation,
  getConversations,
  renameConversation,
} from "./api";

export const conversationKeys = {
  all: ["conversations"] as const,

  lists: () => [...conversationKeys.all, "list"] as const,

  list: (page: number, limit: number) =>
    [...conversationKeys.lists(), page, limit] as const,

  details: () => [...conversationKeys.all, "detail"] as const,

  detail: (conversationId: string) =>
    [...conversationKeys.details(), conversationId] as const,

  messages: (conversationId: string) =>
    [...conversationKeys.all, conversationId, "messages"] as const,
};

export function useConversations(page = 0, limit = 20) {
  return useQuery({
    queryKey: conversationKeys.list(page, limit),

    queryFn: () =>
      getConversations({
        page,
        limit,
      }),
  });
}

export function useConversation(conversationId?: string) {
  return useQuery({
    queryKey: conversationId
      ? conversationKeys.detail(conversationId)
      : [...conversationKeys.details(), "disabled"],

    queryFn: () => {
      if (!conversationId) {
        throw new Error("Conversation ID is required.");
      }

      return getConversation(conversationId);
    },

    enabled: Boolean(conversationId),
  });
}

export function useRenameConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      conversationId,
      title,
    }: {
      conversationId: string;
      title: string;
    }) =>
      renameConversation(conversationId, {
        title,
      }),

    onSuccess: async (updatedConversation) => {
      queryClient.setQueryData(
        conversationKeys.detail(updatedConversation.conversation_id),
        updatedConversation,
      );

      await queryClient.invalidateQueries({
        queryKey: conversationKeys.lists(),
      });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteConversation,

    onSuccess: async (_, conversationId) => {
      queryClient.removeQueries({
        queryKey: conversationKeys.detail(conversationId),
      });

      await queryClient.invalidateQueries({
        queryKey: conversationKeys.lists(),
      });
    },
  });
}
