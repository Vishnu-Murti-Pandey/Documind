"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { StopCircle } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import { ChatHeader } from "@/components/chat/chat-header";
import { ChatHistory } from "@/components/chat/chat-history";
import { DocumentSelector } from "@/components/documents/document-selector";
import {
  PromptInput,
  PromptInputSubmit,
  PromptInputTextarea,
  type PromptInputMessage,
} from "@/components/ai-elements/prompt-input";
import { Button } from "@/components/ui/button";

import { addOptimisticConversation } from "@/features/conversations/cache";
import {
  conversationKeys,
  useConversation,
} from "@/features/conversations/queries";
import { chatMessageKeys } from "@/features/chat/queries";
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

  const conversationQuery = useConversation(conversationId);
  const documentsQuery = useDocuments(0, 50);
  const persistedPaperName = conversationQuery.data?.paper_name;
  const sourceAvailable =
    !conversationId ||
    !persistedPaperName ||
    documentsQuery.isLoading ||
    documentsQuery.isError ||
    Boolean(
      documentsQuery.data?.items.some(
        (document) =>
          document.paper_name === persistedPaperName &&
          document.status === "completed",
      ),
    );

  /**
   * When an existing conversation is opened, restore the source
   * document persisted on the conversation.
   *
   * This runs in an effect instead of mutating Zustand during
   * render.
   */
  useEffect(() => {
    const persistedPaperName = conversationQuery.data?.paper_name;

    if (persistedPaperName && persistedPaperName !== selectedPaperName) {
      selectPaper(persistedPaperName);
    }
  }, [conversationQuery.data?.paper_name, selectedPaperName, selectPaper]);

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

    if (!submittedText || isStreaming || !selectedPaperName) {
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

    try {
      await streamChat(
        {
          message: submittedText,

          conversation_id: conversationIdRef.current,

          filter: {
            paper_name: selectedPaperName,
          },
        },
        {
          onConversation: (data) => {
            resolvedConversationId = data.conversation_id;

            conversationIdRef.current = data.conversation_id;

            setConversationId(data.conversation_id);

            const resolvedPaperName = data.paper_name ?? selectedPaperName;

            if (resolvedPaperName && resolvedPaperName !== selectedPaperName) {
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
    <div className="flex h-full min-h-0 flex-col">
      <ChatHeader
        conversationId={conversationId}
        fallbackPaperName={selectedPaperName}
      />

      <ChatHistory
        conversationId={conversationId}
        liveMessages={liveMessages}
        onRetry={retryResponse}
      />

      {streamStatus && (
        <div className="shrink-0 border-t px-4 py-2 text-center text-xs text-muted-foreground">
          {streamStatus.message}
        </div>
      )}

      {error && (
        <div className="shrink-0 px-4 pt-3">
          <div className="mx-auto max-w-4xl rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
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

      <div className="shrink-0 border-t bg-background px-3 py-3 sm:px-4 sm:py-4">
        <div className="mx-auto max-w-4xl">
          <div className="mb-2 flex min-w-0 items-center justify-between gap-2">
            <DocumentSelector disabled={Boolean(conversationId)} />

            {!selectedPaperName && (
              <span className="text-xs text-amber-600">
                Select a document before asking.
              </span>
            )}
          </div>

          <PromptInput
            onSubmit={handleSubmit}
            className="rounded-2xl border shadow-sm"
          >
            <PromptInputTextarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder={
                selectedPaperName
                  ? "Ask about the selected paper..."
                  : "Select a document first..."
              }
              disabled={isStreaming || !selectedPaperName || !sourceAvailable}
              className="min-h-14 resize-none"
            />

            <div className="flex items-center justify-between gap-3 px-3 pb-3">
              <p className="truncate text-xs text-muted-foreground">
                {selectedPaperName
                  ? `Source: ${selectedPaperName}`
                  : "No document selected"}
              </p>

              {isStreaming ? (
                <Button
                  type="button"
                  size="icon"
                  variant="outline"
                  onClick={stopStreaming}
                  aria-label="Stop generating"
                >
                  <StopCircle className="h-4 w-4" />
                </Button>
              ) : (
                <PromptInputSubmit
                  disabled={!input.trim() || !selectedPaperName || !sourceAvailable}
                />
              )}
            </div>
          </PromptInput>
        </div>
      </div>
    </div>
  );
}
