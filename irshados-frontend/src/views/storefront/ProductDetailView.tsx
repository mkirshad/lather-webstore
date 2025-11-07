import { useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router'
import StorefrontLayout from './StorefrontLayout'
import { leatherProducts, type LeatherProduct } from '@/data/leatherProducts'
import { useCartStore } from '@/store/cartStore'
import { formatCurrency } from '@/utils/currency'

const ProductDetailView = () => {
    const { slug } = useParams()
    const navigate = useNavigate()
    const addItem = useCartStore((state) => state.addItem)

    const product = leatherProducts.find((item) => item.slug === slug)

    const [color, setColor] = useState(product?.colors[0]?.name)
    const [size, setSize] = useState(product?.sizes?.[0])
    const [quantity, setQuantity] = useState(1)

    const recommendations = useMemo(() => {
        if (!product) {
            return []
        }
        return leatherProducts
            .filter(
                (item) => item.category === product.category && item.id !== product.id,
            )
            .slice(0, 2)
    }, [product])

    if (!product) {
        return (
            <StorefrontLayout>
                <div className="max-w-4xl mx-auto px-4 sm:px-6 py-20 text-center text-gray-700 bg-[#f5f5f3]">
                    <p>Product not found.</p>
                    <button
                        className="mt-4 px-6 py-3 rounded-full bg-gray-900 text-white"
                        onClick={() => navigate('/collections')}
                    >
                        Back to collections
                    </button>
                </div>
            </StorefrontLayout>
        )
    }

    const handleAdd = () => {
        addItem(product, { color, size, quantity })
    }

    return (
        <StorefrontLayout>
            <section className="max-w-6xl mx-auto px-4 sm:px-6 py-16 grid gap-10 md:grid-cols-2 bg-[#f5f5f3] text-gray-900">
                <div className="space-y-4">
                    <img
                        src={product.heroImage}
                        alt={product.name}
                        className="rounded-3xl object-cover w-full h-[480px]"
                    />
                    <div className="grid grid-cols-2 gap-4">
                        {product.detailImages.map((image) => (
                            <img
                                key={image}
                                src={image}
                                alt={`${product.name} detail`}
                                className="rounded-2xl h-40 w-full object-cover"
                            />
                        ))}
                    </div>
                </div>

                <div className="space-y-6">
                    <div>
                        <p className="text-xs uppercase tracking-[0.5em] text-gray-500">
                            {product.category}
                        </p>
                        <h1 className="text-4xl text-gray-900 font-light mt-2">
                            {product.name}
                        </h1>
                        <p className="text-gray-600 mt-2">{product.tagline}</p>
                    </div>

                    <div className="flex items-center gap-6">
                        <p className="text-3xl text-gray-900">
                            {formatCurrency(product.price)}
                        </p>
                        <div className="text-sm text-gray-600">
                            <p>{product.stockStatus}</p>
                            <p>{product.leadTime}</p>
                        </div>
                    </div>

                    <div className="space-y-3">
                        <p className="text-gray-700 uppercase tracking-wide text-xs">
                            Color
                        </p>
                        <div className="flex gap-3">
                            {product.colors.map((option) => (
                                <button
                                    key={option.name}
                                    onClick={() => setColor(option.name)}
                                    className={`h-10 w-10 rounded-full border ${
                                        color === option.name
                                            ? 'border-gray-900'
                                            : 'border-gray-300'
                                    }`}
                                    style={{ backgroundColor: option.hex }}
                                />
                            ))}
                        </div>
                    </div>

                    {product.sizes && (
                        <div className="space-y-3">
                            <p className="text-gray-700 uppercase tracking-wide text-xs">
                                Size
                            </p>
                            <div className="flex gap-2 flex-wrap">
                                {product.sizes.map((option) => (
                                    <button
                                        key={option}
                                        onClick={() => setSize(option)}
                                        className={`px-4 py-2 rounded-full border text-sm ${
                                            size === option
                                                ? 'bg-gray-900 text-white border-gray-900'
                                                : 'border-gray-300 text-gray-600'
                                        }`}
                                    >
                                        {option}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    <div>
                        <p className="text-gray-700 uppercase tracking-wide text-xs">
                            Quantity
                        </p>
                        <input
                            type="number"
                            min={1}
                            value={quantity}
                            onChange={(event) =>
                                setQuantity(Math.max(1, Number(event.target.value)))
                            }
                            className="mt-2 bg-white border border-gray-300 rounded-full px-4 py-2 text-gray-900 w-32"
                        />
                    </div>

                    <div className="flex flex-col gap-3 sm:flex-row">
                        <button
                            className="flex-1 px-6 py-3 rounded-full bg-gray-900 text-white uppercase tracking-wide"
                            onClick={handleAdd}
                        >
                            Add to cart
                        </button>
                        <Link
                            to="/contact"
                            className="flex-1 px-6 py-3 rounded-full border border-gray-300 text-gray-700 uppercase tracking-wide text-center hover:bg-gray-900 hover:text-white transition"
                        >
                            Request wholesale pack
                        </Link>
                    </div>

                    <div className="border border-gray-200 rounded-3xl p-6 space-y-4 bg-white shadow-md">
                        <p className="text-gray-600 leading-relaxed">
                            {product.description}
                        </p>
                        <ul className="space-y-2 text-gray-600">
                            {product.craftsmanship.map((detail) => (
                                <li key={detail}>• {detail}</li>
                            ))}
                        </ul>
                        <div>
                            <p className="text-sm text-gray-500 uppercase tracking-wide">
                                Materials
                            </p>
                            <ul className="text-gray-600">
                                {product.materials.map((material) => (
                                    <li key={material}>{material}</li>
                                ))}
                            </ul>
                        </div>
                    </div>
                </div>
            </section>

            {recommendations.length > 0 && (
                <section className="max-w-6xl mx-auto px-4 sm:px-6 pb-16 space-y-6 bg-[#f5f5f3] text-gray-900">
                    <h2 className="text-2xl text-gray-900 font-light">
                        You may also like
                    </h2>
                    <div className="grid gap-6 md:grid-cols-2">
                        {recommendations.map((item) => (
                            <article
                                key={item.id}
                                className="border border-gray-200 rounded-3xl overflow-hidden bg-white shadow-md"
                            >
                                <img
                                    src={item.heroImage}
                                    alt={item.name}
                                    className="h-64 w-full object-cover"
                                />
                                <div className="p-6 space-y-3 text-gray-900">
                                    <p className="text-xs uppercase tracking-[0.5em] text-gray-500">
                                        {item.category}
                                    </p>
                                    <h3 className="text-2xl text-gray-900">
                                        {item.name}
                                    </h3>
                                    <p className="text-gray-600">
                                        {item.tagline}
                                    </p>
                                    <div className="flex items-center justify-between">
                                        <span className="text-xl text-gray-900 font-semibold">
                                            {formatCurrency(item.price)}
                                        </span>
                                        <Link
                                            to={`/product/${item.slug}`}
                                            className="px-4 py-2 rounded-full border border-gray-300 text-gray-700 hover:bg-gray-900 hover:text-white transition"
                                        >
                                            View
                                        </Link>
                                    </div>
                                </div>
                            </article>
                        ))}
                    </div>
                </section>
            )}
        </StorefrontLayout>
    )
}

export default ProductDetailView
