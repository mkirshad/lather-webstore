import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { LeatherProduct } from '@/data/leatherProducts'

export type CartItem = {
    itemId: string
    productId: string
    name: string
    slug: string
    price: number
    quantity: number
    color?: string
    size?: string
    image: string
}

type CartState = {
    items: CartItem[]
}

type CartActions = {
    addItem: (
        product: LeatherProduct,
        options?: {
            color?: string
            size?: string
            quantity?: number
        },
    ) => void
    removeItem: (itemId: string) => void
    updateQuantity: (itemId: string, quantity: number) => void
    clear: () => void
}

const buildVariantKey = (
    productId: string,
    color?: string,
    size?: string,
    suffix?: string,
) => {
    const safeColor = color || 'default-color'
    const safeSize = size || 'default-size'
    return `${productId}-${safeColor}-${safeSize}${suffix ? `-${suffix}` : ''}`
}

export const useCartStore = create<CartState & CartActions>()(
    persist(
        (set) => ({
            items: [],
            addItem: (product, options) => {
                const color = options?.color
                const size = options?.size
                const quantity = Math.max(1, options?.quantity ?? 1)

                set((state) => {
                    const variantKey = buildVariantKey(
                        product.id,
                        color,
                        size,
                    )
                    const existingItem = state.items.find(
                        (item) => item.itemId === variantKey,
                    )

                    if (existingItem) {
                        return {
                            items: state.items.map((item) =>
                                item.itemId === variantKey
                                    ? {
                                          ...item,
                                          quantity: item.quantity + quantity,
                                      }
                                    : item,
                            ),
                        }
                    }

                    const newItem: CartItem = {
                        itemId: variantKey,
                        productId: product.id,
                        name: product.name,
                        slug: product.slug,
                        price: product.price,
                        color,
                        size,
                        quantity,
                        image: product.heroImage,
                    }

                    return {
                        items: [...state.items, newItem],
                    }
                })
            },
            removeItem: (itemId) =>
                set((state) => ({
                    items: state.items.filter((item) => item.itemId !== itemId),
                })),
            updateQuantity: (itemId, quantity) =>
                set((state) => ({
                    items: state.items.map((item) =>
                        item.itemId === itemId
                            ? { ...item, quantity: Math.max(1, quantity) }
                            : item,
                    ),
                })),
            clear: () => set({ items: [] }),
        }),
        {
            name: 'storefront-cart',
            storage: createJSONStorage(() => localStorage),
        },
    ),
)

export const selectCartSummary = (state: CartState) => {
    const itemCount = state.items.reduce(
        (total, item) => total + item.quantity,
        0,
    )
    const subtotal = state.items.reduce(
        (total, item) => total + item.price * item.quantity,
        0,
    )
    return { itemCount, subtotal }
}
