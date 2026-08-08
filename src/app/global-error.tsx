"use client";
import { Button } from "@/components/ui/button";
export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) { return <html><body className="flex min-h-screen items-center justify-center bg-background p-6 text-foreground"><main className="text-center"><h1 className="text-xl font-semibold">Something went wrong</h1><p className="mt-2 text-sm text-muted-foreground">DocuMind hit an unexpected error.</p><Button className="mt-5" onClick={reset}>Try again</Button></main></body></html>; }
