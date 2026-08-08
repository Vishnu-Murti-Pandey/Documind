"use client";

import { FileText, ImageIcon } from "lucide-react";
import { useState } from "react";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { FigurePreviewDialog } from "@/components/chat/figure-preview-dialog";
import type { Citation, FigureReference } from "@/features/chat/types";

export function CitationAccordion({ citations, figures }: { citations: Citation[]; figures: FigureReference[] }) {
  const [preview, setPreview] = useState<FigureReference | null>(null);
  if (!citations.length) return null;
  return (
    <>
      <Accordion className="mt-4 rounded-xl border px-3">
        <AccordionItem value="sources" className="border-0">
          <AccordionTrigger className="py-3">Sources ({citations.length})</AccordionTrigger>
          <AccordionContent className="space-y-1 pb-3">
            {citations.map((citation, index) => {
              const figure = citation.type === "figure" ? figures.find((item) => item.chunk_id === citation.chunk_id) : undefined;
              const pages = citation.page_start === citation.page_end ? `page ${citation.page_start}` : `pages ${citation.page_start}–${citation.page_end}`;
              const content = <><span className="mt-0.5 shrink-0">{citation.type === "figure" ? <ImageIcon className="h-4 w-4" /> : <FileText className="h-4 w-4" />}</span><span className="min-w-0"><span className="block font-medium">{citation.caption || citation.section_title}</span><span className="block text-xs text-muted-foreground">{citation.section_title} · {pages}</span></span></>;
              return figure ? <button type="button" key={`${citation.chunk_id}-${index}`} onClick={() => setPreview(figure)} className="flex w-full gap-3 rounded-lg p-2 text-left hover:bg-muted">{content}</button> : <div key={`${citation.chunk_id}-${index}`} className="flex gap-3 rounded-lg p-2">{content}</div>;
            })}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
      <FigurePreviewDialog figure={preview} open={Boolean(preview)} onOpenChange={(open) => !open && setPreview(null)} />
    </>
  );
}
