"use client";

import { BookOpen, FileText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useConversation } from "@/features/conversations/queries";

type ChatHeaderProps = {
  conversationId?: string;
  fallbackPaperName?: string | null;
};

export function ChatHeader({
  conversationId,
  fallbackPaperName,
}: ChatHeaderProps) {
  const conversationQuery = useConversation(conversationId);

  if (conversationId && conversationQuery.isLoading) {
    return (
      <header className="flex min-h-14 shrink-0 items-center border-b px-5">
        <Skeleton className="h-6 w-60" />
      </header>
    );
  }

  const conversation = conversationQuery.data;

  const title = conversation?.title || "New conversation";

  const paperName = conversation?.paper_name || fallbackPaperName || null;

  return (
    <header className="flex min-h-14 shrink-0 items-center justify-between gap-4 border-b px-5">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 shrink-0" />

          <h1 className="truncate text-sm font-medium">{title}</h1>
        </div>

        {paperName && (
          <p className="mt-0.5 truncate text-xs text-muted-foreground">
            Source: {paperName}
          </p>
        )}
      </div>

      {paperName && (
        <Badge variant="outline" className="hidden max-w-72 gap-1.5 sm:flex">
          <FileText className="h-3.5 w-3.5 shrink-0" />

          <span className="truncate">{paperName}</span>
        </Badge>
      )}
    </header>
  );
}
