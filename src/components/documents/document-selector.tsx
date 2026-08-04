"use client";

import { BookOpen, ChevronDown } from "lucide-react";

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

export function DocumentSelector() {
  const documentsQuery = useDocuments(0, 50);

  const selectedPaperName = useDocumentSelectionStore(
    (state) => state.selectedPaperName,
  );

  const selectPaper = useDocumentSelectionStore((state) => state.selectPaper);

  if (documentsQuery.isLoading) {
    return <Skeleton className="h-8 w-44" />;
  }

  const documents =
    documentsQuery.data?.items.filter(
      (document) => document.status === "completed",
    ) ?? [];

  const selectedDocument = documents.find(
    (document) => document.paper_name === selectedPaperName,
  );

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            type="button"
            size="sm"
            variant="ghost"
            className="max-w-[240px]"
          />
        }
      >
        <BookOpen className="h-4 w-4 shrink-0" />

        <span className="truncate">
          {selectedDocument?.original_filename || "Select document"}
        </span>

        <ChevronDown className="h-4 w-4 shrink-0" />
      </DropdownMenuTrigger>

      <DropdownMenuContent align="start" className="w-72">
        {documents.length === 0 && (
          <DropdownMenuItem disabled>No completed documents</DropdownMenuItem>
        )}

        {documents.map((document) => (
          <DropdownMenuItem
            key={document.id}
            onClick={() => selectPaper(document.paper_name)}
          >
            <div className="min-w-0">
              <p className="truncate text-sm">{document.original_filename}</p>

              <p className="truncate text-xs text-muted-foreground">
                {document.paper_name}
              </p>
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
