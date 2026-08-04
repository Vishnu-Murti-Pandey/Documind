import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  deleteConversation,
  getConversations,
  renameConversation,
} from "./api";

export const conversationKeys = {
  all: ["conversations"] as const,

  list: (page: number, limit: number) =>
    [...conversationKeys.all, "list", page, limit] as const,

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

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: conversationKeys.all,
      });
    },
  });
}

export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteConversation,

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: conversationKeys.all,
      });
    },
  });
}
