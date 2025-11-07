import { lazy } from 'react'
import authRoute from './authRoute'
import othersRoute from './othersRoute'
import storefrontRoute from './storefrontRoute'
import type { Routes } from '@/@types/routes'

export const publicRoutes: Routes = [...storefrontRoute, ...authRoute]

export const protectedRoutes: Routes = [
    {
        key: 'home',
        path: '/home',
        component: lazy(() => import('@/views/Home')),
        authority: [],
    },
    {
        key: 'admin.products',
        path: '/admin/products',
        component: lazy(() => import('@/views/adminStore/ProductsView')),
        authority: [],
        meta: {
            header: {
                title: 'Products',
                description:
                    'Catalogue view aligned with the public Passion Atelier storefront.',
            },
        },
    },
    {
        key: 'admin.orders',
        path: '/admin/orders',
        component: lazy(() => import('@/views/adminStore/OrdersView')),
        authority: [],
        meta: {
            header: {
                title: 'Orders',
                description:
                    'Wholesale, retail, and D2C orders flowing through the pipeline.',
            },
        },
    },
    {
        key: 'admin.customers',
        path: '/admin/customers',
        component: lazy(() => import('@/views/adminStore/CustomersView')),
        authority: [],
        meta: {
            header: {
                title: 'Customers',
                description:
                    'High-touch buyers and VIP customers with live telemetry hooks.',
            },
        },
    },
    {
        key: 'support.userGuide',
        path: '/support/user-guide',
        component: lazy(() => import('@/views/support')),
        authority: [],
        meta: {
            pageContainerType: 'contained',
            pageBackgroundType: 'plain',
            header: {
                title: 'In App User Guide',
                description:
                    'Follow the ECME DEMO flows for onboarding, inventory, purchasing, sales, POS, and reporting.',
            },
        },
    },
    ...othersRoute,
]
