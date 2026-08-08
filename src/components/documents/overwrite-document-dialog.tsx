"use client";

import { RefreshCw, TriangleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

type OverwriteDocumentDialogProps = {
  open: boolean;
  pending: boolean;
  fileName?: string;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
};

export function OverwriteDocumentDialog({
  open,
  pending,
  fileName,
  onOpenChange,
  onConfirm,
}: OverwriteDocumentDialogProps) {
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
          <DialogTitle>Replace existing document?</DialogTitle>

          <DialogDescription>
            A document with this name already exists. Continuing will
            delete its existing vectors and assets before ingesting the uploaded
            PDF again.
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
          <TriangleAlert className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />

          <div className="min-w-0">
            <p className="text-sm font-medium">
              Existing indexed data will be replaced
            </p>

            {fileName && (
              <p className="mt-1 truncate text-xs text-muted-foreground">
                {fileName}
              </p>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            disabled={pending}
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>

          <Button type="button" disabled={pending} onClick={onConfirm}>
            <RefreshCw
              className={pending ? "h-4 w-4 animate-spin" : "h-4 w-4"}
            />

            {pending ? "Replacing..." : "Replace and ingest"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
