import type { TableReference } from "@/features/chat/types";

export function TableGallery({ tables }: { tables: TableReference[] }) {
  if (!tables.length) return null;
  return (
    <div className="mt-5 min-w-0 space-y-4">
      {tables.map((table, index) => (
        <div key={`${table.chunk_id}-${index}`} className="min-w-0 overflow-hidden rounded-xl border">
          {table.summary && <p className="border-b bg-muted/30 p-3 text-sm text-muted-foreground">{table.summary}</p>}
          <div className="max-w-full overflow-x-auto p-4"><div className="prose prose-sm min-w-max max-w-none dark:prose-invert" dangerouslySetInnerHTML={{ __html: table.html }} /></div>
        </div>
      ))}
    </div>
  );
}
