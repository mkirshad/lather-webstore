import { Link, NavLink } from 'react-router'
import { useMemo, type PropsWithChildren } from 'react'
import { useCartStore } from '@/store/cartStore'
import { formatCurrency } from '@/utils/currency'

const navItems = [
    { label: 'Collections', href: '/collections' },
    { label: 'Journal', href: '/journal' },
    { label: 'About', href: '/about' },
    { label: 'Contact', href: '/contact' },
]

const StorefrontLayout = ({ children }: PropsWithChildren) => {
    const cartItems = useCartStore((state) => state.items)
    const cartSummary = useMemo(() => {
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

    return (
        <div className="min-h-screen bg-[#0e0c0a] text-white">
            <div className="bg-[#c19977] text-black text-sm tracking-wide py-2 text-center">
                Studio slots open for holiday bespoke orders. Complimentary
                worldwide shipping through December 31.
            </div>

            <header className="sticky top-0 z-40 border-b border-white/10 bg-[#0e0c0a]/80 backdrop-blur">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 py-5 flex items-center justify-between gap-4">
                    <Link
                        to="/"
                        className="font-semibold tracking-[0.4em] uppercase text-sm"
                    >
                        Passion Atelier
                    </Link>
                    <nav className="hidden md:flex gap-6 text-sm tracking-wide">
                        {navItems.map((item) => (
                            <NavLink
                                key={item.href}
                                to={item.href}
                                className={({ isActive }) =>
                                    [
                                        'transition-colors',
                                        isActive
                                            ? 'text-[#c19977]'
                                            : 'text-white/70 hover:text-white',
                                    ].join(' ')
                                }
                            >
                                {item.label}
                            </NavLink>
                        ))}
                    </nav>
                    <div className="flex items-center gap-3 text-sm">
                        <NavLink
                            to="/sign-in"
                            className="hidden lg:inline-flex px-4 py-2 border border-white/30 rounded-full text-white/80 hover:text-white transition"
                        >
                            Admin Portal
                        </NavLink>
                        <NavLink
                            to="/collections"
                            className="hidden sm:inline-flex px-4 py-2 border border-white/30 rounded-full text-white/80 hover:text-white hover:border-white transition"
                        >
                            View Store
                        </NavLink>
                        <NavLink
                            to="/contact"
                            className="hidden sm:inline-flex px-4 py-2 rounded-full bg-white text-black hover:bg-[#c19977] hover:text-black transition"
                        >
                            Book Atelier Call
                        </NavLink>
                        <div className="relative px-4 py-2 border border-white/20 rounded-full">
                            <span className="text-xs uppercase tracking-wider text-white/60">
                                Cart
                            </span>
                            <div className="flex items-center gap-2 text-white">
                                <span className="text-lg font-semibold">
                                    {cartSummary.itemCount}
                                </span>
                                <span className="text-xs text-white/60">
                                    {formatCurrency(cartSummary.subtotal)}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </header>

            <main className="bg-[#f5f5f3] text-gray-900">{children}</main>

            <footer className="border-t border-white/5 mt-16 bg-[#0e0c0a] text-white">
                <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12 grid gap-8 md:grid-cols-3 text-sm">
                    <div>
                        <p className="uppercase tracking-[0.3em] text-xs text-white/60 mb-4">
                            Passion Atelier
                        </p>
                        <p className="text-white/70 leading-relaxed">
                            Leather accessories hand-built in Lahore and
                            Florence. Monitoring dashboards keep production,
                            fulfillment, and site security observable 24/7.
                        </p>
                        <NavLink
                            to="/sign-in"
                            className="inline-flex mt-4 px-5 py-2 rounded-full border border-white/30 text-white/80 hover:text-white"
                        >
                            Admin Portal →
                        </NavLink>
                    </div>
                    <div>
                        <p className="text-white/80 font-medium mb-2">
                            Studio Hours
                        </p>
                        <p className="text-white/60">
                            Monday - Saturday, 9am to 9pm PKT
                            <br />
                            Remote consults across UTC-8 to UTC+8
                        </p>
                    </div>
                    <div>
                        <p className="text-white/80 font-medium mb-2">
                            Monitoring & Deployment
                        </p>
                        <ul className="text-white/60 space-y-1">
                            <li>Automated Lighthouse audits per release</li>
                            <li>Cloudflare + Supabase edge logs streaming</li>
                            <li>PagerDuty alerts tied to vitals</li>
                        </ul>
                    </div>
                </div>
                <div className="text-center text-white/50 text-xs py-6 border-t border-white/5">
                    © {new Date().getFullYear()} Passion Atelier. Crafted for
                    the Upwork showcase.
                </div>
            </footer>
        </div>
    )
}

export default StorefrontLayout
