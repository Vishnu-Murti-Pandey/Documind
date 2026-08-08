"use client";

import { Check, Copy, LoaderCircle, RefreshCw, RotateCcw, TriangleAlert } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { MessageAction, MessageActions, MessageResponse } from "@/components/ai-elements/message";
import { CitationAccordion } from "@/components/chat/citation-accordion";
import { FigureGallery } from "@/components/chat/figure-gallery";
import { TableGallery } from "@/components/chat/table-gallery";
import type { ChatMessage } from "@/features/chat/types";

export function AnswerContent({ message }: { message: ChatMessage }) {
  return (
    <>
      <MessageResponse>{message.content}</MessageResponse>
      {message.status === "streaming" && !message.content && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <LoaderCircle className="h-4 w-4 animate-spin" /> Preparing response...
        </div>
      )}
      {message.status === "stopped" && (
        <div className="mt-3 flex w-fit max-w-full items-start gap-3 rounded-2xl border border-border/70 bg-muted/45 px-4 py-3 text-sm shadow-sm sm:max-w-lg">
          <RotateCcw className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          <div className="min-w-0"><p className="font-semibold text-foreground">Generation stopped</p><p className="mt-0.5 leading-5 text-muted-foreground">The response was interrupted. You can retry when you are ready.</p></div>
        </div>
      )}
      {message.status === "failed" && (
        <div className="mt-3 flex w-fit max-w-full items-start gap-3 rounded-2xl border border-destructive/20 bg-destructive/8 px-4 py-3 text-sm shadow-sm sm:max-w-lg">
          <TriangleAlert className="mt-0.5 size-4 shrink-0 text-destructive" />
          <div className="min-w-0"><p className="font-semibold text-destructive">Response not generated</p><p className="mt-0.5 leading-5 text-muted-foreground">Something prevented DocuMind from completing this answer. Retry the response or submit the question again.</p></div>
        </div>
      )}
    </>
  );
}

function AssistantMessageActions({ message, onRetry }: { message: ChatMessage; onRetry?: (prompt: string) => void }) {
  const [copied, setCopied] = useState(false);
  const canRetry = Boolean(message.retryPrompt) && message.status !== "streaming";
  const timestamp = message.created_at ? new Date(message.created_at) : null;

  async function copyResponse() {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      toast.success("Response copied");
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      toast.error("Could not copy response");
    }
  }

  return (
    <MessageActions className="mt-2 border-t border-border/50 pt-2 opacity-65 transition-opacity hover:opacity-100 focus-within:opacity-100">
      <time suppressHydrationWarning dateTime={message.created_at} className="mr-1 text-[10px] font-medium tracking-wide text-muted-foreground">
        {timestamp ? timestamp.toLocaleString([], { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) : "Just now"}
      </time>
      <MessageAction tooltip="Copy response" onClick={() => void copyResponse()} disabled={!message.content}>
        {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
      </MessageAction>
      {canRetry && (
        <MessageAction tooltip={message.status === "completed" ? "Regenerate response" : "Retry response"} onClick={() => onRetry?.(message.retryPrompt!)}>
          <RefreshCw className="h-4 w-4" />
        </MessageAction>
      )}
    </MessageActions>
  );
}

export function AssistantMessage({ message, onRetry }: { message: ChatMessage; onRetry?: (prompt: string) => void }) {
  return (
    <>
      <AnswerContent message={message} />
      <AssistantMessageActions message={message} onRetry={onRetry} />
      <CitationAccordion citations={message.citations} figures={message.figures} />
      <FigureGallery figures={message.figures} />
      <TableGallery tables={message.tables} />
    </>
  );
}
