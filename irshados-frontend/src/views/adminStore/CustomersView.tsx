import { adminCustomers } from '@/data/adminStore'
import { formatCurrency } from '@/utils/currency'

const CustomersView = () => {
    return (
        <div className="space-y-6">
            <header className="space-y-2">
                <h1 className="text-2xl font-semibold text-gray-900">
                    Customer cohorts
                </h1>
                <p className="text-gray-600 max-w-2xl">
                    Demo how high-touch wholesale partners sit next to D2C VIPs.
                    Each entry can pull live metrics from Django once the CRM
                    endpoints are online.
                </p>
            </header>
            <div className="border border-gray-200 rounded-2xl overflow-hidden bg-white">
                <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-500 uppercase text-xs">
                        <tr>
                            <th className="text-left px-5 py-3 font-medium">
                                Customer
                            </th>
                            <th className="text-left px-5 py-3 font-medium">
                                Channel
                            </th>
                            <th className="text-left px-5 py-3 font-medium">
                                Last order
                            </th>
                            <th className="text-left px-5 py-3 font-medium">
                                Lifetime value
                            </th>
                        </tr>
                    </thead>
                    <tbody>
                        {adminCustomers.map((customer) => (
                            <tr
                                key={customer.id}
                                className="border-t border-gray-100"
                            >
                                <td className="px-5 py-4">
                                    <p className="font-semibold text-gray-900">
                                        {customer.name}
                                    </p>
                                    <p className="text-gray-500">
                                        {customer.location}
                                    </p>
                                    <p className="text-gray-400">
                                        {customer.email}
                                    </p>
                                </td>
                                <td className="px-5 py-4 text-gray-600">
                                    {customer.channel}
                                </td>
                                <td className="px-5 py-4 text-gray-500">
                                    {customer.lastOrder}
                                </td>
                                <td className="px-5 py-4 font-semibold text-gray-900">
                                    {formatCurrency(customer.lifetimeValue)}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default CustomersView
