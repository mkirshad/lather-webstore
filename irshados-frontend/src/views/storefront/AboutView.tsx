import StorefrontLayout from './StorefrontLayout'
import { atelierMetrics } from '@/data/leatherProducts'

const AboutView = () => {
    return (
        <StorefrontLayout>
            <section className="max-w-5xl mx-auto px-4 sm:px-6 py-16 space-y-10 bg-[#f5f5f3] text-gray-900">
                <header className="space-y-4">
                    <p className="text-xs uppercase tracking-[0.5em] text-gray-500">
                        About Passion Atelier
                    </p>
                    <h1 className="text-4xl text-gray-900 font-light">
                        A leather studio with product, UX, and DevOps under one
                        roof.
                    </h1>
                    <p className="text-gray-600">
                        Inspired by passionleathers.com, this demo proves how we
                        design, build, deploy, and monitor a premium storefront
                        using modern tooling. Whether you need a D2C experience
                        or a B2B portal, the foundation is ready.
                    </p>
                </header>

                <section className="grid gap-6 md:grid-cols-2">
                    <article className="border border-gray-200 rounded-3xl p-6 space-y-3 bg-white shadow-md">
                        <h2 className="text-2xl text-gray-900">Craft Studio</h2>
                        <p className="text-gray-600">
                            Two studios between Lahore and Florence prototype,
                            cut, and finish every piece. We rely on weighted QC
                            checklists stored in the IrshadOS backend to keep
                            retail partners confident.
                        </p>
                    </article>
                    <article className="border border-gray-200 rounded-3xl p-6 space-y-3 bg-white shadow-md">
                        <h2 className="text-2xl text-gray-900">Digital Ops</h2>
                        <p className="text-gray-600">
                            Vite + React + Tailwind for the front-end, Django
                            API for orders, Supabase for analytics, Workbox for
                            offline carts, and PWA install prompts for mobile
                            reps.
                        </p>
                    </article>
                </section>

                <section className="grid gap-4 md:grid-cols-4">
                    {atelierMetrics.map((metric) => (
                        <div
                            key={metric.label}
                            className="border border-gray-200 rounded-3xl p-5 bg-white shadow-sm"
                        >
                            <p className="text-3xl text-gray-900 font-light">
                                {metric.value}
                            </p>
                            <p className="text-gray-600">{metric.label}</p>
                            <p className="text-gray-400 text-xs">
                                {metric.helper}
                            </p>
                        </div>
                    ))}
                </section>

                <section className="border border-gray-200 rounded-3xl p-8 space-y-4 bg-white shadow-md">
                    <h2 className="text-2xl text-gray-900">Engagement Model</h2>
                    <ul className="text-gray-600 space-y-2">
                        <li>• UX + creative direction aligned to your brand DNA</li>
                        <li>• Headless commerce ready (Shopify, Saleor, Medusa)</li>
                        <li>• Deployment playbooks for Vercel, AWS, Render</li>
                        <li>• Monitoring via Sentry, Logtail, and RUM dashboards</li>
                    </ul>
                </section>
            </section>
        </StorefrontLayout>
    )
}

export default AboutView
