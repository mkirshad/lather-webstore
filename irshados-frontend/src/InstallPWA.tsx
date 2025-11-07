import { CSSProperties, useEffect, useState } from "react"

type InstallOutcome = "accepted" | "dismissed"

interface InstallPWAProps {
    deferredPrompt: BeforeInstallPromptEvent | null
    onInstallChoice?: (outcome: InstallOutcome) => void
    onDismiss?: () => void
}

const containerStyles: CSSProperties = {
    position: "fixed",
    bottom: "24px",
    right: "24px",
    maxWidth: "320px",
    padding: "16px 20px",
    background: "#0b1a33",
    color: "#ffffff",
    borderRadius: "12px",
    boxShadow: "0 12px 24px rgba(0, 0, 0, 0.25)",
    display: "flex",
    flexDirection: "column",
    gap: "12px",
    zIndex: 1000,
}

const primaryButtonStyles: CSSProperties = {
    padding: "10px 16px",
    backgroundColor: "#00b4d8",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    fontWeight: 600,
    cursor: "pointer",
    transition: "background-color 0.2s ease",
}

const secondaryButtonStyles: CSSProperties = {
    background: "transparent",
    color: "#c3dafe",
    border: "none",
    fontSize: "0.85rem",
    textDecoration: "underline",
    cursor: "pointer",
    alignSelf: "flex-start",
    marginTop: "8px",
}

const InstallPWA = ({ deferredPrompt, onInstallChoice, onDismiss }: InstallPWAProps) => {
    const [isVisible, setIsVisible] = useState(Boolean(deferredPrompt))

    useEffect(() => {
        setIsVisible(Boolean(deferredPrompt))
    }, [deferredPrompt])

    if (!deferredPrompt || !isVisible) {
        return null
    }

    const handleInstall = async () => {
        try {
            await deferredPrompt.prompt()
            const choiceResult = await deferredPrompt.userChoice
            onInstallChoice?.(choiceResult.outcome)
        } catch (error) {
            console.error("[PWA] Unable to show install prompt", error)
            onInstallChoice?.("dismissed")
        } finally {
            setIsVisible(false)
        }
    }

    const handleDismiss = () => {
        setIsVisible(false)
        onDismiss?.()
    }

    return (
        <aside style={containerStyles} role="dialog" aria-live="polite" aria-label="Install the application">
            <div>
                <h3 style={{ fontSize: "1.1rem", margin: 0 }}>Install IrshadOS</h3>
                <p style={{ fontSize: "0.9rem", margin: "6px 0 0" }}>
                    Get faster access, offline support, and a native-like experience by installing the app.
                </p>
            </div>
            <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
                <button type="button" onClick={handleInstall} style={primaryButtonStyles}>
                    📲 Install App
                </button>
                <button type="button" onClick={handleDismiss} style={secondaryButtonStyles}>
                    Maybe later
                </button>
            </div>
        </aside>
    )
}

export default InstallPWA
