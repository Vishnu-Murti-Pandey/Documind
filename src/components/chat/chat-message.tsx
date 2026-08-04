"use client";

import { ImageIcon, LoaderCircle } from "lucide-react";

import {
  Message,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import type { ChatMessage as ChatMessageType } from "@/features/chat/types";

type ChatMessageProps = {
  message: ChatMessageType;
};

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <Message from={message.role}>
      <MessageContent
        className={cn(isUser && "rounded-2xl bg-muted px-4 py-3")}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-6">
            {message.content}
          </p>
        ) : (
          <>
            <MessageResponse>{message.content}</MessageResponse>

            {message.status === "streaming" && !message.content && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <LoaderCircle className="h-4 w-4 animate-spin" />
                Preparing response...
              </div>
            )}

            {message.status === "failed" && (
              <p className="mt-2 text-sm text-destructive">
                The response could not be completed.
              </p>
            )}

            {message.citations.length > 0 && (
              <div className="mt-5 flex flex-wrap gap-2">
                {message.citations.map((citation, index) => (
                  <Badge
                    key={`${citation.chunk_id}-${index}`}
                    variant="secondary"
                  >
                    {citation.section_title}
                  </Badge>
                ))}
              </div>
            )}

            {message.figures.length > 0 && (
              <div className="mt-5 grid gap-4 md:grid-cols-2">
                {message.figures.map((figure, index) => (
                  <figure
                    key={`${figure.chunk_id}-${index}`}
                    className="overflow-hidden rounded-xl border bg-card"
                  >
                    <img
                      src={`${process.env.NEXT_PUBLIC_API_URL}${figure.image_url}`}
                      alt={figure.caption || `Figure ${index + 1}`}
                      className="aspect-video w-full object-contain"
                    />

                    <figcaption className="space-y-1 border-t p-3">
                      <div className="flex items-center gap-2 text-sm font-medium">
                        <ImageIcon className="h-4 w-4" />

                        {figure.caption || `Figure ${index + 1}`}
                      </div>

                      <p className="line-clamp-3 text-xs text-muted-foreground">
                        {figure.section_title}
                      </p>
                    </figcaption>
                  </figure>
                ))}
              </div>
            )}

            {message.tables.length > 0 && (
              <div className="mt-5 space-y-4">
                {message.tables.map((table, index) => (
                  <div
                    key={`${table.chunk_id}-${index}`}
                    className="overflow-x-auto rounded-xl border p-4"
                  >
                    {table.summary && (
                      <p className="mb-3 text-sm text-muted-foreground">
                        {table.summary}
                      </p>
                    )}

                    <div
                      className="prose prose-sm max-w-none"
                      dangerouslySetInnerHTML={{
                        __html: table.html,
                      }}
                    />
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </MessageContent>
    </Message>
  );
}
