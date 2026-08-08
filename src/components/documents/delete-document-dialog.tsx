"use client";

import { FileText, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import type { DocumentItem } from "@/features/documents/types";

type DeleteDocumentDialogProps = {
  document: DocumentItem | null;
  open: boolean;
  pending: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
};

export function DeleteDocumentDialog({
  document,
  open,
  pending,
  onOpenChange,
  onConfirm,
}: DeleteDocumentDialogProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!pending) {
          onOpenChange(nextOpen);
        }
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete document?</DialogTitle>

          <DialogDescription>
            This permanently removes the document record, Qdrant vectors, and
            stored image assets. Existing conversation history will remain
            available.
          </DialogDescription>
        </DialogHeader>

        {document && (
          <div className="flex items-start gap-3 rounded-xl border bg-muted/40 p-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-background">
              <FileText className="h-5 w-5" />
            </div>

            <div className="min-w-0">
              <p className="truncate text-sm font-medium">
                {document.original_filename}
              </p>

              <p className="mt-1 truncate text-xs text-muted-foreground">
                {document.paper_name}
              </p>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            disabled={pending}
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>

          <Button
            type="button"
            variant="destructive"
            disabled={pending}
            onClick={onConfirm}
          >
            <Trash2 className="h-4 w-4" />

            {pending ? "Deleting..." : "Delete permanently"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
