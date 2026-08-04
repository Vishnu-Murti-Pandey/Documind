import { apiFetch } from "@/lib/api-client";

import type { DocumentItem, DocumentListResponse } from "./types";

export async function getDocuments(
  page = 0,
  limit = 50,
): Promise<DocumentListResponse> {
  const searchParams = new URLSearchParams({
    page: String(page),
    limit: String(limit),
  });

  return apiFetch<DocumentListResponse>(
    `/api/documents?${searchParams.toString()}`,
  );
}

export async function getDocument(paperName: string): Promise<DocumentItem> {
  return apiFetch<DocumentItem>(
    `/api/documents/${encodeURIComponent(paperName)}`,
  );
}

export async function deleteDocument(paperName: string): Promise<void> {
  return apiFetch<void>(`/api/documents/${encodeURIComponent(paperName)}`, {
    method: "DELETE",
  });
}
