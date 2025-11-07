import { adminProducts } from '@/data/adminStore'
import { formatCurrency } from '@/utils/currency'

const statusBadge: Record<
    string,
    { label: string; className: string }
> = {
    ready: {
        label: 'Ready to ship',
        className:
            'bg-emerald-100 text-emerald-700 border border-emerald-200',
    },
    low: {
        label: 'Low stock',
        className: 'bg-amber-100 text-amber-700 border border-amber-200',
    },
    madeToOrder: {
        label: 'Made to order',
        className: 'bg-sky-100 text-sky-700 border border-sky-200',
    },
}

const ProductsView = () => {
    return (
        <div className="space-y-6">
            <header className="space-y-2">
                <h1 className="text-2xl font-semibold text-gray-900">
                    Catalog overview
                </h1>
                <p className="text-gray-600 max-w-2xl">
                    This grid mirrors what would sync with the storefront. Show
                    buyers how inventory, pricing, and fulfillment promises line
                    up with the public Passion Atelier experience.
                </p>
            </header>
            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-500 uppercase text-xs">
                        <tr>
                            <th className="text-left px-5 py-3 font-medium">
                                Product
                            </th>
                            <th className="text-left px-5 py-3 font-medium">
                                Category
                            </th>
                            <th className="text-left px-5 py-3 font-medium">
                                Price
                            </th>
                            <th className="text-left px-5 py-3 font-medium">
                                Available / Reserved
                            </th>
                            <th className="text-left px-5 py-3 font-medium">
                                Status
                            </th>
                            <th className="text-left px-5 py-3 font-medium">
                                Lead time
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {adminProducts.map((product) => (
                            <tr
                                key={product.id}
                                className="border-t border-gray-100 text-gray-800"
                            >
                                <td className="px-5 py-4 font-medium">
                                    {product.name}
                                </td>
                                <td className="px-5 py-4 capitalize text-gray-500">
                                    {product.category}
                                </td>
                                <td className="px-5 py-4 font-semibold">
                                    {formatCurrency(product.price)}
                                </td>
                                <td className="px-5 py-4 text-gray-600">
                                    {product.inventory} / {product.reserved}
                                </td>
                                <td className="px-5 py-4">
                                    <span
                                        className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${statusBadge[product.status].className}`}
                                    >
                                        {statusBadge[product.status].label}
                                    </span>
                                </td>
                                <td className="px-5 py-4 text-gray-500">
                                    {product.updatedAt}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default ProductsView
