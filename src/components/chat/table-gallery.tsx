import type { TableReference } from "@/features/chat/types";
import { Table2 } from "lucide-react";

function sanitizeTableHtml(html: string): string {
  return html
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, "")
    .replace(/<style\b[^>]*>[\s\S]*?<\/style>/gi, "")
    .replace(/\son\w+\s*=\s*("[^"]*"|'[^']*')/gi, "")
    .replace(/javascript:/gi, "");
}

export function TableGallery({ tables }: { tables: TableReference[] }) {
  if (!tables.length) return null;
  return (
    <div className="mt-5 min-w-0 space-y-4">
      {tables.map((table, index) => (
        <section key={`${table.chunk_id}-${index}`} className="enterprise-panel min-w-0 overflow-hidden">
          <div className="flex items-start gap-3 border-b border-border/60 bg-muted/25 px-4 py-3.5">
            <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary"><Table2 className="size-3.5" /></span>
            <div className="min-w-0"><h4 className="text-[13px] font-semibold">Table {index + 1}</h4>{table.summary && <p className="mt-0.5 text-xs leading-5 text-muted-foreground">{table.summary}</p>}</div>
          </div>
          <div className="max-w-full overflow-x-auto"><div className="answer-prose min-w-max [&_table]:border-0" dangerouslySetInnerHTML={{ __html: sanitizeTableHtml(table.html) }} /></div>
        </section>
      ))}
    </div>
  );
}
