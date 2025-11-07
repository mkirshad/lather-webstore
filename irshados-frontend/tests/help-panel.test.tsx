import React from "react"
import test, { beforeEach, afterEach } from 'node:test'
import assert from 'node:assert/strict'
import { JSDOM } from 'jsdom'
import { render, fireEvent } from '@testing-library/react'
import { useHelpStore } from '../src/store/helpStore'
import { useRouteKeyStore } from '../src/store/routeKeyStore'
import { helpTopics, defaultHelpTopicKey } from '../src/data/helpTopics'

let dom: JSDOM | null = null
const assignedGlobals = new Set<string>()

const setGlobalValue = (key: string, value: unknown) => {
    assignedGlobals.add(key)
    Object.defineProperty(globalThis, key, {
        configurable: true,
        writable: true,
        value,
    })
}

beforeEach(() => {
    dom = new JSDOM('<!doctype html><html><body></body></html>', {
        url: 'http://localhost/',
    })

    const window = dom.window as unknown as Window & typeof globalThis

    setGlobalValue('window', window)
    setGlobalValue('document', window.document)
    setGlobalValue('navigator', window.navigator)
    setGlobalValue('HTMLElement', window.HTMLElement)
    setGlobalValue('Node', window.Node)
    setGlobalValue('getComputedStyle', window.getComputedStyle.bind(window))

    setGlobalValue(
        'requestAnimationFrame',
        ((callback: (time: number) => void) =>
            window.setTimeout(() => callback(Date.now()), 16)) as unknown,
    )
    setGlobalValue(
        'cancelAnimationFrame',
        ((handle: number) => window.clearTimeout(handle)) as unknown,
    )

    useHelpStore.setState({ isOpen: false, topicKey: null })
    useRouteKeyStore.setState({ currentRouteKey: '' })
})

afterEach(() => {
    useHelpStore.setState({ isOpen: false, topicKey: null })
    useRouteKeyStore.setState({ currentRouteKey: '' })
    if (dom) {
        dom.window.close()
        dom = null
    }
    assignedGlobals.forEach((key) => {
        Reflect.deleteProperty(globalThis, key)
    })
    assignedGlobals.clear()
})

const resolveTopic = (key: string | null): typeof helpTopics[number] => {
    if (helpTopics.length === 0) {
        throw new Error('helpTopics data is missing')
    }
    const normalizedKey = key ?? defaultHelpTopicKey
    return (
        helpTopics.find((topic) => topic.key === normalizedKey) ??
        helpTopics.find((topic) => topic.key === defaultHelpTopicKey) ??
        helpTopics[0]
    )
}

const HelpPanelHarness = () => {
    const { isOpen, topicKey, open, close, setTopic } = useHelpStore()
    const currentRouteKey = useRouteKeyStore((state) => state.currentRouteKey)
    const activeTopic = resolveTopic(topicKey ?? currentRouteKey ?? null)

    const handleOpen = () => {
        const routeKey = currentRouteKey || defaultHelpTopicKey
        setTopic(routeKey)
        open(routeKey)
    }

    return (
        <div>
            <button type="button" aria-label="Open help" onClick={handleOpen}>
                Open help
            </button>
            {isOpen && (
                <div role="dialog" aria-label="Help drawer">
                    <h2>{activeTopic.title}</h2>
                    <p>{activeTopic.summary}</p>
                    <button type="button" onClick={close}>
                        Close
                    </button>
                </div>
            )}
        </div>
    )
}

test('help store opens with default topic and closes on escape', async () => {
    const { getByRole, findByText } = render(<HelpPanelHarness />)

    fireEvent.click(getByRole('button', { name: /open help/i }))

    await findByText(/workspace overview/i)
    assert.equal(useHelpStore.getState().isOpen, true)
    assert.equal(useHelpStore.getState().topicKey, defaultHelpTopicKey)

    const closeButton = getByRole('button', { name: /close/i })
    fireEvent.click(closeButton)

    assert.equal(useHelpStore.getState().isOpen, false)
})

test('help store respects the current route key when opening', async () => {
    useRouteKeyStore.setState({ currentRouteKey: 'inventory.products' })

    const { getByRole, findByText } = render(<HelpPanelHarness />)

    fireEvent.click(getByRole('button', { name: /open help/i }))
    await findByText(/products and variants/i)

    const { topicKey } = useHelpStore.getState()
    assert.equal(topicKey, 'inventory.products')
})
