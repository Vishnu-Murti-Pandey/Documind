"use client";

import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

import type { ConversationItem } from "@/features/conversations/types";

type RenameConversationDialogProps = {
  conversation: ConversationItem | null;
  open: boolean;
  pending: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (title: string) => void;
};

export function RenameConversationDialog({
  conversation,
  open,
  pending,
  onOpenChange,
  onSubmit,
}: RenameConversationDialogProps) {
  const [title, setTitle] = useState("");

  useEffect(() => {
    if (conversation) {
      setTitle(conversation.title ?? "");
    }
  }, [conversation]);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalizedTitle = title.trim();

    if (!normalizedTitle) {
      return;
    }

    onSubmit(normalizedTitle);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Rename conversation</DialogTitle>

            <DialogDescription>
              Enter a new title for this conversation.
            </DialogDescription>
          </DialogHeader>

          <div className="py-5">
            <Input
              autoFocus
              value={title}
              maxLength={255}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Conversation title"
            />
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

            <Button type="submit" disabled={pending || !title.trim()}>
              {pending ? "Saving..." : "Save"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
