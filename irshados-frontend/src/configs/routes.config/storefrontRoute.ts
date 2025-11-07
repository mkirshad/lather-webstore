import { lazy } from 'react'
import type { Routes } from '@/@types/routes'

const storefrontRoute: Routes = [
    {
        key: 'storefront.home',
        path: '/',
        component: lazy(() => import('@/views/storefront/StoreLanding')),
        authority: [],
        meta: {
            layout: 'classic',
            pageBackgroundType: 'transparent',
            pageContainerType: 'gutterless',
        },
    },
    {
        key: 'storefront.collections',
        path: '/collections',
        component: lazy(() => import('@/views/storefront/CollectionsView')),
        authority: [],
        meta: {
            pageContainerType: 'gutterless',
        },
    },
    {
        key: 'storefront.product',
        path: '/product/:slug',
        component: lazy(() => import('@/views/storefront/ProductDetailView')),
        authority: [],
        meta: {
            pageContainerType: 'gutterless',
        },
    },
    {
        key: 'storefront.journal',
        path: '/journal',
        component: lazy(() => import('@/views/storefront/JournalView')),
        authority: [],
    },
    {
        key: 'storefront.about',
        path: '/about',
        component: lazy(() => import('@/views/storefront/AboutView')),
        authority: [],
    },
    {
        key: 'storefront.contact',
        path: '/contact',
        component: lazy(() => import('@/views/storefront/ContactView')),
        authority: [],
    },
]

export default storefrontRoute
