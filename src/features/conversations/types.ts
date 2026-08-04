export type ConversationItem = {
  conversation_id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
};

export type ConversationListResponse = {
  items: ConversationItem[];
  page: number;
  limit: number;
  total: number;
  has_more: boolean;
};

export type ConversationDetail = {
  conversation_id: string;
  title: string | null;
  summary: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type RenameConversationPayload = {
  title: string;
};
