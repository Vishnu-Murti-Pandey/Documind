"use client";

import { ImageIcon } from "lucide-react";
import Image from "next/image";
import { useState } from "react";
import { FigurePreviewDialog } from "@/components/chat/figure-preview-dialog";
import type { FigureReference } from "@/features/chat/types";

export function FigureGallery({ figures }: { figures: FigureReference[] }) {
  const [selected, setSelected] = useState<FigureReference | null>(null);
  if (!figures.length) return null;
  return (
    <>
      <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">
        {figures.map((figure, index) => (
          <button type="button" key={`${figure.chunk_id}-${index}`} onClick={() => setSelected(figure)} className="overflow-hidden rounded-xl border bg-card text-left transition-colors hover:bg-muted/30 focus-visible:ring-2 focus-visible:ring-ring">
            <Image unoptimized width={960} height={540} src={`${process.env.NEXT_PUBLIC_API_URL}${figure.image_url}`} alt={figure.caption || `Figure ${index + 1}`} className="aspect-video w-full object-contain" />
            <span className="block space-y-1 border-t p-3">
              <span className="flex items-center gap-2 text-sm font-medium"><ImageIcon className="h-4 w-4" />{figure.caption || `Figure ${index + 1}`}</span>
              <span className="line-clamp-2 block text-xs text-muted-foreground">{figure.section_title}</span>
            </span>
          </button>
        ))}
      </div>
      <FigurePreviewDialog figure={selected} open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)} />
    </>
  );
}
