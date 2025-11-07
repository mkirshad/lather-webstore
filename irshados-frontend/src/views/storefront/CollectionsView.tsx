import { useMemo, useState } from 'react'
import StorefrontLayout from './StorefrontLayout'
import { leatherProducts, type ProductCategory } from '@/data/leatherProducts'
import { useCartStore } from '@/store/cartStore'
import { formatCurrency } from '@/utils/currency'
import { Link } from 'react-router'

type FilterCategory = ProductCategory | 'all'

const categories: { label: string; value: FilterCategory }[] = [
    { label: 'All', value: 'all' },
    { label: 'Bags', value: 'bags' },
    { label: 'Travel', value: 'travel' },
    { label: 'Wallets', value: 'wallets' },
    { label: 'Belts', value: 'belts' },
    { label: 'Accessories', value: 'accessories' },
]

const sortOptions = [
    { label: 'Featured', value: 'featured' },
    { label: 'Price (low to high)', value: 'priceAsc' },
    { label: 'Price (high to low)', value: 'priceDesc' },
]

const CollectionsView = () => {
    const [category, setCategory] = useState<FilterCategory>('all')
    const [sortBy, setSortBy] = useState('featured')
    const addItem = useCartStore((state) => state.addItem)

    const products = useMemo(() => {
        let data = [...leatherProducts]
        if (category !== 'all') {
            data = data.filter((product) => product.category === category)
        }
        if (sortBy === 'priceAsc') {
            data = data.sort((a, b) => a.price - b.price)
        } else if (sortBy === 'priceDesc') {
            data = data.sort((a, b) => b.price - a.price)
        } else {
            data = data.sort((a, b) => Number(b.bestseller) - Number(a.bestseller))
        }
        return data
    }, [category, sortBy])

    return (
        <StorefrontLayout>
            <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 space-y-10 text-gray-900">
                <header className="space-y-4">
                    <p className="text-xs uppercase tracking-[0.5em] text-gray-500">
                        Collections
                    </p>
                    <h1 className="text-4xl text-gray-900 font-light">
                        Retail-ready assortment with transparent specs
                    </h1>
                    <p className="text-gray-600">
                        Downloadable specs, configurable variants, and
                        fulfillment promises keep wholesale and D2C flows
                        aligned. Filter the lineup and drop items into the
                        working cart to show e-commerce readiness.
                    </p>
                </header>

                <div className="flex flex-wrap gap-3">
                    {categories.map((item) => (
                        <button
                            key={item.value}
                            onClick={() => setCategory(item.value)}
                            className={`px-4 py-2 rounded-full text-sm border ${
                                category === item.value
                                    ? 'bg-gray-900 text-white border-gray-900'
                                    : 'border-gray-300 text-gray-600 hover:bg-gray-900 hover:text-white'
                            }`}
                        >
                            {item.label}
                        </button>
                    ))}
                </div>

                <div className="flex flex-wrap items-center justify-between gap-4">
                    <p className="text-gray-600 text-sm">
                        Showing {products.length} pieces
                    </p>
                    <select
                        value={sortBy}
                        onChange={(event) => setSortBy(event.target.value)}
                        className="bg-white/80 border border-gray-300 rounded-full px-4 py-2 text-sm text-gray-800"
                    >
                        {sortOptions.map((option) => (
                            <option
                                key={option.value}
                                value={option.value}
                                className="text-black"
                            >
                                {option.label}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                    {products.map((product) => (
                        <article
                            key={product.id}
                            className="grid md:grid-cols-2 border border-gray-100 rounded-3xl overflow-hidden bg-white text-gray-900 shadow-lg"
                        >
                            <img
                                src={product.heroImage}
                                alt={product.name}
                                className="h-full object-cover w-full"
                            />
                            <div className="p-6 flex flex-col">
                                <div className="flex items-center justify-between text-sm text-gray-500">
                                    <span className="uppercase tracking-[0.4em]">
                                        {product.category}
                                    </span>
                                    {product.badge && (
                                        <span className="text-[#b86b3c] font-medium">
                                            {product.badge}
                                        </span>
                                    )}
                                </div>
                                <h3 className="text-2xl text-gray-900 mt-3 font-semibold">
                                    {product.name}
                                </h3>
                                <p className="text-gray-600 mt-2 flex-1">
                                    {product.description}
                                </p>
                                <div className="mt-4 flex gap-2">
                                    {product.colors.map((color) => (
                                        <span
                                            key={`${product.id}-${color.name}`}
                                            className="h-6 w-6 rounded-full border border-white/10"
                                            style={{ backgroundColor: color.hex }}
                                        />
                                    ))}
                                </div>
                                <div className="mt-6 flex items-center justify-between">
                                    <div>
                                        <p className="text-gray-900 text-2xl font-semibold">
                                            {formatCurrency(product.price)}
                                        </p>
                                        <p className="text-xs text-gray-500">
                                            {product.leadTime}
                                        </p>
                                    </div>
                                    <div className="flex gap-3">
                                        <button
                                            className="px-4 py-2 rounded-full border border-gray-300 text-gray-700 text-sm hover:bg-gray-900 hover:text-white transition"
                                            onClick={() =>
                                                addItem(product, {
                                                    color: product.colors[0]?.name,
                                                    size: product.sizes?.[0],
                                                })
                                            }
                                        >
                                            Add
                                        </button>
                                        <Link
                                            to={`/product/${product.slug}`}
                                            className="px-4 py-2 rounded-full bg-gray-900 text-white text-sm hover:bg-black transition"
                                        >
                                            Details
                                        </Link>
                                    </div>
                                </div>
                            </div>
                        </article>
                    ))}
                </div>
            </section>
        </StorefrontLayout>
    )
}

export default CollectionsView
