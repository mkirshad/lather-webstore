import { create } from 'zustand'

type HelpState = {
    isOpen: boolean
    topicKey: string | null
    open: (topicKey?: string | null) => void
    close: () => void
    setTopic: (topicKey: string | null) => void
}

export const useHelpStore = create<HelpState>((set) => ({
    isOpen: false,
    topicKey: null,
    open: (topicKey) =>
        set({
            isOpen: true,
            topicKey: typeof topicKey === 'undefined' ? null : topicKey,
        }),
    close: () => set({ isOpen: false }),
    setTopic: (topicKey) => set({ topicKey }),
}))
