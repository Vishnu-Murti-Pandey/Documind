"use client";

import { Laptop, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

type ThemeToggleProps = {
  showLabel?: boolean;
};

export function ThemeToggle({ showLabel = false }: ThemeToggleProps) {
  const { setTheme, theme } = useTheme();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            type="button"
            variant="ghost"
            size={showLabel ? "default" : "icon"}
            className={cn(showLabel && "w-full justify-start")}
            aria-label="Change color theme"
          />
        }
      >
        <Sun className="h-4 w-4 dark:hidden" />
        <Moon className="hidden h-4 w-4 dark:block" />
        {showLabel && (
          <span className="flex min-w-0 flex-1 items-center justify-between gap-2">
            <span>Theme</span>
            <span className="truncate text-xs capitalize text-muted-foreground">
              {theme ?? "system"}
            </span>
          </span>
        )}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setTheme("light")}><Sun /> Light</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("dark")}><Moon /> Dark</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme("system")}><Laptop /> System</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
