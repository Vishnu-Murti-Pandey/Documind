"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { ChatHeader } from "@/components/chat/chat-header";
import { ChatHistory } from "@/components/chat/chat-history";
import { DocumentSelector } from "@/components/documents/document-selector";
import {
  PromptInput,
  PromptInputFooter,
  PromptInputSubmit,
  PromptInputTextarea,
  PromptInputTools,
  type PromptInputMessage,
} from "@/components/ai-elements/prompt-input";

import { addOptimisticConversation } from "@/features/conversations/cache";
import {
  conversationKeys,
  useConversation,
} from "@/features/conversations/queries";
import { chatMessageKeys } from "@/features/chat/queries";
import { cacheOptimisticUserMessage } from "@/features/chat/cache";
import { streamChat } from "@/features/chat/stream";
import type {
  ChatMessage as ChatMessageType,
  ChatMetadata,
  ChatStreamStatus,
} from "@/features/chat/types";
import { useDocumentSelectionStore } from "@/features/documents/document-store";
import { useDocuments } from "@/features/documents/queries";

type ChatClientProps = {
  initialConversationId?: string;
};

function createTemporaryId(): string {
  return crypto.randomUUID();
}

export function ChatClient({ initialConversationId }: ChatClientProps) {
  const queryClient = useQueryClient();

  // ============================================================
  // Refs
  // ============================================================

  const abortControllerRef = useRef<AbortController | null>(null);

  const conversationIdRef = useRef<string | undefined>(initialConversationId);

  const activeAssistantIdRef = useRef<string | null>(null);

  // ============================================================
  // Local state
  // ============================================================

  const [conversationId, setConversationId] = useState<string | undefined>(
    initialConversationId,
  );

  /**
   * Only unsynchronized messages created in the current browser
   * session are held here. Persisted history is loaded separately
   * by ChatHistory.
   */
  const [liveMessages, setLiveMessages] = useState<ChatMessageType[]>([]);

  const [input, setInput] = useState("");

  const [streamStatus, setStreamStatus] = useState<ChatStreamStatus | null>(
    null,
  );

  const [isStreaming, setIsStreaming] = useState(false);

  const [error, setError] = useState<string | null>(null);

  // ============================================================
  // Document selection
  // ============================================================

  const selectedPaperName = useDocumentSelectionStore(
    (state) => state.selectedPaperName,
  );

  const selectPaper = useDocumentSelectionStore((state) => state.selectPaper);

  // Route props change before the local state reset effect runs. Prefer the
  // route ID so a conversation switch can never briefly use the previous
  // conversation's source document.
  const activeConversationId = initialConversationId ?? conversationId;
  const conversationQuery = useConversation(activeConversationId);
  const documentsQuery = useDocuments(0, 50);
  const persistedPaperName = conversationQuery.data?.paper_name;
  const activePaperName = activeConversationId
    ? persistedPaperName ?? null
    : selectedPaperName;
  const sourceUnavailable = Boolean(
    activeConversationId &&
    !conversationQuery.isLoading &&
    (!persistedPaperName ||
      (!documentsQuery.isLoading &&
        !documentsQuery.isError &&
        !documentsQuery.data?.items.some(
          (document) =>
            document.paper_name === persistedPaperName &&
            document.status === "completed",
        ))),
  );
  const sourceAvailable = !sourceUnavailable;

  /**
   * Synchronize refs when the dynamic route changes.
   */
  useEffect(() => {
    conversationIdRef.current = initialConversationId;

    const resetState = window.setTimeout(() => {
      setConversationId(initialConversationId);
      setLiveMessages([]);
      setError(null);
      setStreamStatus(null);
    }, 0);

    return () => window.clearTimeout(resetState);
  }, [initialConversationId]);

  useEffect(() => {
    function resetForNewChat() {
      abortControllerRef.current?.abort();
      abortControllerRef.current = null;
      activeAssistantIdRef.current = null;
      conversationIdRef.current = undefined;
      setConversationId(undefined);
      setLiveMessages([]);
      setInput("");
      setError(null);
      setStreamStatus(null);
      setIsStreaming(false);
    }

    window.addEventListener("documind:new-chat", resetForNewChat);
    return () => window.removeEventListener("documind:new-chat", resetForNewChat);
  }, []);

  // ============================================================
  // Message helpers
  // ============================================================

  const updateAssistantMessage = useCallback(
    (
      assistantId: string,
      updater: (message: ChatMessageType) => ChatMessageType,
    ) => {
      setLiveMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === assistantId ? updater(message) : message,
        ),
      );
    },
    [],
  );

  const removeLiveMessages = useCallback((messageIds: string[]) => {
    const ids = new Set(messageIds);

    setLiveMessages((currentMessages) =>
      currentMessages.filter((message) => !ids.has(message.id)),
    );
  }, []);

  // ============================================================
  // Submit
  // ============================================================

  async function handleSubmit(promptMessage: PromptInputMessage) {
    const submittedText = promptMessage.text.trim();

    if (!submittedText || isStreaming || !activePaperName) {
      return;
    }

    const userMessageId = createTemporaryId();

    const assistantId = createTemporaryId();

    const userMessage: ChatMessageType = {
      id: userMessageId,
      role: "user",
      content: submittedText,
      citations: [],
      figures: [],
      tables: [],
      status: "completed",
      created_at: new Date().toISOString(),
    };

    const assistantMessage: ChatMessageType = {
      id: assistantId,
      role: "assistant",
      content: "",
      citations: [],
      figures: [],
      tables: [],
      status: "streaming",
      retryPrompt: submittedText,
      created_at: new Date().toISOString(),
    };

    activeAssistantIdRef.current = assistantId;

    setLiveMessages((currentMessages) => [
      ...currentMessages,
      userMessage,
      assistantMessage,
    ]);

    setInput("");
    setError(null);
    setStreamStatus({
      stage: "memory",
      message: "Preparing conversation...",
    });
    setIsStreaming(true);

    const abortController = new AbortController();

    abortControllerRef.current = abortController;

    let resolvedConversationId = conversationIdRef.current;

    let streamCompleted = false;
    let userMessageCached = false;

    const cacheSubmittedUser = (targetConversationId: string) => {
      if (userMessageCached) return;

      cacheOptimisticUserMessage({
        queryClient,
        conversationId: targetConversationId,
        message: userMessage,
        paperName: activePaperName,
      });
      userMessageCached = true;
    };

    if (resolvedConversationId) {
      cacheSubmittedUser(resolvedConversationId);
    }

    try {
      await streamChat(
        {
          message: submittedText,

          conversation_id: conversationIdRef.current,

          filter: {
            paper_name: activePaperName,
          },
        },
        {
          onConversation: (data) => {
            resolvedConversationId = data.conversation_id;

            cacheSubmittedUser(data.conversation_id);

            conversationIdRef.current = data.conversation_id;

            setConversationId(data.conversation_id);

            const resolvedPaperName = data.paper_name ?? activePaperName;

            if (
              !activeConversationId &&
              resolvedPaperName &&
              resolvedPaperName !== selectedPaperName
            ) {
              selectPaper(resolvedPaperName);
            }

            if (data.is_new) {
              addOptimisticConversation({
                queryClient,

                conversationId: data.conversation_id,

                title: submittedText,

                paperName: resolvedPaperName,
              });

              /**
               * Change the URL without remounting ChatClient.
               */
              window.history.replaceState(
                null,
                "",
                `/chat/${data.conversation_id}`,
              );
            }
          },

          onStatus: (status) => {
            setStreamStatus(status);
          },

          onToken: (token) => {
            if (!token) {
              return;
            }

            updateAssistantMessage(assistantId, (message) => ({
              ...message,

              content: message.content + token,
            }));
          },

          onMetadata: (metadata: ChatMetadata) => {
            updateAssistantMessage(assistantId, (message) => ({
              ...message,

              citations: metadata.citations ?? [],

              figures: metadata.figures ?? [],

              tables: metadata.tables ?? [],
            }));
          },

          onDone: (done) => {
            streamCompleted = done.status === "completed";

            updateAssistantMessage(assistantId, (message) => ({
              ...message,

              status: streamCompleted ? "completed" : "failed",
            }));
          },

          onError: (streamError) => {
            setError(streamError.message);

            updateAssistantMessage(assistantId, (message) => ({
              ...message,
              status: "failed",
            }));
          },
        },

        abortController.signal,
      );

      // --------------------------------------------------------
      // Synchronize persisted data
      // --------------------------------------------------------

      await queryClient.invalidateQueries({
        queryKey: conversationKeys.all,
      });

      if (resolvedConversationId) {
        await Promise.all([
          queryClient.invalidateQueries({
            queryKey: conversationKeys.detail(resolvedConversationId),
          }),

          queryClient.invalidateQueries({
            queryKey: chatMessageKeys.conversation(resolvedConversationId),
          }),
        ]);
      }

      /**
       * After the database history has been refreshed, remove the
       * temporary copies so ChatHistory renders persisted messages.
       */
      if (streamCompleted && resolvedConversationId) {
        removeLiveMessages([userMessageId, assistantId]);
      }
    } catch (streamError) {
      const aborted = abortController.signal.aborted;

      if (aborted) {
        updateAssistantMessage(assistantId, (message) => ({
          ...message,
          status: "stopped",
        }));

        setError(null);
      } else {
        const message =
          streamError instanceof Error
            ? streamError.message
            : "Chat request failed.";

        setError(message);

        updateAssistantMessage(assistantId, (currentMessage) => ({
          ...currentMessage,
          status: "failed",
        }));
      }
    } finally {
      abortControllerRef.current = null;

      activeAssistantIdRef.current = null;

      setIsStreaming(false);
      setStreamStatus(null);
    }
  }

  function retryResponse(prompt: string) {
    if (!isStreaming && sourceAvailable) {
      void handleSubmit({ text: prompt, files: [] });
    }
  }

  // ============================================================
  // Stop generation
  // ============================================================

  function stopStreaming() {
    const assistantId = activeAssistantIdRef.current;

    abortControllerRef.current?.abort();

    abortControllerRef.current = null;

    if (assistantId) {
      updateAssistantMessage(assistantId, (message) => ({
        ...message,
        status: "stopped",
      }));
    }

    setIsStreaming(false);
    setStreamStatus(null);
  }

  // ============================================================
  // Render
  // ============================================================

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden">
      <ChatHeader
        conversationId={activeConversationId}
        fallbackPaperName={selectedPaperName}
      />

      <ChatHistory
        conversationId={activeConversationId}
        liveMessages={
          activeConversationId === conversationId ? liveMessages : []
        }
        onRetry={retryResponse}
      />

      {streamStatus && <div className="shrink-0 px-4 py-1.5 text-center text-[11px] font-medium text-muted-foreground">{streamStatus.message}</div>}

      {error && (
        <div className="shrink-0 px-4 pt-3">
          <div className="mx-auto flex max-w-3xl items-start gap-3 rounded-2xl border border-destructive/20 bg-destructive/8 px-4 py-3 text-sm text-destructive shadow-sm">
            <span className="min-w-0 break-words leading-5">{error}</span>
          </div>
        </div>
      )}

      {!sourceAvailable && (
        <div className="shrink-0 border-t border-amber-500/30 bg-amber-500/10 px-4 py-3 text-center text-sm">
          <p className="font-medium">Source document unavailable</p>
          <p className="text-muted-foreground">
            Historical answers and citations are still visible. New questions
            cannot be submitted in this conversation.
          </p>
        </div>
      )}

      <div className="relative z-10 shrink-0 bg-gradient-to-t from-background via-background to-background/0 px-3 pb-4 pt-6 sm:px-6 sm:pb-6">
        <div className="mx-auto max-w-3xl">
          <PromptInput
            onSubmit={handleSubmit}
            className="rounded-[22px] border border-border/80 bg-card shadow-[0_1px_2px_rgb(40_30_20/0.05),0_12px_38px_rgb(40_30_20/0.09)] transition-shadow focus-within:border-primary/35 focus-within:shadow-[0_1px_2px_rgb(40_30_20/0.05),0_18px_46px_rgb(40_30_20/0.12)]"
          >
            <PromptInputTextarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder={
                activePaperName
                  ? "Ask about the selected document..."
                  : "Select a document first..."
              }
              disabled={isStreaming || !activePaperName || !sourceAvailable}
              className="min-h-20 resize-none px-4 pb-2 pt-4 text-[15px] leading-6 placeholder:text-muted-foreground/70"
            />
            <PromptInputFooter className="px-3 pb-3">
              <PromptInputTools>
                <DocumentSelector
                  disabled={Boolean(activeConversationId)}
                  paperName={activeConversationId ? activePaperName : undefined}
                  sourceLoading={Boolean(activeConversationId && conversationQuery.isLoading)}
                />
              </PromptInputTools>
              <PromptInputSubmit
                status={isStreaming ? "streaming" : error ? "error" : "ready"}
                onStop={stopStreaming}
                className="size-9 rounded-xl"
                disabled={!isStreaming && (!input.trim() || !activePaperName || !sourceAvailable)}
              />
            </PromptInputFooter>
          </PromptInput>
          <p className="mt-2.5 text-center text-[10px] tracking-wide text-muted-foreground/75">DocuMind can make mistakes. Verify important details in the cited source.</p>
        </div>
      </div>
    </div>
  );
}
