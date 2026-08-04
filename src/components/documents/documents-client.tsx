"use client";

import { FileUp, LoaderCircle, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { DocumentCard } from "@/components/documents/document-card";
import { IngestionProgress } from "@/components/documents/ingestion-progress";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

import {
  documentKeys,
  useDeleteDocument,
  useDocuments,
} from "@/features/documents/queries";
import { useDocumentSelectionStore } from "@/features/documents/document-store";
import { streamDocumentIngestion } from "@/features/documents/ingestion-stream";
import type {
  IngestionEventData,
  IngestionEventType,
} from "@/features/documents/types";

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

  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [overwrite, setOverwrite] = useState(false);

  const [ingestionEventType, setIngestionEventType] =
    useState<IngestionEventType | null>(null);

  const [ingestionData, setIngestionData] = useState<IngestionEventData | null>(
    null,
  );

  const [isIngesting, setIsIngesting] = useState(false);

  const [error, setError] = useState<string | null>(null);

  function handleFileChange(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    if (
      file.type !== "application/pdf" &&
      !file.name.toLowerCase().endsWith(".pdf")
    ) {
      setError("Please select a PDF file.");

      event.target.value = "";

      return;
    }

    setSelectedFile(file);
    setOverwrite(false);
    setError(null);
    setIngestionEventType(null);
    setIngestionData(null);
  }

  async function beginIngestion(shouldOverwrite = overwrite) {
    if (!selectedFile || isIngesting) {
      return;
    }

    setError(null);
    setIsIngesting(true);

    const controller = new AbortController();

    abortControllerRef.current = controller;

    try {
      await streamDocumentIngestion(
        selectedFile,
        {
          onEvent: (eventType, data) => {
            setIngestionEventType(eventType);

            setIngestionData(data);

            if (eventType === "completed") {
              void queryClient.invalidateQueries({
                queryKey: documentKeys.all,
              });

              if (data.paper_name) {
                selectPaper(data.paper_name);
              }
            }
          },

          onError: (streamError) => {
            setError(streamError.message);
          },
        },
        {
          overwrite: shouldOverwrite,
          signal: controller.signal,
        },
      );

      setSelectedFile(null);
      setOverwrite(false);

      if (inputRef.current) {
        inputRef.current.value = "";
      }
    } catch (ingestionError) {
      const message =
        ingestionError instanceof Error
          ? ingestionError.message
          : "Document ingestion failed.";

      setError(message);

      if (message.toLowerCase().includes("already exists")) {
        setOverwrite(true);
      }
    } finally {
      abortControllerRef.current = null;

      setIsIngesting(false);
    }
  }

  function stopIngestion() {
    abortControllerRef.current?.abort();

    abortControllerRef.current = null;

    setIsIngesting(false);
  }

  function handleReingest(paperName: string) {
    const matchingDocument = documentsQuery.data?.items.find(
      (document) => document.paper_name === paperName,
    );

    if (!matchingDocument) {
      return;
    }

    setError("Choose the original PDF again, then select overwrite.");

    setOverwrite(true);

    inputRef.current?.click();
  }

  async function handleDelete(paperName: string) {
    const confirmed = window.confirm(
      "Delete this document, its vectors, and its stored assets?",
    );

    if (!confirmed) {
      return;
    }

    deleteMutation.mutate(paperName, {
      onSuccess: () => {
        if (selectedPaperName === paperName) {
          selectPaper(null);
        }
      },
    });
  }

  const documents = documentsQuery.data?.items ?? [];

  return (
    <div className="h-full overflow-y-auto">
      <div className="mx-auto max-w-6xl space-y-8 px-5 py-8 md:px-8">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Documents</h1>

          <p className="mt-2 text-sm text-muted-foreground">
            Upload research papers, track ingestion progress, and choose which
            paper DocuMind should use.
          </p>
        </div>

        <section className="space-y-4 rounded-xl border bg-card p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-muted">
              <FileUp className="h-5 w-5" />
            </div>

            <div>
              <h2 className="font-medium">Upload PDF</h2>

              <p className="text-sm text-muted-foreground">
                The backend will parse, enrich, embed, and store the paper.
              </p>
            </div>
          </div>

          <Input
            ref={inputRef}
            type="file"
            accept=".pdf,application/pdf"
            disabled={isIngesting}
            onChange={handleFileChange}
          />

          {selectedFile && (
            <div className="rounded-lg bg-muted p-3 text-sm">
              <p className="font-medium">{selectedFile.name}</p>

              <p className="mt-1 text-xs text-muted-foreground">
                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          )}

          {overwrite && (
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm">
              This paper already exists. Uploading with overwrite will replace
              its Qdrant vectors and stored assets.
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          <div className="flex flex-wrap gap-2">
            {isIngesting ? (
              <Button type="button" variant="outline" onClick={stopIngestion}>
                Stop ingestion
              </Button>
            ) : (
              <Button
                type="button"
                disabled={!selectedFile}
                onClick={() => void beginIngestion(overwrite)}
              >
                <Upload className="h-4 w-4" />

                {overwrite ? "Overwrite and ingest" : "Upload and ingest"}
              </Button>
            )}
          </div>
        </section>

        <IngestionProgress
          eventType={ingestionEventType}
          data={ingestionData}
          fileName={selectedFile?.name}
        />

        <section className="space-y-4">
          <div className="flex items-end justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold">Available papers</h2>

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
                  Upload your first research paper to begin.
                </p>
              </div>
            )}

          <div className="grid gap-4">
            {documents.map((document) => (
              <DocumentCard
                key={document.id}
                document={document}
                selected={selectedPaperName === document.paper_name}
                deleting={
                  deleteMutation.isPending &&
                  deleteMutation.variables === document.paper_name
                }
                onSelect={() => selectPaper(document.paper_name)}
                onDelete={() => void handleDelete(document.paper_name)}
                onReingest={() => handleReingest(document.paper_name)}
              />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
