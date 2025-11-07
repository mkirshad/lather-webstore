import { leatherProducts } from './leatherProducts'

export type AdminProduct = {
    id: string
    name: string
    category: string
    price: number
    inventory: number
    reserved: number
    status: 'ready' | 'low' | 'madeToOrder'
    updatedAt: string
}

export type AdminOrder = {
    id: string
    customer: string
    total: number
    status: 'processing' | 'fulfilled' | 'ready' | 'inProduction'
    channel: 'Web' | 'Retail' | 'Wholesale'
    updatedAt: string
    lineItems: number
}

export type AdminCustomer = {
    id: string
    name: string
    location: string
    email: string
    lifetimeValue: number
    lastOrder: string
    channel: string
}

export const adminProducts: AdminProduct[] = leatherProducts.map(
    (product, index) => ({
        id: product.id,
        name: product.name,
        category: product.category,
        price: product.price,
        inventory: product.madeToOrder ? 12 - index * 2 : 48 - index * 3,
        reserved: 4 + index,
        status: product.madeToOrder
            ? 'madeToOrder'
            : product.stockStatus === 'Ready to ship'
              ? 'ready'
              : 'low',
        updatedAt: product.leadTime,
    }),
)

export const adminOrders: AdminOrder[] = [
    {
        id: 'PO-2048',
        customer: 'Arcadia Retail (Dubai)',
        total: 14800,
        status: 'processing',
        channel: 'Wholesale',
        updatedAt: 'Today • 14:32 PKT',
        lineItems: 42,
    },
    {
        id: 'PO-2047',
        customer: 'Luca Bottega (Milan)',
        total: 6400,
        status: 'inProduction',
        channel: 'Wholesale',
        updatedAt: 'Today • 09:10 PKT',
        lineItems: 18,
    },
    {
        id: 'D2C-982',
        customer: 'Maya Ren',
        total: 890,
        status: 'ready',
        channel: 'Web',
        updatedAt: 'Yesterday • 21:04 PKT',
        lineItems: 1,
    },
    {
        id: 'RET-551',
        customer: 'Atelier Flagship',
        total: 2200,
        status: 'fulfilled',
        channel: 'Retail',
        updatedAt: 'Yesterday • 17:20 PKT',
        lineItems: 6,
    },
]

export const adminCustomers: AdminCustomer[] = [
    {
        id: 'customer-01',
        name: 'Arcadia Retail Group',
        location: 'Dubai, UAE',
        email: 'wholesale@arcadia.com',
        lifetimeValue: 42000,
        lastOrder: 'PO-2048 • Today',
        channel: 'Wholesale Portal',
    },
    {
        id: 'customer-02',
        name: 'Maya Ren',
        location: 'Los Angeles, USA',
        email: 'maya.ren@gmail.com',
        lifetimeValue: 2280,
        lastOrder: 'D2C-982 • Yesterday',
        channel: 'Web Store',
    },
    {
        id: 'customer-03',
        name: 'Luca Bottega Studio',
        location: 'Milan, Italy',
        email: 'orders@lucabottega.it',
        lifetimeValue: 18300,
        lastOrder: 'PO-2047 • Today',
        channel: 'Wholesale Portal',
    },
    {
        id: 'customer-04',
        name: 'Atelier Flagship',
        location: 'Lahore, PK',
        email: 'gm@passionatelier.com',
        lifetimeValue: 11200,
        lastOrder: 'RET-551 • Yesterday',
        channel: 'Retail POS',
    },
]
