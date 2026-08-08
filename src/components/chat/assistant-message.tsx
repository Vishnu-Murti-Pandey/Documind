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
        <div className="mt-2 flex items-center gap-2 rounded-lg border bg-muted/50 p-3 text-sm text-muted-foreground">
          <RotateCcw className="h-4 w-4" /> Generation stopped. You can retry this response.
        </div>
      )}
      {message.status === "failed" && (
        <div className="mt-2 flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
          <TriangleAlert className="h-4 w-4" /> The response could not be completed. Try again.
        </div>
      )}
    </>
  );
}

function AssistantMessageActions({ message, onRetry }: { message: ChatMessage; onRetry?: (prompt: string) => void }) {
  const [copied, setCopied] = useState(false);
  const canRetry = Boolean(message.retryPrompt) && message.status !== "streaming";

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
    <MessageActions className="mt-1 opacity-70 transition-opacity hover:opacity-100 focus-within:opacity-100">
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
