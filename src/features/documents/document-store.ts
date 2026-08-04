import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

type DocumentSelectionState = {
  selectedPaperName: string | null;

  selectPaper: (paperName: string | null) => void;
};

export const useDocumentSelectionStore = create<DocumentSelectionState>()(
  persist(
    (set) => ({
      selectedPaperName: null,

      selectPaper: (paperName) =>
        set({
          selectedPaperName: paperName,
        }),
    }),
    {
      name: "documind-selected-paper",
      storage: createJSONStorage(() => localStorage),
    },
  ),
);
