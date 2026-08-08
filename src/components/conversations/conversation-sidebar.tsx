"use client";

import {
  FileText,
  LibraryBig,
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
import { toast } from "sonner";
import { ThemeToggle } from "@/components/layout/theme-toggle";

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
          toast.success("Conversation renamed");
        },
        onError: (error) => toast.error(error instanceof Error ? error.message : "Could not rename conversation."),
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
        toast.success("Conversation deleted");

        if (pathname === `/chat/${deletedConversationId}`) {
          router.replace("/chat");
        }
      },
      onError: (error) => toast.error(error instanceof Error ? error.message : "Could not delete conversation."),
    });
  }

  const newChatLink = (
    <Link
      href="/chat"
      onClick={() => {
        if (pathname.startsWith("/chat")) {
          window.dispatchEvent(new Event("documind:new-chat"));
        }
        onNavigate?.();
      }}
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
          "flex h-full flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground transition-[width] duration-300 ease-out",
          collapsed ? "w-[72px]" : "w-[292px]",
        )}
      >
        <div
          className={cn(
            "flex h-[72px] items-center gap-2 px-3",
            collapsed ? "justify-center" : "justify-between",
          )}
        >
          {!collapsed && (
            <Link
              href="/chat"
              onClick={onNavigate}
              className="flex items-center gap-2.5 px-1 text-[15px] font-semibold tracking-[-0.025em]"
            >
              <span className="flex size-8 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm"><LibraryBig className="size-4" /></span>
              <span>DocuMind</span>
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

        <div className="px-3 pb-4">
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
            <div className="px-4 pb-2 pt-5 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
              Workspace
            </div>
          )}

          <ScrollArea className="min-h-0 flex-1 px-2">
            <div className="space-y-0.5 py-2">
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

        <div className="flex flex-col items-center gap-1 p-3">
          {collapsed ? (
            <Tooltip>
              <TooltipTrigger render={documentsLink} />

              <TooltipContent side="right">Documents</TooltipContent>
            </Tooltip>
          ) : (
            documentsLink
          )}
          <ThemeToggle showLabel={!collapsed} />
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
