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
      <Accordion className="mt-5 overflow-hidden rounded-2xl border border-border/70 bg-card/70 px-4 shadow-[0_1px_2px_rgb(40_30_20/0.03)]">
        <AccordionItem value="sources" className="border-0">
          <AccordionTrigger className="py-3.5 text-[12px] font-semibold uppercase tracking-[0.08em] text-muted-foreground hover:no-underline">Sources <span className="ml-1 rounded-full bg-muted px-2 py-0.5 text-[10px]">{citations.length}</span></AccordionTrigger>
          <AccordionContent className="space-y-1 pb-3">
            {citations.map((citation, index) => {
              const figure = citation.type === "figure" ? figures.find((item) => item.chunk_id === citation.chunk_id) : undefined;
              const pages = citation.page_start === citation.page_end ? `page ${citation.page_start}` : `pages ${citation.page_start}–${citation.page_end}`;
              const content = <><span className="mt-0.5 shrink-0">{citation.type === "figure" ? <ImageIcon className="h-4 w-4" /> : <FileText className="h-4 w-4" />}</span><span className="min-w-0"><span className="block font-medium">{citation.caption || citation.section_title}</span><span className="block text-xs text-muted-foreground">{citation.section_title} · {pages}</span></span></>;
              return figure ? <button type="button" key={`${citation.chunk_id}-${index}`} onClick={() => setPreview(figure)} className="flex w-full gap-3 rounded-xl p-2.5 text-left transition-colors hover:bg-muted">{content}</button> : <div key={`${citation.chunk_id}-${index}`} className="flex gap-3 rounded-xl p-2.5">{content}</div>;
            })}
          </AccordionContent>
        </AccordionItem>
      </Accordion>
      <FigurePreviewDialog figure={preview} open={Boolean(preview)} onOpenChange={(open) => !open && setPreview(null)} />
    </>
  );
}
