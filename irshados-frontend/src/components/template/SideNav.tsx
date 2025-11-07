import classNames from '@/utils/classNames'
import ScrollBar from '@/components/ui/ScrollBar'
import Logo from '@/components/template/Logo'
import VerticalMenuContent from '@/components/template/VerticalMenuContent'
import { useThemeStore } from '@/store/themeStore'
import { useSessionUser } from '@/store/authStore'
import { useRouteKeyStore } from '@/store/routeKeyStore'
import navigationConfig from '@/configs/navigation.config'
import appConfig from '@/configs/app.config'
import { Link } from 'react-router'
import { useEffect, useRef, useState } from 'react'
import {
    SIDE_NAV_WIDTH,
    SIDE_NAV_COLLAPSED_WIDTH,
    SIDE_NAV_CONTENT_GUTTER,
    HEADER_HEIGHT,
    LOGO_X_GUTTER,
} from '@/constants/theme.constant'
import type { Mode } from '@/@types/theme'

type SideNavProps = {
    translationSetup?: boolean
    background?: boolean
    className?: string
    contentClass?: string
    mode?: Mode
}

const SideNav = ({
    translationSetup = true,
    background = true,
    className,
    contentClass,
    mode,
}: SideNavProps) => {
    const defaultMode = useThemeStore((state) => state.mode)
    const direction = useThemeStore((state) => state.direction)

    const [isHovered, setIsHovered] = useState(false)
    const [isExpanded, setIsExpanded] = useState(false)
    const hoverTimeoutRef = useRef<NodeJS.Timeout | null>(null)

    const currentRouteKey = useRouteKeyStore((state) => state.currentRouteKey)
    const userAuthority = useSessionUser((state) => state.user.authority)
    const fetchUserGroups = useSessionUser((state) => state.fetchUserGroups)

    useEffect(() => {
        console.log('userAuthority', userAuthority)
        fetchUserGroups()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    const clearHoverTimeout = () => {
        if (hoverTimeoutRef.current) {
            clearTimeout(hoverTimeoutRef.current)
            hoverTimeoutRef.current = null
        }
    }

    const handleMouseEnter = () => {
        clearHoverTimeout()
        setIsHovered(true)
        hoverTimeoutRef.current = setTimeout(() => {
            setIsExpanded(true)
        }, 150)
    }

    const handleMouseLeave = () => {
        clearHoverTimeout()
        setIsHovered(false)
        hoverTimeoutRef.current = setTimeout(() => {
            setIsExpanded(false)
        }, 150)
    }

    useEffect(() => {
        return () => clearHoverTimeout()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])

    const navExpanded = isHovered || isExpanded

    return (
        <div
            style={{
                width: navExpanded ? SIDE_NAV_WIDTH : SIDE_NAV_COLLAPSED_WIDTH,
                minWidth: navExpanded ? SIDE_NAV_WIDTH : SIDE_NAV_COLLAPSED_WIDTH,
                transition: 'width 0.3s ease-in-out',
            }}
            className={classNames(
                'side-nav',
                background && 'side-nav-bg',
                navExpanded && 'side-nav-expand',
                className,
            )}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
        >
            <Link
                to={appConfig.authenticatedEntryPath}
                className="side-nav-header flex flex-col justify-center"
                style={{ height: HEADER_HEIGHT }}
            >
                <Logo
                    imgClass="max-h-10"
                    mode={mode || defaultMode}
                    type={isHovered ? 'full' : 'streamline'}
                    className={classNames(
                        isHovered ? LOGO_X_GUTTER : SIDE_NAV_CONTENT_GUTTER,
                    )}
                />
            </Link>
            <div className={classNames('side-nav-content', contentClass)}>
                <ScrollBar style={{ height: '100%' }} direction={direction}>
                    <VerticalMenuContent
                        collapsed={!navExpanded}
                        navigationTree={navigationConfig}
                        routeKey={currentRouteKey}
                        direction={direction}
                        translationSetup={translationSetup}
                        userAuthority={userAuthority || []}
                    />
                </ScrollBar>
            </div>
        </div>
    )
}

export default SideNav
