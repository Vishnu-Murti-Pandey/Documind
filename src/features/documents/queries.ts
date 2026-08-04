import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { deleteDocument, getDocuments } from "./api";

export const documentKeys = {
  all: ["documents"] as const,

  list: (page: number, limit: number) =>
    [...documentKeys.all, "list", page, limit] as const,

  detail: (paperName: string) =>
    [...documentKeys.all, "detail", paperName] as const,
};

export function useDocuments(page = 0, limit = 50) {
  return useQuery({
    queryKey: documentKeys.list(page, limit),
    queryFn: () => getDocuments(page, limit),
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: deleteDocument,

    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: documentKeys.all,
      });
    },
  });
}
