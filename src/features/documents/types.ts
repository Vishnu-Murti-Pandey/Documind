export type DocumentStatus = "pending" | "processing" | "completed" | "failed";

export type DocumentItem = {
  id: string;
  paper_name: string;
  original_filename: string;
  status: DocumentStatus;

  file_size_bytes: number;

  elements_count: number | null;
  chunks_count: number | null;

  error_message: string | null;

  created_at: string;
  updated_at: string;
};

export type DocumentListResponse = {
  items: DocumentItem[];

  page: number;
  limit: number;
  total: number;
  has_more: boolean;
};

export type IngestionEventType =
  | "document"
  | "started"
  | "status"
  | "chunk_progress"
  | "completed"
  | "error";

export type IngestionEventData = {
  document_id?: string;
  paper_name?: string;
  filename?: string;

  status?: DocumentStatus | "completed";
  stage?: string;
  message?: string;
  detail?: string;

  progress?: number;

  elements_count?: number;
  chunks_stored?: number;

  current_chunk?: number;
  total_chunks?: number;
  chunk_id?: string;

  elapsed_seconds?: number;
  overwrite?: boolean;
};
