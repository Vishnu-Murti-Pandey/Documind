"use client";

import {
  CheckCircle2,
  CircleX,
  LoaderCircle,
  RotateCcw,
  Square,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

import type {
  IngestionEventData,
  IngestionEventType,
} from "@/features/documents/types";

type IngestionProgressProps = {
  eventType: IngestionEventType | null;
  data: IngestionEventData | null;
  fileName?: string;
  isIngesting?: boolean;
  canRetry?: boolean;

  onStop?: () => void;
  onRetry?: () => void;
};

export function IngestionProgress({
  eventType,
  data,
  fileName,
  isIngesting = false,
  canRetry = false,
  onStop,
  onRetry,
}: IngestionProgressProps) {
  if (!eventType || !data) {
    return null;
  }

  const progress = Math.min(Math.max(data.progress ?? 0, 0), 100);

  const completed = eventType === "completed";

  const failed = eventType === "error";

  return (
    <div className="space-y-4 rounded-xl border bg-card p-5">
      <div className="flex items-start gap-3">
        {completed ? (
          <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-600" />
        ) : failed ? (
          <CircleX className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
        ) : (
          <LoaderCircle className="mt-0.5 h-5 w-5 shrink-0 animate-spin text-primary" />
        )}

        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium">
            {fileName || data.paper_name || "PDF document"}
          </p>

          <p className="mt-1 text-sm text-muted-foreground">
            {data.message || "Processing document..."}
          </p>
        </div>

        <span className="text-sm font-medium tabular-nums">
          {Math.round(progress)}%
        </span>
      </div>

      <Progress value={progress} />

      {typeof data.current_chunk === "number" &&
        typeof data.total_chunks === "number" && (
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>
              Chunk {data.current_chunk} of {data.total_chunks}
            </span>

            {data.chunk_id && (
              <span className="max-w-52 truncate">{data.chunk_id}</span>
            )}
          </div>
        )}

      {completed && (
        <div className="grid gap-3 text-sm sm:grid-cols-3">
          <div className="rounded-lg bg-muted p-3">
            <p className="text-xs text-muted-foreground">Elements</p>

            <p className="mt-1 font-medium">{data.elements_count ?? 0}</p>
          </div>

          <div className="rounded-lg bg-muted p-3">
            <p className="text-xs text-muted-foreground">Chunks</p>

            <p className="mt-1 font-medium">{data.chunks_stored ?? 0}</p>
          </div>

          <div className="rounded-lg bg-muted p-3">
            <p className="text-xs text-muted-foreground">Duration</p>

            <p className="mt-1 font-medium">{data.elapsed_seconds ?? 0}s</p>
          </div>
        </div>
      )}

      {failed && (
        <div className="space-y-3">
          <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {data.detail || data.message || "Document ingestion failed."}
          </p>

          {canRetry && onRetry && (
            <Button type="button" size="sm" variant="outline" onClick={onRetry}>
              <RotateCcw className="h-4 w-4" />
              Retry ingestion
            </Button>
          )}
        </div>
      )}

      {isIngesting && onStop && (
        <Button type="button" size="sm" variant="outline" onClick={onStop}>
          <Square className="h-4 w-4" />
          Stop ingestion
        </Button>
      )}
    </div>
  );
}
