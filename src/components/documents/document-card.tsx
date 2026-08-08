"use client";

import {
  Check,
  CircleAlert,
  Clock3,
  FileText,
  LoaderCircle,
  RefreshCw,
  Trash2,
  TriangleAlert,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import type { DocumentItem, DocumentStatus } from "@/features/documents/types";

type DocumentCardProps = {
  document: DocumentItem;
  selected: boolean;
  deleting: boolean;
  controlsDisabled?: boolean;

  onSelect: () => void;
  onDelete: () => void;
  onReingest: () => void;
};

function formatBytes(bytes: number): string {
  if (bytes <= 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];

  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );

  const value = bytes / 1024 ** index;

  return `${value.toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function getStatusConfig(status: DocumentStatus) {
  switch (status) {
    case "completed":
      return {
        label: "Completed",
        icon: Check,
        className:
          "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400",
      };

    case "processing":
      return {
        label: "Processing",
        icon: LoaderCircle,
        className:
          "border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-400",
      };

    case "failed":
      return {
        label: "Failed",
        icon: CircleAlert,
        className: "border-destructive/30 bg-destructive/10 text-destructive",
      };

    case "pending":
    default:
      return {
        label: "Pending",
        icon: Clock3,
        className:
          "border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-400",
      };
  }
}

export function DocumentCard({
  document,
  selected,
  deleting,
  controlsDisabled = false,
  onSelect,
  onDelete,
  onReingest,
}: DocumentCardProps) {
  const completed = document.status === "completed";

  const failed = document.status === "failed";

  const processing = document.status === "processing";

  const statusConfig = getStatusConfig(document.status);

  const StatusIcon = statusConfig.icon;

  const actionsDisabled = controlsDisabled || deleting || processing;
  const deleteDisabled = controlsDisabled || deleting;

  return (
    <article
      className={cn(
        "rounded-xl border bg-card p-5 transition-colors",
        selected && "border-primary ring-1 ring-primary",
      )}
    >
      <div className="flex items-start gap-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-muted">
          <FileText className="h-5 w-5" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <h3
                className="truncate font-medium"
                title={document.original_filename}
              >
                {document.original_filename}
              </h3>

              <p
                className="mt-1 truncate text-xs text-muted-foreground"
                title={document.paper_name}
              >
                {document.paper_name}
              </p>
            </div>

            <Badge
              variant="outline"
              className={cn("gap-1.5", statusConfig.className)}
            >
              <StatusIcon
                className={cn("h-3.5 w-3.5", processing && "animate-spin")}
              />

              {statusConfig.label}
            </Badge>
          </div>

          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted-foreground">
            <span>{formatBytes(document.file_size_bytes)}</span>

            <span>{document.chunks_count ?? 0} chunks</span>

            <span>{document.elements_count ?? 0} elements</span>

            <span>
              Updated {new Date(document.updated_at).toLocaleString()}
            </span>
          </div>

          {document.error_message && (
            <div className="mt-4 flex gap-2 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />

              <p className="break-words">{document.error_message}</p>
            </div>
          )}

          {processing && (
            <p className="mt-4 text-sm text-muted-foreground">
              This document is currently being processed.
            </p>
          )}

          <div className="mt-5 flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              variant={selected ? "default" : "outline"}
              disabled={!completed || actionsDisabled}
              onClick={onSelect}
            >
              {selected && <Check className="h-4 w-4" />}

              {selected ? "Selected" : "Use in chat"}
            </Button>

            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={actionsDisabled}
              onClick={onReingest}
            >
              <RefreshCw className="h-4 w-4" />

              {failed ? "Retry ingestion" : "Re-ingest"}
            </Button>

            <Button
              type="button"
              size="sm"
              variant="ghost"
              disabled={deleteDisabled}
              className="text-destructive hover:text-destructive"
              onClick={onDelete}
            >
              {deleting ? (
                <LoaderCircle className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}

              {deleting ? "Deleting..." : "Delete"}
            </Button>
          </div>
        </div>
      </div>
    </article>
  );
}
