export type ChatRole = "user" | "assistant" | "system";

export type Citation = {
  type: "section" | "figure";
  chunk_id: string;
  paper_name: string;
  section_title: string;
  page_start: number;
  page_end: number;
  caption?: string | null;
  storage?: {
    provider: string;
    bucket: string;
    object_name: string;
  } | null;
};

export type FigureReference = {
  score: number;
  chunk_id: string;
  paper_name: string;
  section_title: string;
  page_start: number;
  page_end: number;
  caption?: string | null;
  description?: string | null;
  image_url: string;
};

export type TableReference = {
  score: number;
  chunk_id: string;
  paper_name: string;
  section_title: string;
  page_start: number;
  page_end: number;
  summary?: string | null;
  html: string;
};

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;

  citations: Citation[];
  figures: FigureReference[];
  tables: TableReference[];

  createdAt?: string;

  status?: "pending" | "streaming" | "completed" | "failed";
};

export type ChatStreamStatus = {
  stage:
    | "memory"
    | "embedding"
    | "retrieval"
    | "reranking"
    | "context"
    | "generation"
    | "saving"
    | string;

  message: string;
};

export type ChatRequestPayload = {
  message: string;
  conversation_id?: string;
  filter?: {
    paper_name?: string;
    section_title?: string;
    page_start?: number;
    page_end?: number;
  } | null;
};

export type ChatMetadata = {
  citations: Citation[];
  figures: FigureReference[];
  tables: TableReference[];
};

export type ConversationMessagesResponse = {
  conversation_id: string;
  title: string | null;

  messages: Array<{
    id: string;
    role: ChatRole;
    content: string;
    citations: Citation[];
    figures: FigureReference[];
    tables: TableReference[];
    created_at: string;
  }>;

  page: number;
  limit: number;
  total: number;
  has_more: boolean;
};
