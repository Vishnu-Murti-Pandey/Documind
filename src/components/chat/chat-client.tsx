"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { BookOpen, StopCircle } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";

import { DocumentSelector } from "@/components/documents/document-selector";
import { useDocumentSelectionStore } from "@/features/documents/document-store";

import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import {
  PromptInput,
  PromptInputSubmit,
  PromptInputTextarea,
  type PromptInputMessage,
} from "@/components/ai-elements/prompt-input";
import { ChatMessage } from "@/components/chat/chat-message";
import { Button } from "@/components/ui/button";
import { conversationKeys } from "@/features/conversations/queries";
import {
  getConversationMessages,
  mapPersistedMessages,
} from "@/features/chat/api";
import { streamChat } from "@/features/chat/stream";
import type {
  ChatMessage as ChatMessageType,
  ChatMetadata,
  ChatStreamStatus,
} from "@/features/chat/types";

type ChatClientProps = {
  initialConversationId?: string;
};

function createTemporaryId(): string {
  return crypto.randomUUID();
}

export function ChatClient({ initialConversationId }: ChatClientProps) {
  const queryClient = useQueryClient();

  const abortControllerRef = useRef<AbortController | null>(null);

  const conversationIdRef = useRef<string | undefined>(initialConversationId);

  const [conversationId, setConversationId] = useState<string | undefined>(
    initialConversationId,
  );

  const [messages, setMessages] = useState<ChatMessageType[]>([]);

  const [input, setInput] = useState("");

  const [streamStatus, setStreamStatus] = useState<ChatStreamStatus | null>(
    null,
  );

  const [isLoadingHistory, setIsLoadingHistory] = useState(
    Boolean(initialConversationId),
  );

  const [isStreaming, setIsStreaming] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const selectedPaperName = useDocumentSelectionStore(
    (state) => state.selectedPaperName,
  );

  useEffect(() => {
    if (!initialConversationId) {
      setMessages([]);
      setConversationId(undefined);
      setIsLoadingHistory(false);
      return;
    }

    const currentConversationId = initialConversationId;

    let active = true;

    async function loadHistory() {
      setIsLoadingHistory(true);
      setError(null);

      try {
        const response = await getConversationMessages(
          currentConversationId,
          0,
          100,
        );

        if (!active) {
          return;
        }

        setMessages(mapPersistedMessages(response));

        setConversationId(currentConversationId);

        conversationIdRef.current = currentConversationId;
      } catch (loadError) {
        if (!active) {
          return;
        }

        setError(
          loadError instanceof Error
            ? loadError.message
            : "Could not load conversation.",
        );
      } finally {
        if (active) {
          setIsLoadingHistory(false);
        }
      }
    }

    void loadHistory();

    return () => {
      active = false;
    };
  }, [initialConversationId]);

  const updateAssistantMessage = useCallback(
    (
      assistantId: string,
      updater: (message: ChatMessageType) => ChatMessageType,
    ) => {
      setMessages((currentMessages) =>
        currentMessages.map((message) =>
          message.id === assistantId ? updater(message) : message,
        ),
      );
    },
    [],
  );

  async function handleSubmit(promptMessage: PromptInputMessage) {
    const text = promptMessage.text.trim();

    if (!text || isStreaming || !selectedPaperName) {
      return;
    }

    const userMessage: ChatMessageType = {
      id: createTemporaryId(),
      role: "user",
      content: text,
      citations: [],
      figures: [],
      tables: [],
      status: "completed",
    };

    const assistantId = createTemporaryId();

    const assistantMessage: ChatMessageType = {
      id: assistantId,
      role: "assistant",
      content: "",
      citations: [],
      figures: [],
      tables: [],
      status: "streaming",
    };

    setMessages((currentMessages) => [
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

    try {
      await streamChat(
        {
          message: text,
          conversation_id: conversationIdRef.current,
          filter: selectedPaperName
            ? {
                paper_name: selectedPaperName,
              }
            : null,
        },
        {
          onConversation: (data) => {
            resolvedConversationId = data.conversation_id;

            conversationIdRef.current = data.conversation_id;

            setConversationId(data.conversation_id);

            if (data.is_new) {
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
            updateAssistantMessage(assistantId, (message) => ({
              ...message,
              content: message.content + token,
            }));
          },

          onMetadata: (metadata) => {
            updateAssistantMessage(assistantId, (message) => ({
              ...message,
              citations: metadata.citations ?? [],
              figures: metadata.figures ?? [],
              tables: metadata.tables ?? [],
            }));
          },

          onDone: (done) => {
            updateAssistantMessage(assistantId, (message) => ({
              ...message,
              status: done.status === "completed" ? "completed" : "failed",
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

      await queryClient.invalidateQueries({
        queryKey: conversationKeys.all,
      });

      if (resolvedConversationId) {
        await queryClient.invalidateQueries({
          queryKey: conversationKeys.messages(resolvedConversationId),
        });
      }
    } finally {
      abortControllerRef.current = null;
      setIsStreaming(false);
      setStreamStatus(null);
    }
  }

  function stopStreaming() {
    abortControllerRef.current?.abort();

    abortControllerRef.current = null;

    setIsStreaming(false);

    setStreamStatus(null);
  }

  if (isLoadingHistory) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
        Loading conversation...
      </div>
    );
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <Conversation className="min-h-0 flex-1">
        <ConversationContent className="mx-auto w-full max-w-4xl gap-6 px-4 py-8 md:px-8">
          {messages.length === 0 ? (
            <ConversationEmptyState
              icon={<BookOpen className="h-8 w-8" />}
              title="Ask your research papers"
              description="Upload a paper, choose it as your source, and ask detailed questions."
            />
          ) : (
            messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))
          )}

          {streamStatus && (
            <div className="ml-1 text-xs text-muted-foreground">
              {streamStatus.message}
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              {error}
            </div>
          )}
        </ConversationContent>

        <ConversationScrollButton />
      </Conversation>

      <div className="shrink-0 border-t bg-background px-4 py-4">
        <div className="mx-auto max-w-4xl">
          <div className="mb-2 flex items-center justify-between gap-3">
            <DocumentSelector />

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
              disabled={isStreaming || !selectedPaperName}
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
                  disabled={!input.trim() || !selectedPaperName}
                />
              )}
            </div>
          </PromptInput>
        </div>
      </div>
    </div>
  );
}
