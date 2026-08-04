import { create } from "zustand";

type SidebarState = {
  mobileOpen: boolean;
  desktopCollapsed: boolean;

  setMobileOpen: (open: boolean) => void;

  toggleDesktopCollapsed: () => void;
};

export const useSidebarStore = create<SidebarState>((set) => ({
  mobileOpen: false,
  desktopCollapsed: false,

  setMobileOpen: (open) =>
    set({
      mobileOpen: open,
    }),

  toggleDesktopCollapsed: () =>
    set((state) => ({
      desktopCollapsed: !state.desktopCollapsed,
    })),
}));
