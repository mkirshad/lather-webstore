import { useMemo } from 'react'
import { leatherProducts } from '@/data/leatherProducts'
import { useCartStore } from '@/store/cartStore'
import { formatCurrency } from '@/utils/currency'

const Home = () => {
    const cartItems = useCartStore((state) => state.items)
    const cartSnapshot = useMemo(() => {
        const itemCount = cartItems.reduce(
            (total, item) => total + item.quantity,
            0,
        )
        const subtotal = cartItems.reduce(
            (total, item) => total + item.price * item.quantity,
            0,
        )
        return { itemCount, subtotal }
    }, [cartItems])
    const readyProducts = leatherProducts.filter(
        (product) => product.stockStatus !== 'Made to order',
    )

    return (
        <div className="p-6 space-y-6 text-gray-900">
            <section className="grid gap-4 md:grid-cols-3">
                <MetricCard
                    label="Active demo cart"
                    value={`${cartSnapshot.itemCount} items`}
                    helper={formatCurrency(cartSnapshot.subtotal)}
                />
                <MetricCard
                    label="Ready-to-ship styles"
                    value={readyProducts.length.toString()}
                    helper="Synced with storefront catalog"
                />
                <MetricCard
                    label="Made-to-order lead time"
                    value="12 days"
                    helper="Updated from atelier board"
                />
            </section>
            <section className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
                <h2 className="text-lg font-medium text-gray-900 mb-4">
                    Best sellers on display
                </h2>
                <div className="grid gap-4 md:grid-cols-3">
                    {leatherProducts.slice(0, 3).map((product) => (
                        <div
                            key={product.id}
                            className="border border-gray-100 rounded-xl p-4 bg-white shadow-sm"
                        >
                            <p className="text-sm text-gray-500 uppercase tracking-widest">
                                {product.category}
                            </p>
                            <p className="text-gray-900 text-lg">
                                {product.name}
                            </p>
                            <p className="text-gray-500 text-sm">
                                {formatCurrency(product.price)} ·{' '}
                                {product.leadTime}
                            </p>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    )
}

const MetricCard = ({
    label,
    value,
    helper,
}: {
    label: string
    value: string
    helper?: string
}) => (
    <div className="border border-gray-100 rounded-2xl p-5 bg-white shadow-sm text-gray-900">
        <p className="text-sm text-gray-500 uppercase tracking-widest">
            {label}
        </p>
        <p className="text-2xl font-light mt-2">{value}</p>
        {helper && <p className="text-gray-500 text-sm mt-1">{helper}</p>}
    </div>
)

export default Home
