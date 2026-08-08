"use client";

import { Message, MessageContent } from "@/components/ai-elements/message";
import { AssistantMessage } from "@/components/chat/assistant-message";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/features/chat/types";

type ChatMessageProps = {
  message: ChatMessageType;
  onRetry?: (prompt: string) => void;
};

export function ChatMessage({ message, onRetry }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <Message from={message.role} data-message-id={message.id}>
      <MessageContent className={cn(isUser && "shadow-[0_1px_2px_rgb(40_30_20/0.04)]")}>
        {isUser ? (
          <p className="whitespace-pre-wrap leading-6">{message.content}</p>
        ) : (
          <AssistantMessage message={message} onRetry={onRetry} />
        )}
      </MessageContent>
    </Message>
  );
}
