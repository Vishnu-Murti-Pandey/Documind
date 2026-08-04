"use client";

import {
  FileText,
  MessageSquarePlus,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { ConversationItem } from "@/components/conversations/conversation-item";
import { DeleteConversationDialog } from "@/components/conversations/delete-conversation-dialog";
import { RenameConversationDialog } from "@/components/conversations/rename-conversation-dialog";
import { Button, buttonVariants } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  useConversations,
  useDeleteConversation,
  useRenameConversation,
} from "@/features/conversations/queries";
import type { ConversationItem as ConversationItemType } from "@/features/conversations/types";
import { cn } from "@/lib/utils";

type ConversationSidebarProps = {
  collapsed?: boolean;
  onToggleCollapsed?: () => void;
  onNavigate?: () => void;
};

export function ConversationSidebar({
  collapsed = false,
  onToggleCollapsed,
  onNavigate,
}: ConversationSidebarProps) {
  const router = useRouter();
  const pathname = usePathname();

  const conversationsQuery = useConversations(0, 50);

  const renameMutation = useRenameConversation();

  const deleteMutation = useDeleteConversation();

  const [renameTarget, setRenameTarget] = useState<ConversationItemType | null>(
    null,
  );

  const [deleteTarget, setDeleteTarget] = useState<ConversationItemType | null>(
    null,
  );

  const conversations = useMemo(
    () => conversationsQuery.data?.items ?? [],
    [conversationsQuery.data],
  );

  function handleRename(title: string) {
    if (!renameTarget) {
      return;
    }

    renameMutation.mutate(
      {
        conversationId: renameTarget.conversation_id,
        title,
      },
      {
        onSuccess: () => {
          setRenameTarget(null);
        },
      },
    );
  }

  function handleDelete() {
    if (!deleteTarget) {
      return;
    }

    const deletedConversationId = deleteTarget.conversation_id;

    deleteMutation.mutate(deletedConversationId, {
      onSuccess: () => {
        setDeleteTarget(null);

        if (pathname === `/chat/${deletedConversationId}`) {
          router.replace("/chat");
        }
      },
    });
  }

  const newChatLink = (
    <Link
      href="/chat"
      onClick={onNavigate}
      className={cn(
        buttonVariants({
          variant: "default",
        }),
        "w-full",
        collapsed ? "justify-center px-0" : "justify-start",
      )}
      aria-label="New chat"
    >
      <MessageSquarePlus className="h-4 w-4" />

      {!collapsed && <span>New chat</span>}
    </Link>
  );

  const documentsLink = (
    <Link
      href="/documents"
      onClick={onNavigate}
      className={cn(
        buttonVariants({
          variant: "ghost",
        }),
        "w-full",
        collapsed ? "justify-center px-0" : "justify-start",
      )}
      aria-label="Documents"
    >
      <FileText className="h-4 w-4" />

      {!collapsed && <span>Documents</span>}
    </Link>
  );

  return (
    <>
      <aside
        className={cn(
          "flex h-full flex-col border-r bg-muted/30 transition-[width] duration-200",
          collapsed ? "w-[72px]" : "w-[280px]",
        )}
      >
        <div
          className={cn(
            "flex h-16 items-center gap-2 px-3",
            collapsed ? "justify-center" : "justify-between",
          )}
        >
          {!collapsed && (
            <Link
              href="/chat"
              onClick={onNavigate}
              className="text-lg font-semibold tracking-tight"
            >
              DocuMind
            </Link>
          )}

          {onToggleCollapsed && (
            <Tooltip>
              <TooltipTrigger
                render={
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={onToggleCollapsed}
                    aria-label={
                      collapsed ? "Expand sidebar" : "Collapse sidebar"
                    }
                  />
                }
              >
                {collapsed ? (
                  <PanelLeftOpen className="h-5 w-5" />
                ) : (
                  <PanelLeftClose className="h-5 w-5" />
                )}
              </TooltipTrigger>

              <TooltipContent side="right">
                {collapsed ? "Expand sidebar" : "Collapse sidebar"}
              </TooltipContent>
            </Tooltip>
          )}
        </div>

        <div className="px-3 pb-3">
          {collapsed ? (
            <Tooltip>
              <TooltipTrigger render={newChatLink} />

              <TooltipContent side="right">New chat</TooltipContent>
            </Tooltip>
          ) : (
            newChatLink
          )}
        </div>

        <Separator />

        <div className="flex min-h-0 flex-1 flex-col">
          {!collapsed && (
            <div className="px-4 pb-2 pt-4 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Recent conversations
            </div>
          )}

          <ScrollArea className="min-h-0 flex-1 px-2">
            <div className="space-y-1 py-2">
              {conversationsQuery.isLoading &&
                Array.from({
                  length: 6,
                }).map((_, index) => (
                  <Skeleton key={index} className="h-9 w-full" />
                ))}

              {conversationsQuery.isError && !collapsed && (
                <div className="px-3 py-4 text-sm text-destructive">
                  Could not load conversations.
                </div>
              )}

              {!conversationsQuery.isLoading &&
                !conversationsQuery.isError &&
                conversations.length === 0 &&
                !collapsed && (
                  <div className="px-3 py-4 text-sm text-muted-foreground">
                    No conversations yet.
                  </div>
                )}

              {conversations.map((conversation) => (
                <ConversationItem
                  key={conversation.conversation_id}
                  conversation={conversation}
                  collapsed={collapsed}
                  onRename={setRenameTarget}
                  onDelete={setDeleteTarget}
                  onNavigate={onNavigate}
                />
              ))}
            </div>
          </ScrollArea>
        </div>

        <Separator />

        <div className="p-3">
          {collapsed ? (
            <Tooltip>
              <TooltipTrigger render={documentsLink} />

              <TooltipContent side="right">Documents</TooltipContent>
            </Tooltip>
          ) : (
            documentsLink
          )}
        </div>
      </aside>

      <RenameConversationDialog
        conversation={renameTarget}
        open={Boolean(renameTarget)}
        pending={renameMutation.isPending}
        onOpenChange={(open) => {
          if (!open) {
            setRenameTarget(null);
          }
        }}
        onSubmit={handleRename}
      />

      <DeleteConversationDialog
        conversation={deleteTarget}
        open={Boolean(deleteTarget)}
        pending={deleteMutation.isPending}
        onOpenChange={(open) => {
          if (!open) {
            setDeleteTarget(null);
          }
        }}
        onConfirm={handleDelete}
      />
    </>
  );
}
