"use client";

import { BookOpen, Check, ChevronDown } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";

import { useDocumentSelectionStore } from "@/features/documents/document-store";
import { useDocuments } from "@/features/documents/queries";

type DocumentSelectorProps = {
  disabled?: boolean;
  paperName?: string | null;
  sourceLoading?: boolean;
};

export function DocumentSelector({
  disabled = false,
  paperName,
  sourceLoading = false,
}: DocumentSelectorProps) {
  const documentsQuery = useDocuments(0, 50);

  const selectedPaperName = useDocumentSelectionStore(
    (state) => state.selectedPaperName,
  );

  const selectPaper = useDocumentSelectionStore((state) => state.selectPaper);
  const effectivePaperName = paperName === undefined ? selectedPaperName : paperName;

  if (documentsQuery.isLoading || sourceLoading) {
    return <Skeleton className="h-8 w-44" />;
  }

  const documents =
    documentsQuery.data?.items.filter(
      (document) => document.status === "completed",
    ) ?? [];

  const selectedDocument = documents.find(
    (document) => document.paper_name === effectivePaperName,
  );

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            type="button"
            size="sm"
            variant="secondary"
            className="max-w-[min(280px,68vw)] rounded-xl border-0 bg-muted/70 px-3 text-[11px] font-semibold shadow-none hover:bg-muted"
            disabled={disabled}
            aria-label="Select document"
          />
        }
      >
        <BookOpen className="h-4 w-4 shrink-0" />

        <span className="truncate">
          {selectedDocument?.original_filename ||
            effectivePaperName ||
            "Select document"}
        </span>

        {!disabled && <ChevronDown className="h-4 w-4 shrink-0" />}
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" className="w-[min(20rem,calc(100vw-1rem))]">
        {documents.length === 0 && (
          <DropdownMenuItem disabled>No completed documents</DropdownMenuItem>
        )}

        {documents.map((document) => {
          const selected = document.paper_name === effectivePaperName;

          return (
            <DropdownMenuItem
              key={document.id}
              onClick={() => selectPaper(document.paper_name)}
            >
              <div className="flex min-w-0 flex-1 items-center gap-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm">
                    {document.original_filename}
                  </p>

                  <p className="truncate text-xs text-muted-foreground">
                    {document.paper_name}
                  </p>
                </div>

                {selected && <Check className="h-4 w-4 shrink-0" />}
              </div>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
