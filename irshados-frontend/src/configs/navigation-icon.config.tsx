import {
    PiHouseLineDuotone,
    PiArrowsInDuotone,
    PiBookOpenUserDuotone,
    PiBookBookmarkDuotone,
    PiAcornDuotone,
    PiBagSimpleDuotone,
    PiLifebuoyDuotone,
    PiBriefcaseMetalDuotone,
    PiClipboardTextDuotone,
    PiUsersThreeDuotone,
} from 'react-icons/pi'
import type { JSX } from 'react'

export type NavigationIcons = Record<string, JSX.Element>

const navigationIcon: NavigationIcons = {
    home: <PiHouseLineDuotone />,
    singleMenu: <PiAcornDuotone />,
    collapseMenu: <PiArrowsInDuotone />,
    groupSingleMenu: <PiBookOpenUserDuotone />,
    groupCollapseMenu: <PiBookBookmarkDuotone />,
    groupMenu: <PiBagSimpleDuotone />,
    support: <PiLifebuoyDuotone />,
    admin: <PiBriefcaseMetalDuotone />,
    products: <PiBagSimpleDuotone />,
    orders: <PiClipboardTextDuotone />,
    customers: <PiUsersThreeDuotone />,
}

export default navigationIcon
