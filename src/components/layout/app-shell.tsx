"use client";

import { Menu } from "lucide-react";
import type { ReactNode } from "react";

import { ConversationSidebar } from "@/components/conversations/conversation-sidebar";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";

import { useSidebarStore } from "./sidebar-store";
import { ThemeToggle } from "./theme-toggle";

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
    <div className="flex h-dvh overflow-hidden bg-background text-foreground">
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
        <header className="flex h-16 shrink-0 items-center border-b border-border/70 bg-background/85 px-4 backdrop-blur-xl lg:hidden">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => setMobileOpen(true)}
            aria-label="Open navigation"
          >
            <Menu className="h-5 w-5" />
          </Button>

          <span className="ml-3 text-[15px] font-semibold tracking-[-0.02em]">DocuMind</span>
          <div className="ml-auto"><ThemeToggle /></div>
        </header>

        <main className="min-h-0 flex-1 overflow-hidden">{children}</main>
      </div>
    </div>
  );
}
