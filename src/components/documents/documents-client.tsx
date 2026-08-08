"use client";

import { FileUp, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { DeleteDocumentDialog } from "@/components/documents/delete-document-dialog";
import { DocumentCard } from "@/components/documents/document-card";
import { IngestionProgress } from "@/components/documents/ingestion-progress";
import { OverwriteDocumentDialog } from "@/components/documents/overwrite-document-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

import { useDocumentSelectionStore } from "@/features/documents/document-store";
import {
  cancelDocumentIngestion,
  streamDocumentIngestion,
} from "@/features/documents/ingestion-stream";
import {
  documentKeys,
  useDeleteDocument,
  useDocuments,
} from "@/features/documents/queries";
import type {
  DocumentItem,
  IngestionEventData,
  IngestionEventType,
} from "@/features/documents/types";
import { toast } from "sonner";

const MAX_UPLOAD_SIZE_MB = 50;

const MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024;

export function DocumentsClient() {
  const queryClient = useQueryClient();

  const documentsQuery = useDocuments(0, 50);

  const deleteMutation = useDeleteDocument();

  const selectedPaperName = useDocumentSelectionStore(
    (state) => state.selectedPaperName,
  );

  const selectPaper = useDocumentSelectionStore((state) => state.selectPaper);

  const inputRef = useRef<HTMLInputElement | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);
  const activeDocumentIdRef = useRef<string | null>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [lastAttemptedFile, setLastAttemptedFile] = useState<File | null>(null);

  const [ingestionEventType, setIngestionEventType] =
    useState<IngestionEventType | null>(null);

  const [ingestionData, setIngestionData] = useState<IngestionEventData | null>(
    null,
  );

  const [isIngesting, setIsIngesting] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const [deleteTarget, setDeleteTarget] = useState<DocumentItem | null>(null);

  const [overwriteDialogOpen, setOverwriteDialogOpen] = useState(false);

  const [pendingOverwriteFile, setPendingOverwriteFile] = useState<File | null>(
    null,
  );

  // --------------------------------------------------
  // File selection
  // --------------------------------------------------

  function resetIngestionFeedback() {
    setError(null);
    setIngestionEventType(null);
    setIngestionData(null);
  }

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    resetIngestionFeedback();

    const isPdf =
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
      setError("Please select a valid PDF file.");

      event.target.value = "";
      setSelectedFile(null);

      return;
    }

    if (file.size > MAX_UPLOAD_SIZE_BYTES) {
      setError(`The PDF exceeds the ${MAX_UPLOAD_SIZE_MB} MB upload limit.`);

      event.target.value = "";
      setSelectedFile(null);

      return;
    }

    if (file.size === 0) {
      setError("The selected PDF is empty.");

      event.target.value = "";
      setSelectedFile(null);

      return;
    }

    setSelectedFile(file);
    setLastAttemptedFile(null);
  }

  // --------------------------------------------------
  // Ingestion
  // --------------------------------------------------

  async function beginIngestion(file: File, overwrite = false) {
    if (isIngesting) {
      return;
    }

    setError(null);
    setIsIngesting(true);
    setLastAttemptedFile(file);

    setIngestionEventType("status");

    setIngestionData({
      stage: "uploading",
      message: "Uploading document...",
      progress: 0,
      filename: file.name,
    });

    const controller = new AbortController();

    abortControllerRef.current = controller;

    try {
      await streamDocumentIngestion(
        file,
        {
          onEvent: (eventType, data) => {
            if (data.document_id) {
              activeDocumentIdRef.current = data.document_id;
            }
            setIngestionEventType(eventType);

            setIngestionData(data);

            if (eventType === "completed") {
              toast.success("Document uploaded");
              void queryClient.invalidateQueries({
                queryKey: documentKeys.all,
              });

              if (data.paper_name) {
                selectPaper(data.paper_name);
              }
            }

            if (eventType === "error") {
              toast.error(data.detail || data.message || "Document ingestion failed.");
              setError(
                data.detail || data.message || "Document ingestion failed.",
              );
            }
          },

          onError: (streamError) => {
            setError(streamError.message);
            toast.error(streamError.message);
          },
        },
        {
          overwrite,
          signal: controller.signal,
        },
      );

      setSelectedFile(null);
      setPendingOverwriteFile(null);
      setOverwriteDialogOpen(false);

      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } catch (ingestionError) {
      const aborted = controller.signal.aborted;

      if (aborted) {
        setIngestionEventType("error");

        setIngestionData({
          status: "failed",
          stage: "cancelled",
          message: "Document ingestion was stopped.",
          detail: "The upload or processing request was cancelled.",
          progress: ingestionData?.progress ?? 0,
        });

        return;
      }

      const message =
        ingestionError instanceof Error
          ? ingestionError.message
          : "Document ingestion failed.";

      setError(message);

      const duplicate = message.toLowerCase().includes("already exists");

      if (duplicate && !overwrite) {
        setPendingOverwriteFile(file);

        setOverwriteDialogOpen(true);

        return;
      }

      setIngestionEventType("error");

      setIngestionData({
        status: "failed",
        message: "Document ingestion failed.",
        detail: message,
        progress: ingestionData?.progress ?? 0,
      });
    } finally {
      abortControllerRef.current = null;
      activeDocumentIdRef.current = null;

      setIsIngesting(false);
    }
  }

  async function stopIngestion() {
    const documentId = activeDocumentIdRef.current;

    try {
      if (documentId) {
        await cancelDocumentIngestion(documentId);
      }
    } catch (cancelError) {
      toast.error(
        cancelError instanceof Error
          ? cancelError.message
          : "Could not stop document ingestion.",
      );
    } finally {
      abortControllerRef.current?.abort();
      void queryClient.invalidateQueries({ queryKey: documentKeys.all });
    }
  }

  function retryLastIngestion() {
    if (!lastAttemptedFile || isIngesting) {
      return;
    }

    void beginIngestion(lastAttemptedFile, false);
  }

  function confirmOverwrite() {
    if (!pendingOverwriteFile || isIngesting) {
      return;
    }

    void beginIngestion(pendingOverwriteFile, true);
  }

  // --------------------------------------------------
  // Re-ingestion
  // --------------------------------------------------

  function handleReingest(document: DocumentItem) {
    if (isIngesting) {
      return;
    }

    resetIngestionFeedback();

    setError(
      `Select "${document.original_filename}" or another PDF with the same document name to replace it.`,
    );

    inputRef.current?.click();
  }

  // --------------------------------------------------
  // Delete
  // --------------------------------------------------

  function handleDeleteConfirm() {
    if (!deleteTarget || isIngesting) {
      return;
    }

    const paperName = deleteTarget.paper_name;

    deleteMutation.mutate(paperName, {
      onSuccess: () => {
        if (selectedPaperName === paperName) {
          selectPaper(null);
        }

        setDeleteTarget(null);
        toast.success("Document deleted");
      },

      onError: (deleteError) => {
        setError(
          deleteError instanceof Error
            ? deleteError.message
            : "Could not delete document.",
        );
        toast.error(deleteError instanceof Error ? deleteError.message : "Could not delete document.");
      },
    });
  }

  const documents = documentsQuery.data?.items ?? [];

  const anyActionPending = isIngesting || deleteMutation.isPending;

  return (
    <>
      <div className="h-full overflow-y-auto">
        <div className="mx-auto max-w-6xl space-y-8 px-4 py-8 sm:px-6 md:py-12 lg:px-10">
          <div>
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-primary">Knowledge base</p>
            <h1 className="font-serif text-3xl font-medium tracking-[-0.025em] sm:text-4xl">Your document library</h1>

            <p className="mt-2 text-sm text-muted-foreground">
              Upload PDF documents, track processing progress, and choose a
              retrieval source for chat.
            </p>
          </div>

          <section className="enterprise-panel space-y-5 p-5 sm:p-6">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <FileUp className="h-5 w-5" />
              </div>

              <div>
                <h2 className="text-[15px] font-semibold">Add a PDF document</h2>

                <p className="text-sm text-muted-foreground">
                  Maximum file size: {MAX_UPLOAD_SIZE_MB} MB.
                </p>
              </div>
            </div>

            <Input
              ref={inputRef}
              type="file"
              accept=".pdf,application/pdf"
              disabled={isIngesting}
              onChange={handleFileChange}
              className="h-14 cursor-pointer rounded-xl border-dashed bg-muted/20 px-4 py-2 leading-9 file:mr-4 file:h-9 file:align-middle file:rounded-lg file:border-0 file:bg-primary/10 file:px-3 file:py-0 file:text-xs file:font-semibold file:leading-9 file:text-primary"
            />

            {selectedFile && (
              <div className="rounded-lg bg-muted p-3 text-sm">
                <p className="font-medium">{selectedFile.name}</p>

                <p className="mt-1 text-xs text-muted-foreground">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            )}

            {error && (
              <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              <Button
                type="button"
                disabled={!selectedFile || isIngesting}
                onClick={() => {
                  if (selectedFile) {
                    void beginIngestion(selectedFile, false);
                  }
                }}
              >
                <Upload className="h-4 w-4" />

                {isIngesting ? "Ingesting..." : "Upload and ingest"}
              </Button>
            </div>
          </section>

          <IngestionProgress
            eventType={ingestionEventType}
            data={ingestionData}
            fileName={selectedFile?.name || lastAttemptedFile?.name}
            isIngesting={isIngesting}
            canRetry={
              ingestionEventType === "error" && Boolean(lastAttemptedFile)
            }
            onStop={() => void stopIngestion()}
            onRetry={retryLastIngestion}
          />

          <section className="space-y-4">
            <div className="flex items-end justify-between gap-4">
              <div>
                <h2 className="font-serif text-2xl font-medium tracking-[-0.02em]">Available documents</h2>

                <p className="mt-1 text-sm text-muted-foreground">
                  Choose one as the retrieval source for chat.
                </p>
              </div>

              <span className="text-sm text-muted-foreground">
                {documentsQuery.data?.total ?? 0} documents
              </span>
            </div>

            {documentsQuery.isLoading && (
              <div className="grid gap-4">
                {Array.from({
                  length: 3,
                }).map((_, index) => (
                  <Skeleton key={index} className="h-48 w-full rounded-xl" />
                ))}
              </div>
            )}

            {documentsQuery.isError && (
              <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
                Could not load documents.
              </div>
            )}

            {!documentsQuery.isLoading &&
              !documentsQuery.isError &&
              documents.length === 0 && (
                <div className="rounded-xl border border-dashed p-10 text-center">
                  <FileUp className="mx-auto h-8 w-8 text-muted-foreground" />

                  <h3 className="mt-4 font-medium">No documents yet</h3>

                  <p className="mt-2 text-sm text-muted-foreground">
                    Upload your first PDF document to begin.
                  </p>
                </div>
              )}

            <div className="grid gap-4 xl:grid-cols-2">
              {documents.map((document) => (
                <DocumentCard
                  key={document.id}
                  document={document}
                  selected={selectedPaperName === document.paper_name}
                  deleting={
                    deleteMutation.isPending &&
                    deleteMutation.variables === document.paper_name
                  }
                  controlsDisabled={anyActionPending}
                  onSelect={() => selectPaper(document.paper_name)}
                  onDelete={() => setDeleteTarget(document)}
                  onReingest={() => handleReingest(document)}
                />
              ))}
            </div>
          </section>
        </div>
      </div>

      <DeleteDocumentDialog
        document={deleteTarget}
        open={Boolean(deleteTarget)}
        pending={deleteMutation.isPending}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteTarget(null);
          }
        }}
        onConfirm={handleDeleteConfirm}
      />

      <OverwriteDocumentDialog
        open={overwriteDialogOpen}
        pending={isIngesting}
        fileName={pendingOverwriteFile?.name}
        onOpenChange={(open) => {
          setOverwriteDialogOpen(open);

          if (!open) {
            setPendingOverwriteFile(null);
          }
        }}
        onConfirm={confirmOverwrite}
      />
    </>
  );
}
