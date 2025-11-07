import { adminOrders } from '@/data/adminStore'
import { formatCurrency } from '@/utils/currency'

const statusCopy: Record<
    string,
    { dot: string; label: string }
> = {
    processing: { dot: 'bg-amber-500', label: 'Processing' },
    fulfilled: { dot: 'bg-emerald-500', label: 'Fulfilled' },
    ready: { dot: 'bg-sky-500', label: 'Ready for pickup' },
    inProduction: { dot: 'bg-indigo-500', label: 'In production' },
}

const OrdersView = () => {
    return (
        <div className="space-y-6">
            <header className="space-y-2">
                <h1 className="text-2xl font-semibold text-gray-900">
                    Order pipeline
                </h1>
                <p className="text-gray-600 max-w-2xl">
                    Wholesale, retail, and direct orders flow into this queue.
                    Tie each status to the Django backend endpoints when you
                    need a fully automated demo.
                </p>
            </header>
            <div className="grid gap-4">
                {adminOrders.map((order) => (
                    <article
                        key={order.id}
                        className="border border-gray-200 rounded-2xl p-5 bg-white flex flex-wrap gap-4 items-center justify-between"
                    >
                        <div>
                            <p className="text-sm text-gray-500 uppercase tracking-wide">
                                {order.id}
                            </p>
                            <p className="text-lg font-semibold text-gray-900">
                                {order.customer}
                            </p>
                            <p className="text-sm text-gray-500">
                                {order.updatedAt}
                            </p>
                        </div>
                        <div className="text-right">
                            <p className="text-sm text-gray-500 uppercase tracking-wide">
                                Total
                            </p>
                            <p className="text-xl font-semibold text-gray-900">
                                {formatCurrency(order.total)}
                            </p>
                            <p className="text-sm text-gray-500">
                                {order.lineItems} line items • {order.channel}
                            </p>
                        </div>
                        <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                            <span
                                className={`h-2.5 w-2.5 rounded-full ${statusCopy[order.status].dot}`}
                            />
                            {statusCopy[order.status].label}
                        </div>
                    </article>
                ))}
            </div>
        </div>
    )
}

export default OrdersView
