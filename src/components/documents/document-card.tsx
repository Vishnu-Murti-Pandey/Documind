"use client";

import {
  Check,
  FileText,
  RefreshCw,
  Trash2,
  TriangleAlert,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import type { DocumentItem } from "@/features/documents/types";

type DocumentCardProps = {
  document: DocumentItem;
  selected: boolean;
  deleting: boolean;

  onSelect: () => void;
  onDelete: () => void;
  onReingest: () => void;
};

function formatBytes(bytes: number): string {
  if (bytes === 0) {
    return "0 B";
  }

  const units = ["B", "KB", "MB", "GB"];

  const index = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  );

  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 1)} ${
    units[index]
  }`;
}

export function DocumentCard({
  document,
  selected,
  deleting,
  onSelect,
  onDelete,
  onReingest,
}: DocumentCardProps) {
  const completed = document.status === "completed";

  const failed = document.status === "failed";

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
              <h3 className="truncate font-medium">
                {document.original_filename}
              </h3>

              <p className="mt-1 truncate text-xs text-muted-foreground">
                {document.paper_name}
              </p>
            </div>

            <Badge
              variant={
                completed ? "secondary" : failed ? "destructive" : "outline"
              }
            >
              {document.status}
            </Badge>
          </div>

          <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-muted-foreground">
            <span>{formatBytes(document.file_size_bytes)}</span>

            <span>{document.chunks_count ?? 0} chunks</span>

            <span>
              Updated {new Date(document.updated_at).toLocaleString()}
            </span>
          </div>

          {document.error_message && (
            <div className="mt-3 flex gap-2 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" />

              <p>{document.error_message}</p>
            </div>
          )}

          <div className="mt-5 flex flex-wrap gap-2">
            <Button
              type="button"
              size="sm"
              variant={selected ? "default" : "outline"}
              disabled={!completed}
              onClick={onSelect}
            >
              {selected && <Check className="h-4 w-4" />}

              {selected ? "Selected" : "Use in chat"}
            </Button>

            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={onReingest}
            >
              <RefreshCw className="h-4 w-4" />
              Re-ingest
            </Button>

            <Button
              type="button"
              size="sm"
              variant="ghost"
              disabled={deleting}
              className="text-destructive hover:text-destructive"
              onClick={onDelete}
            >
              <Trash2 className="h-4 w-4" />

              {deleting ? "Deleting..." : "Delete"}
            </Button>
          </div>
        </div>
      </div>
    </article>
  );
}
