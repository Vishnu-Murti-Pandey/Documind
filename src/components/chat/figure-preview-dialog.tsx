"use client";

import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import type { FigureReference } from "@/features/chat/types";
import Image from "next/image";

export function FigurePreviewDialog({ figure, open, onOpenChange }: { figure: FigureReference | null; open: boolean; onOpenChange: (open: boolean) => void }) {
  if (!figure) return null;
  const pages = figure.page_start === figure.page_end ? `Page ${figure.page_start}` : `Pages ${figure.page_start}–${figure.page_end}`;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[calc(100dvh-1rem)] max-w-[calc(100vw-1rem)] gap-4 overflow-y-auto p-4 sm:max-w-5xl sm:p-6">
        <DialogHeader>
          <DialogTitle>{figure.caption || "Figure preview"}</DialogTitle>
          <DialogDescription>{figure.paper_name} · {figure.section_title} · {pages}</DialogDescription>
        </DialogHeader>
        <div className="flex min-h-0 justify-center rounded-xl bg-muted/40 p-2">
          <Image unoptimized width={1600} height={1000} src={`${process.env.NEXT_PUBLIC_API_URL}${figure.image_url}`} alt={figure.caption || figure.section_title} className="h-auto max-h-[72dvh] w-auto max-w-full object-contain" />
        </div>
      </DialogContent>
    </Dialog>
  );
}
