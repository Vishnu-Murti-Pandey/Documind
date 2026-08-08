"use client";

import { FileText, LockKeyhole } from "lucide-react";

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

  const paperName = conversationId
    ? conversation?.paper_name ?? null
    : fallbackPaperName || null;

  return (
    <header className="flex min-h-16 shrink-0 items-center justify-between gap-4 border-b border-border/60 bg-background/80 px-5 backdrop-blur-xl sm:px-7">
      <div className="min-w-0">
        <div className="flex items-center gap-2">
          <h1 className="truncate text-[14px] font-semibold tracking-[-0.02em]">{title}</h1>
        </div>

        {paperName && (
          <p className="mt-0.5 truncate text-[11px] text-muted-foreground">
            Source: {paperName}
          </p>
        )}
      </div>

      {paperName && (
        <Badge variant="secondary" className="hidden max-w-72 gap-1.5 rounded-full border-0 bg-muted/80 px-3 py-1.5 font-medium sm:flex">
          <FileText className="h-3.5 w-3.5 shrink-0" />

          <span className="truncate">{paperName}</span>
          <LockKeyhole className="ml-1 size-3 text-muted-foreground" />
        </Badge>
      )}
    </header>
  );
}
