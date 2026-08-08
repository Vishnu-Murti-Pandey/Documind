"use client";
import { CircleAlert } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ChatError({ reset }: { error: Error; reset: () => void }) {
  return <div className="flex h-full items-center justify-center p-6"><div className="max-w-md text-center"><CircleAlert className="mx-auto h-8 w-8 text-destructive" /><h2 className="mt-4 text-lg font-semibold">Could not open this conversation</h2><p className="mt-2 text-sm text-muted-foreground">The conversation or its messages could not be loaded.</p><Button className="mt-5" onClick={reset}>Try again</Button></div></div>;
}
