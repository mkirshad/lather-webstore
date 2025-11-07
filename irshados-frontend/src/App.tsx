import { BrowserRouter, MemoryRouter } from 'react-router'
import { useEffect, useRef, useState, type ReactNode } from 'react'
import Theme from '@/components/template/Theme'
import Layout from '@/components/layouts'
import { AuthProvider } from '@/auth'
import Views from '@/views'
import appConfig from './configs/app.config'
import InstallPWA from './InstallPWA'

if (appConfig.enableMock) {
    import('./mock')
}

const RouterWrapper = ({ children }: { children: ReactNode }) => {
    if (typeof window === 'undefined') {
        return <MemoryRouter initialEntries={['/']}>{children}</MemoryRouter>
    }
    return <BrowserRouter>{children}</BrowserRouter>
}

type InstallOutcome = 'accepted' | 'dismissed'

function App() {
    const [showInstallPrompt, setShowInstallPrompt] = useState(false)
    const [updateAvailable, setUpdateAvailable] = useState(false)
    const deferredPromptRef = useRef<BeforeInstallPromptEvent | null>(null)
    const waitingWorkerRef = useRef<ServiceWorker | null>(null)

    useEffect(() => {
        if (!('serviceWorker' in navigator)) {
            return
        }

        let isMounted = true
        let refreshing = false

        const registerUpdateListeners = async () => {
            try {
                const registration = await navigator.serviceWorker.ready

                if (!isMounted) {
                    return
                }

                if (registration.waiting) {
                    waitingWorkerRef.current = registration.waiting
                    setUpdateAvailable(true)
                }

                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing
                    if (!newWorker) {
                        return
                    }

                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            waitingWorkerRef.current = registration.waiting
                            setUpdateAvailable(true)
                        }
                    })
                })
            } catch (error) {
                console.error('[PWA] Unable to determine service worker readiness', error)
            }
        }

        const handleMessage = (event: MessageEvent) => {
            if (event.data?.type === 'NEW_VERSION') {
                setUpdateAvailable(true)
            }
        }

        const handleControllerChange = () => {
            if (refreshing) {
                return
            }
            refreshing = true
            waitingWorkerRef.current = null
            window.location.reload()
        }

        navigator.serviceWorker.addEventListener('message', handleMessage)
        navigator.serviceWorker.addEventListener('controllerchange', handleControllerChange)

        registerUpdateListeners()

        return () => {
            isMounted = false
            navigator.serviceWorker.removeEventListener('message', handleMessage)
            navigator.serviceWorker.removeEventListener('controllerchange', handleControllerChange)
        }
    }, [])

    useEffect(() => {
        const handleBeforeInstallPrompt = (event: Event) => {
            event.preventDefault()
            deferredPromptRef.current = event as BeforeInstallPromptEvent
            setShowInstallPrompt(true)
        }

        const handleAppInstalled = () => {
            deferredPromptRef.current = null
            setShowInstallPrompt(false)
        }

        window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt as EventListener)
        window.addEventListener('appinstalled', handleAppInstalled)

        return () => {
            window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt as EventListener)
            window.removeEventListener('appinstalled', handleAppInstalled)
        }
    }, [])

    const handleInstallChoice = (outcome: InstallOutcome) => {
        deferredPromptRef.current = null
        setShowInstallPrompt(false)
        if (outcome === 'accepted') {
            console.log('[PWA] User accepted the install prompt')
        } else {
            console.log('[PWA] User dismissed the install prompt')
        }
    }

    const handleInstallDismiss = () => {
        deferredPromptRef.current = null
        setShowInstallPrompt(false)
        console.log('[PWA] Install prompt dismissed for now')
    }

    const updatePWA = () => {
        waitingWorkerRef.current?.postMessage({ type: 'SKIP_WAITING' })
        setUpdateAvailable(false)
    }

    return (
        <>
            <Theme>
                <RouterWrapper>
                    <AuthProvider>
                        <Layout>
                            <Views />
                        </Layout>
                    </AuthProvider>
                </RouterWrapper>
            </Theme>

            {showInstallPrompt && (
                <InstallPWA
                    deferredPrompt={deferredPromptRef.current}
                    onInstallChoice={handleInstallChoice}
                    onDismiss={handleInstallDismiss}
                />
            )}

            {updateAvailable && (
                <button
                    onClick={updatePWA}
                    style={{
                        position: 'fixed',
                        bottom: '20px',
                        right: showInstallPrompt ? '200px' : '20px',
                        padding: '12px 20px',
                        fontSize: '16px',
                        backgroundColor: '#22c55e',
                        color: 'white',
                        border: 'none',
                        borderRadius: '999px',
                        cursor: 'pointer',
                        boxShadow: '0px 10px 20px rgba(34, 197, 94, 0.3)',
                        zIndex: 1000,
                    }}
                >
                    🔄 Update Available - Refresh
                </button>
            )}
        </>
    )
}

export default App

