import {
    NAV_ITEM_TYPE_TITLE,
    NAV_ITEM_TYPE_ITEM,
    NAV_ITEM_TYPE_COLLAPSE,
} from '@/constants/navigation.constant'

import type { NavigationTree } from '@/@types/navigation'

const navigationConfig: NavigationTree[] = [
    {
        key: 'home',
        path: '/home',
        title: 'Home',
        translateKey: 'nav.home',
        icon: 'home',
        type: NAV_ITEM_TYPE_ITEM,
        authority: [],
        subMenu: [],
    },
    {
        key: 'admin',
        path: '',
        title: 'Store Admin',
        translateKey: 'nav.admin.admin',
        icon: 'admin',
        type: NAV_ITEM_TYPE_COLLAPSE,
        authority: [],
        subMenu: [
            {
                key: 'admin.products',
                path: '/admin/products',
                title: 'Products',
                translateKey: 'nav.admin.products',
                icon: 'products',
                type: NAV_ITEM_TYPE_ITEM,
                authority: [],
                subMenu: [],
            },
            {
                key: 'admin.orders',
                path: '/admin/orders',
                title: 'Orders',
                translateKey: 'nav.admin.orders',
                icon: 'orders',
                type: NAV_ITEM_TYPE_ITEM,
                authority: [],
                subMenu: [],
            },
            {
                key: 'admin.customers',
                path: '/admin/customers',
                title: 'Customers',
                translateKey: 'nav.admin.customers',
                icon: 'customers',
                type: NAV_ITEM_TYPE_ITEM,
                authority: [],
                subMenu: [],
            },
        ],
    },
    {
        key: 'support',
        path: '',
        title: 'Support',
        translateKey: 'nav.support.support',
        icon: 'support',
        type: NAV_ITEM_TYPE_COLLAPSE,
        authority: [],
        subMenu: [
            {
                key: 'support.userGuide',
                path: '/support/user-guide',
                title: 'User Guide',
                translateKey: 'nav.support.userGuide',
                icon: '',
                type: NAV_ITEM_TYPE_ITEM,
                authority: [],
                subMenu: [],
            },
        ],
    },
]

export default navigationConfig
