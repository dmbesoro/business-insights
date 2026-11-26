import { create } from "zustand";

interface UIState {
  isUploadPanelOpen: boolean;
  openUploadPanel: () => void;
  closeUploadPanel: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  isUploadPanelOpen: false,

  openUploadPanel: () => set({ isUploadPanelOpen: true }),

  closeUploadPanel: () => set({ isUploadPanelOpen: false }),
}));
