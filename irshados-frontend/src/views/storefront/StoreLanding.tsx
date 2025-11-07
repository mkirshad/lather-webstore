import { Link } from 'react-router'
import StorefrontLayout from './StorefrontLayout'
import {
    atelierMetrics,
    collectionHighlights,
    journalEntries,
    leatherProducts,
    testimonials,
    type LeatherProduct,
} from '@/data/leatherProducts'
import { useCartStore } from '@/store/cartStore'
import { formatCurrency } from '@/utils/currency'

const featuredProducts = leatherProducts.slice(0, 4)

const StoreLanding = () => {
    const addItem = useCartStore((state) => state.addItem)

    const handleAdd = (product: LeatherProduct) => {
        const defaultColor = product.colors?.[0]?.name
        const defaultSize = product.sizes?.[0]
        addItem(product, { color: defaultColor, size: defaultSize })
    }

    return (
        <StorefrontLayout>
            <section className="relative overflow-hidden bg-gradient-to-br from-[#080706] via-[#14100d] to-[#1d130c]">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 py-20 md:py-28 grid gap-10 md:grid-cols-2 items-center">
                    <div>
                        <p className="text-sm uppercase tracking-[0.6em] text-white/50">
                            Leather accessories studio
                        </p>
                        <h1 className="mt-6 text-4xl md:text-5xl font-light leading-tight text-white">
                            Leather accessories engineered for modern travel and
                            retail shelves.
                        </h1>
                        <p className="mt-6 text-lg text-white/70">
                            Passion Atelier merges artisanal finishing with a
                            monitored e-commerce stack inspired by
                            passionleathers.com. Explore shoppable collections,
                            editorial stories, and a telemetry-ready launch
                            plan.
                        </p>
                        <div className="mt-8 flex flex-wrap gap-3">
                            <Link
                                to="/collections"
                                className="px-6 py-3 rounded-full bg-white text-black uppercase tracking-wide text-sm"
                            >
                                Shop the collection
                            </Link>
                            <Link
                                to="/journal"
                                className="px-6 py-3 rounded-full border border-white/30 text-white/80 uppercase tracking-wide text-sm hover:text-white"
                            >
                                View journal
                            </Link>
                        </div>
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                        {featuredProducts.map((product) => (
                            <article
                                key={product.id}
                                className="bg-white/5 rounded-3xl p-4 flex flex-col border border-white/5 backdrop-blur"
                            >
                                <img
                                    src={product.heroImage}
                                    alt={product.name}
                                    className="h-48 w-full object-cover rounded-2xl"
                                />
                                <p className="mt-4 text-sm uppercase tracking-wide text-[#c19977]">
                                    {product.badge || product.category}
                                </p>
                                <h3 className="text-lg font-medium text-white">
                                    {product.name}
                                </h3>
                                <p className="text-sm text-white/60 h-12 overflow-hidden">
                                    {product.tagline}
                                </p>
                                <div className="mt-auto pt-4 flex items-center justify-between">
                                    <span className="text-white text-xl font-semibold">
                                        {formatCurrency(product.price)}
                                    </span>
                                    <button
                                        className="text-sm text-white/80 hover:text-white"
                                        onClick={() => handleAdd(product)}
                                    >
                                        Add to cart
                                    </button>
                                </div>
                            </article>
                        ))}
                    </div>
                </div>
            </section>

            <div className="bg-[#f5f5f3] text-gray-900">
                <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 grid gap-6 md:grid-cols-4">
                    {atelierMetrics.map((metric) => (
                        <div
                            key={metric.label}
                            className="border border-gray-200 rounded-3xl p-6 bg-white shadow-md"
                        >
                            <p className="text-3xl font-light text-gray-900">
                                {metric.value}
                            </p>
                            <p className="text-gray-600 mt-2">{metric.label}</p>
                            <p className="text-xs text-gray-400 mt-1">
                                {metric.helper}
                            </p>
                        </div>
                    ))}
                </section>

                <section className="max-w-6xl mx-auto px-4 sm:px-6 py-12 grid gap-8 md:grid-cols-3">
                    {collectionHighlights.map((highlight) => (
                        <article
                            key={highlight.title}
                            className="rounded-3xl overflow-hidden border border-gray-200 bg-white shadow-lg"
                        >
                            <img
                                src={highlight.image}
                                alt={highlight.title}
                                className="h-64 w-full object-cover"
                            />
                            <div className="p-6 space-y-3">
                                <span className="text-xs uppercase tracking-wider text-gray-500">
                                    {highlight.pill}
                                </span>
                                <h3 className="text-2xl text-gray-900 font-light">
                                    {highlight.title}
                                </h3>
                                <p className="text-gray-600 leading-relaxed">
                                    {highlight.summary}
                                </p>
                            </div>
                        </article>
                    ))}
                </section>

                <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 grid gap-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs uppercase tracking-[0.5em] text-gray-500">
                                Featured assortments
                            </p>
                            <h2 className="text-3xl text-gray-900 mt-4 font-light">
                                Highlighted leather pieces ready for retail drops
                            </h2>
                        </div>
                        <Link
                            to="/collections"
                            className="hidden sm:inline-flex px-6 py-3 border border-gray-300 rounded-full text-gray-700 hover:bg-gray-900 hover:text-white transition"
                        >
                            Browse all
                        </Link>
                    </div>
                    <div className="grid gap-6 md:grid-cols-2">
                        {featuredProducts.map((product) => (
                            <ProductCard
                                key={product.id}
                                product={product}
                                onAdd={() => handleAdd(product)}
                            />
                        ))}
                    </div>
                </section>

                <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 grid md:grid-cols-2 gap-10 items-center">
                    <div className="space-y-4">
                        <p className="text-xs uppercase tracking-[0.5em] text-gray-500">
                            Transparent craft & monitoring
                        </p>
                        <h2 className="text-3xl text-gray-900 font-light">
                            Live dashboards track crafting stages, QC, and secure
                            deployment pipelines.
                        </h2>
                        <p className="text-gray-600">
                            Beyond aesthetics, both the storefront and production
                            lines are instrumented. GitHub Actions ship to Vercel,
                            Cloudflare shields traffic, and Sentry + Logtail watch
                            for regressions. Clients can subscribe to build and
                            fulfillment notifications.
                        </p>
                        <ul className="space-y-2 text-gray-600">
                            <li>• Lighthouse + Playwright gates before deploy</li>
                            <li>• Per-route uptime checks via Cronitor</li>
                            <li>• Inventory + order webhooks streaming to ERP</li>
                        </ul>
                    </div>
                    <div className="grid gap-4">
                        <div className="rounded-3xl bg-white border border-gray-200 p-6 shadow-md">
                            <p className="text-sm text-gray-500 uppercase tracking-wider">
                                Observability Stack
                            </p>
                            <p className="text-2xl text-gray-900 mt-3 font-light">
                                Metrics synced every 60 seconds
                            </p>
                            <p className="text-gray-600 mt-2">
                                Shopify-style analytics pipeline built with
                                Supabase, enabling proactive alerts for downtime or
                                low inventory.
                            </p>
                        </div>
                        <div className="rounded-3xl bg-white border border-gray-200 p-6 shadow-md">
                            <p className="text-sm text-gray-500 uppercase tracking-wider">
                                Deployment Ready
                            </p>
                            <p className="text-gray-900 text-lg mt-2">
                                CI/CD templates for Vercel or Render with secrets
                                scanning and rollbacks.
                            </p>
                        </div>
                    </div>
                </section>

                <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 grid gap-6 md:grid-cols-3">
                    {testimonials.map((testimonial) => (
                        <blockquote
                            key={testimonial.author}
                            className="rounded-3xl border border-gray-200 bg-white p-6 text-gray-700 shadow-md"
                        >
                            <p className="text-lg leading-relaxed">
                                “{testimonial.quote}”
                            </p>
                            <footer className="mt-4 text-sm text-gray-500">
                                {testimonial.author} · {testimonial.location}
                            </footer>
                        </blockquote>
                    ))}
                </section>

                <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 space-y-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-xs uppercase tracking-[0.6em] text-gray-500">
                                Journal
                            </p>
                            <h2 className="text-3xl text-gray-900 mt-3 font-light">
                                Product stories & performance reports
                            </h2>
                        </div>
                        <Link
                            to="/journal"
                            className="hidden sm:inline-flex px-5 py-2 border border-gray-300 rounded-full text-gray-700 hover:bg-gray-900 hover:text-white transition"
                        >
                            View journal
                        </Link>
                    </div>
                    <div className="grid gap-6 md:grid-cols-3">
                        {journalEntries.map((entry) => (
                            <article
                                key={entry.id}
                                className="border border-gray-200 rounded-3xl p-6 bg-white shadow-md"
                            >
                                <p className="text-xs text-gray-500 uppercase tracking-widest">
                                    {entry.published}
                                </p>
                                <h3 className="text-xl text-gray-900 mt-3">
                                    {entry.title}
                                </h3>
                                <p className="text-gray-600 mt-2">
                                    {entry.summary}
                                </p>
                                <p className="text-gray-400 text-sm mt-4">
                                    {entry.readingTime}
                                </p>
                            </article>
                        ))}
                    </div>
                </section>
            </div>
        </StorefrontLayout>
    )
}

