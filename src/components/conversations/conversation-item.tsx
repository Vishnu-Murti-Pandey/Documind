"use client";

import { MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { ConversationItem as ConversationItemType } from "@/features/conversations/types";
import { cn } from "@/lib/utils";

type ConversationItemProps = {
  conversation: ConversationItemType;
  collapsed?: boolean;
  onRename: (conversation: ConversationItemType) => void;
  onDelete: (conversation: ConversationItemType) => void;
  onNavigate?: () => void;
};

export function ConversationItem({
  conversation,
  collapsed = false,
  onRename,
  onDelete,
  onNavigate,
}: ConversationItemProps) {
  const params = useParams<{
    conversationId?: string;
  }>();

  const isActive = params?.conversationId === conversation.conversation_id;

  const title = conversation.title?.trim() || "Untitled conversation";

  const conversationHref = `/chat/${conversation.conversation_id}`;

  if (collapsed) {
    return (
      <div className="group flex min-w-0 items-center gap-1 rounded-md">
        <Tooltip>
          <TooltipTrigger
            render={
              <Link
                href={conversationHref}
                onClick={onNavigate}
                className={cn(
                  "flex h-10 w-full items-center justify-center rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-accent text-accent-foreground"
                    : "text-muted-foreground hover:bg-accent/60 hover:text-foreground",
                )}
                aria-label={title}
              />
            }
          >
            {title.charAt(0).toUpperCase()}
          </TooltipTrigger>

          <TooltipContent side="right">
            <div className="max-w-64">
              <p className="font-medium">{title}</p>

              {conversation.paper_name && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Source: {conversation.paper_name}
                </p>
              )}
            </div>
          </TooltipContent>
        </Tooltip>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "group flex min-w-0 items-center gap-1 rounded-xl",
        isActive && "bg-sidebar-accent",
      )}
    >
      <Link
        href={conversationHref}
        onClick={onNavigate}
        className={cn(
          "min-w-0 flex-1 rounded-xl px-3 py-2.5 transition-all duration-200",
          isActive
            ? "text-sidebar-accent-foreground"
            : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-sidebar-foreground",
        )}
      >
        <p className="truncate text-[13px] font-medium" title={title}>
          {title}
        </p>

        {conversation.paper_name && (
          <p
            className="mt-0.5 truncate text-[11px] text-muted-foreground"
            title={conversation.paper_name}
          >
            {conversation.paper_name}
          </p>
        )}
      </Link>

      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="mr-1 h-8 w-8 shrink-0 opacity-0 transition-opacity group-hover:opacity-100 data-[popup-open]:opacity-100"
              aria-label={`Actions for ${title}`}
            />
          }
        >
          <MoreHorizontal className="h-4 w-4" />
        </DropdownMenuTrigger>

        <DropdownMenuContent align="end" className="w-40">
          <DropdownMenuItem onClick={() => onRename(conversation)}>
            <Pencil className="mr-2 h-4 w-4" />
            Rename
          </DropdownMenuItem>

          <DropdownMenuItem
            className="text-destructive focus:text-destructive"
            onClick={() => onDelete(conversation)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
