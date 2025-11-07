import { useCallback, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router'
import { PiQuestionDuotone, PiCheckCircleDuotone } from 'react-icons/pi'
import Drawer from '@/components/ui/Drawer'
import Button from '@/components/ui/Button'
import withHeaderItem, {
    type WithHeaderItemProps,
} from '@/utils/hoc/withHeaderItem'
import { useHelpStore } from '@/store/helpStore'
import { useRouteKeyStore } from '@/store/routeKeyStore'
import {
    defaultHelpTopicKey,
    helpTopics,
    type HelpTopic,
} from '@/data/helpTopics'
import classNames from 'classnames'

const resolvedTopicByKey = (key?: string | null): HelpTopic => {
    if (helpTopics.length === 0) {
        throw new Error('No help topics configured')
    }
    if (!key) {
        return (
            helpTopics.find((topic) => topic.key === defaultHelpTopicKey) ||
            helpTopics[0]
        )
    }
    return (
        helpTopics.find((topic) => topic.key === key) ||
        helpTopics.find((topic) => topic.key === defaultHelpTopicKey) ||
        helpTopics[0]
    )
}

const _HelpPanel = ({ className }: WithHeaderItemProps) => {
    const navigate = useNavigate()
    const currentRouteKey = useRouteKeyStore(
        (state) => state.currentRouteKey || undefined,
    )
    const { isOpen, open, close, topicKey, setTopic } = useHelpStore()

    const activeTopic = useMemo(() => {
        return resolvedTopicByKey(topicKey ?? currentRouteKey)
    }, [currentRouteKey, topicKey])

    const handleOpen = useCallback(() => {
        const key = currentRouteKey ?? defaultHelpTopicKey
        setTopic(key)
        open(key)
    }, [currentRouteKey, open, setTopic])

    useEffect(() => {
        if (isOpen) {
            setTopic(currentRouteKey ?? defaultHelpTopicKey)
        }
    }, [currentRouteKey, isOpen, setTopic])

    const primaryLink = activeTopic.links?.[0]
    const secondaryLinks = activeTopic.links?.slice(1) ?? []

    const goToGuide = () => {
        close()
        const destination = primaryLink?.path ?? '/support/user-guide'
        navigate(destination)
    }

    return (
        <>
            <button
                type="button"
                aria-label="Open help"
                className={classNames(
                    'text-2xl hover:text-primary-500 transition-colors',
                    className,
                )}
                onClick={handleOpen}
            >
                <PiQuestionDuotone />
            </button>
            <Drawer
                title={activeTopic.title}
                isOpen={isOpen}
                width="min(420px, 100vw)"
                onClose={close}
                onRequestClose={close}
                placement="right"
                bodyClass="px-5 pb-6 space-y-4"
            >
                <p className="text-sm text-muted">{activeTopic.summary}</p>
                <ul className="space-y-3">
                    {activeTopic.bullets.map((bullet, index) => (
                        <li
                            key={index}
                            className="flex items-start gap-3 text-sm leading-relaxed"
                        >
                            <PiCheckCircleDuotone className="text-primary-500 mt-0.5 shrink-0" />
                            <span>{bullet}</span>
                        </li>
                    ))}
                </ul>
                {secondaryLinks.length > 0 && (
                    <div className="space-y-2">
                        {secondaryLinks.map((link, index) => (
                            <Button
                                key={index}
                                block
                                variant="plain"
                                className="justify-center border border-primary-500 text-primary-600 hover:bg-primary-50 dark:border-primary-400 dark:text-primary-200 dark:hover:bg-primary-500/10"
                                onClick={() => {
                                    if (link.path) {
                                        close()
                                        navigate(link.path)
                                    }
                                }}
                            >
                                {link.label}
                            </Button>
                        ))}
                    </div>
                )}
                <div className="space-y-2">
                    <Button
                        block
                        variant="solid"
                        onClick={goToGuide}
                        className="justify-center"
                    >
                        {primaryLink?.label ?? 'View full guide'}
                    </Button>
                    <div
                        className={classNames(
                            'text-xs text-left text-muted border-t border-gray-200',
                            'pt-3',
                        )}
                    >
                        Need more help? Email{' '}
                        <a
                            className="text-primary-500 underline"
                            href="mailto:support@irshados.dev"
                        >
                            support@irshados.dev
                        </a>
                        .
                    </div>
                </div>
            </Drawer>
        </>
    )
}

const HelpPanel = withHeaderItem(_HelpPanel)

export default HelpPanel
