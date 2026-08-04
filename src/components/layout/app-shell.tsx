"use client";

import { Menu } from "lucide-react";
import type { ReactNode } from "react";

import { ConversationSidebar } from "@/components/conversations/conversation-sidebar";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";

import { useSidebarStore } from "./sidebar-store";

type AppShellProps = {
  children: ReactNode;
};

export function AppShell({ children }: AppShellProps) {
  const {
    mobileOpen,
    desktopCollapsed,
    setMobileOpen,
    toggleDesktopCollapsed,
  } = useSidebarStore();

  return (
    <div className="flex h-dvh overflow-hidden bg-background">
      <div className="hidden lg:block">
        <ConversationSidebar
          collapsed={desktopCollapsed}
          onToggleCollapsed={toggleDesktopCollapsed}
        />
      </div>

      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="left" className="w-[300px] p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>

          <ConversationSidebar onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center border-b px-4 lg:hidden">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" />
          </Button>

          <span className="ml-3 font-semibold">DocuMind</span>
        </header>

        <main className="min-h-0 flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}
