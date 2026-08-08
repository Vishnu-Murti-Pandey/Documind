import { Skeleton } from "@/components/ui/skeleton";

export default function ChatLoading() {
  return <div className="flex h-full flex-col"><div className="flex h-14 items-center border-b px-5"><Skeleton className="h-5 w-56" /></div><div className="mx-auto w-full max-w-4xl flex-1 space-y-8 px-4 py-8"><Skeleton className="ml-auto h-16 w-2/3" /><Skeleton className="h-40 w-full" /><Skeleton className="ml-auto h-12 w-1/2" /></div><div className="border-t p-4"><Skeleton className="mx-auto h-24 max-w-4xl rounded-2xl" /></div></div>;
}
