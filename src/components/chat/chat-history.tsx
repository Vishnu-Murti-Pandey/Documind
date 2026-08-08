"use client";

import { ArrowDown, LoaderCircle } from "lucide-react";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import { ChatMessage } from "@/components/chat/chat-message";
import { Button } from "@/components/ui/button";
import { mapPersistedMessages } from "@/features/chat/api";
import { useInfiniteConversationMessages } from "@/features/chat/queries";
import type { ChatMessage as ChatMessageType } from "@/features/chat/types";

type ChatHistoryProps = {
  conversationId?: string;
  liveMessages: ChatMessageType[];
  onRetry?: (prompt: string) => void;
};

export function ChatHistory({
  conversationId,
  liveMessages,
  onRetry,
}: ChatHistoryProps) {
  const scrollRef = useRef<HTMLDivElement | null>(null);

  const previousScrollHeightRef = useRef<number | null>(null);

  const initialScrollCompletedRef = useRef(false);
  const nearBottomRef = useRef(true);
  const previousLiveLengthRef = useRef(0);
  const [showLatestButton, setShowLatestButton] = useState(false);

  const messagesQuery = useInfiniteConversationMessages(conversationId);

  const persistedMessages = useMemo(() => {
    const pages = messagesQuery.data?.pages ?? [];

    return [...pages].reverse().flatMap((page) => mapPersistedMessages(page));
  }, [messagesQuery.data]);

  const persistedIds = useMemo(
    () => new Set(persistedMessages.map((message) => message.id)),
    [persistedMessages],
  );

  const combinedMessages = useMemo(() => {
    const messages = [
      ...persistedMessages,

      ...liveMessages.filter((message) => !persistedIds.has(message.id)),
    ];
    return messages.map((message, index) => message.role === "assistant" && !message.retryPrompt ? { ...message, retryPrompt: [...messages.slice(0, index)].reverse().find((item) => item.role === "user")?.content } : message);
  }, [persistedMessages, liveMessages, persistedIds]);

  // Initial page should open at the bottom.
  useEffect(() => {
    if (initialScrollCompletedRef.current || messagesQuery.isLoading) {
      return;
    }

    const element = scrollRef.current;

    if (!element) {
      return;
    }

    requestAnimationFrame(() => {
      element.scrollTop = element.scrollHeight;

      initialScrollCompletedRef.current = true;
    });
  }, [messagesQuery.isLoading, conversationId]);

  // Preserve viewport when older messages are prepended.
  useLayoutEffect(() => {
    const previousHeight = previousScrollHeightRef.current;

    const element = scrollRef.current;

    if (previousHeight === null || !element) {
      return;
    }

    const heightDifference = element.scrollHeight - previousHeight;

    element.scrollTop += heightDifference;

    previousScrollHeightRef.current = null;
  }, [persistedMessages.length]);

  useEffect(() => {
    const element = scrollRef.current;
    if (!element || !initialScrollCompletedRef.current) return;
    const isNewMessage = liveMessages.length > previousLiveLengthRef.current;
    if (isNewMessage) {
      const newestUser = [...liveMessages].reverse().find((message) => message.role === "user");
      const target = newestUser ? element.querySelector(`[data-message-id="${newestUser.id}"]`) : null;
      target?.scrollIntoView({ block: "start", behavior: "smooth" });
    } else if (nearBottomRef.current) {
      element.scrollTo({ top: element.scrollHeight, behavior: "smooth" });
    }
    previousLiveLengthRef.current = liveMessages.length;
  }, [liveMessages]);

  async function loadOlderMessages() {
    const element = scrollRef.current;

    if (
      !element ||
      !messagesQuery.hasNextPage ||
      messagesQuery.isFetchingNextPage
    ) {
      return;
    }

    previousScrollHeightRef.current = element.scrollHeight;

    await messagesQuery.fetchNextPage();
  }

  function handleScroll() {
    const element = scrollRef.current;

    if (!element) {
      return;
    }

    if (element.scrollTop <= 80) {
      void loadOlderMessages();
    }
    const distance = element.scrollHeight - element.scrollTop - element.clientHeight;
    nearBottomRef.current = distance < 160;
    setShowLatestButton(distance >= 160);
  }

  if (conversationId && messagesQuery.isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoaderCircle className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="relative min-h-0 flex-1">
    <div ref={scrollRef} onScroll={handleScroll} className="h-full overflow-y-auto">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-6 px-4 py-8 md:px-8">
        {messagesQuery.hasNextPage && (
          <div className="flex justify-center">
            <Button
              type="button"
              size="sm"
              variant="ghost"
              disabled={messagesQuery.isFetchingNextPage}
              onClick={() => void loadOlderMessages()}
            >
              {messagesQuery.isFetchingNextPage
                ? "Loading older messages..."
                : "Load older messages"}
            </Button>
          </div>
        )}

        {combinedMessages.map((message) => (
          <ChatMessage key={message.id} message={message} onRetry={onRetry} />
        ))}
      </div>
    </div>
    {showLatestButton && <Button type="button" size="icon" variant="secondary" className="absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full shadow-lg" onClick={() => scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })} aria-label="Scroll to latest message"><ArrowDown className="h-4 w-4" /></Button>}
    </div>
  );
}
