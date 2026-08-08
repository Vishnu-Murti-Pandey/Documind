"use client";

import { ArrowDown, LibraryBig, LoaderCircle } from "lucide-react";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

import { ChatMessage } from "@/components/chat/chat-message";
import { Button } from "@/components/ui/button";
import { ConversationEmptyState } from "@/components/ai-elements/conversation";
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
  const latestSubmittedUserIdRef = useRef<string | null>(null);
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
    const latestPersistedUser = [...persistedMessages]
      .reverse()
      .find((message) => message.role === "user");

    const messages = [
      ...persistedMessages,

      ...liveMessages.filter((message) => {
        if (persistedIds.has(message.id)) {
          return false;
        }

        // The backend persists the current user message before generation and
        // returns a database ID. Reconcile that row with its optimistic copy
        // by content so both are not shown during the response stream.
        if (
          message.role === "user" &&
          latestPersistedUser?.content === message.content &&
          message.created_at &&
          latestPersistedUser.created_at &&
          new Date(latestPersistedUser.created_at).getTime() >=
            new Date(message.created_at).getTime()
        ) {
          return false;
        }

        return true;
      }),
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

  useLayoutEffect(() => {
    const element = scrollRef.current;
    if (!element || !initialScrollCompletedRef.current) return;

    const newestUser = [...liveMessages]
      .reverse()
      .find((message) => message.role === "user");
    const isNewSubmission =
      newestUser && newestUser.id !== latestSubmittedUserIdRef.current;

    if (isNewSubmission) {
      // Keep the submitted question and assistant placeholder next to the
      // fixed composer. Element-level viewport scrolling can move outer
      // ancestors, so update only this container's scroll position.
      latestSubmittedUserIdRef.current = newestUser.id;
      nearBottomRef.current = true;
      setShowLatestButton(false);
      element.scrollTop = element.scrollHeight;
    } else if (nearBottomRef.current) {
      // Follow streaming tokens without queuing smooth-scroll animations.
      element.scrollTop = element.scrollHeight;
    }
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
      <div className="flex min-h-0 flex-1 items-center justify-center">
        <LoaderCircle className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="relative min-h-0 flex-1 overflow-hidden">
    <div ref={scrollRef} onScroll={handleScroll} className="h-full overscroll-contain overflow-y-auto [overflow-anchor:none]">
      <div className="mx-auto flex min-h-full w-full max-w-3xl flex-col gap-8 px-4 pb-10 pt-10 md:px-6 md:pb-12 md:pt-14">
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

        {combinedMessages.length === 0 && (
          <ConversationEmptyState className="my-auto min-h-[52vh]" icon={<span className="flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary"><LibraryBig className="size-5" /></span>} title="Ask your document library" description="Select a source and explore it with grounded answers, figures, tables, and precise citations." />
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