type ProductCardProps = {
    product: LeatherProduct
    onAdd: () => void
}

const ProductCard = ({ product, onAdd }: ProductCardProps) => {
    return (
        <article className="rounded-3xl border border-white/10 bg-white text-gray-900 overflow-hidden grid md:grid-cols-[1.1fr_0.9fr]">
            <img
                src={product.lifestyleImage}
                alt={product.name}
                className="h-full w-full object-cover"
            />
            <div className="p-6 flex flex-col">
                <div className="flex items-center justify-between">
                    <span className="text-xs uppercase tracking-[0.4em] text-gray-400">
                        {product.category}
                    </span>
                    <span className="text-gray-500">
                        {product.rating.toFixed(1)} · {product.reviews} reviews
                    </span>
                </div>
                <h3 className="text-2xl text-gray-900 mt-4">{product.name}</h3>
                <p className="text-gray-600 mt-2">{product.description}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                    {product.craftsmanship.map((detail) => (
                        <span
                            key={detail}
                            className="px-3 py-1 rounded-full bg-gray-100 text-xs text-gray-600"
                        >
                            {detail}
                        </span>
                    ))}
                </div>
                <div className="mt-auto pt-6 flex flex-col gap-3">
                    <div className="flex items-center justify-between">
                        <span className="text-2xl text-gray-900 font-light">
                            {formatCurrency(product.price)}
                        </span>
                        <span className="text-sm text-gray-500">
                            {product.stockStatus}
                        </span>
                    </div>
                    <div className="flex gap-3">
                        <button
                            className="flex-1 px-4 py-3 rounded-full bg-[#0e0c0a] text-white uppercase tracking-wide text-sm"
                            onClick={onAdd}
                        >
                            Add to cart
                        </button>
                        <Link
                            to={`/product/${product.slug}`}
                            className="flex-1 px-4 py-3 rounded-full border border-gray-200 text-gray-700 uppercase tracking-wide text-sm text-center"
                        >
                            View detail
                        </Link>
                    </div>
                </div>
            </div>
        </article>
    )
}

export default StoreLanding
