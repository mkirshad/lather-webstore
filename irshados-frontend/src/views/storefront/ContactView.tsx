import StorefrontLayout from './StorefrontLayout'

const services = [
    {
        title: 'Store Launch Sprint',
        details: 'Design system, catalog setup, payment config, deployment.',
        timeline: '3-4 weeks',
    },
    {
        title: 'Growth & Monitoring',
        details: 'Instrumentation, analytics, CRO testing, incident response.',
        timeline: 'Monthly retainer',
    },
    {
        title: 'Bespoke Integrations',
        details: 'ERP bridges, fulfillment automation, wholesale portals.',
        timeline: 'Scope dependent',
    },
]

const ContactView = () => {
    return (
        <StorefrontLayout>
            <section className="max-w-5xl mx-auto px-4 sm:px-6 py-16 space-y-10 bg-[#f5f5f3] text-gray-900">
                <header className="space-y-4">
                    <p className="text-xs uppercase tracking-[0.5em] text-gray-500">
                        Contact
                    </p>
                    <h1 className="text-4xl text-gray-900 font-light">
                        Book a discovery call or drop your brief.
                    </h1>
                    <p className="text-gray-600">
                        Tell us about your leather line, timeline, and tech
                        stack. We respond within 12 hours with next steps and a
                        tailored roadmap.
                    </p>
                </header>

                <div className="grid gap-8 md:grid-cols-[1.2fr_0.8fr]">
                    <form className="space-y-4 border border-gray-200 rounded-3xl p-6 bg-white shadow-md">
                        <div className="grid gap-4 sm:grid-cols-2">
                            <input
                                placeholder="Name"
                                className="px-4 py-3 rounded-full border border-gray-300 bg-white text-gray-900"
                            />
                            <input
                                placeholder="Email"
                                className="px-4 py-3 rounded-full border border-gray-300 bg-white text-gray-900"
                            />
                        </div>
                        <input
                            placeholder="Brand or company"
                            className="w-full px-4 py-3 rounded-full border border-gray-300 bg-white text-gray-900"
                        />
                        <textarea
                            placeholder="What are you building?"
                            className="w-full px-4 py-3 rounded-2xl border border-gray-300 bg-white text-gray-900 h-32"
                        />
                        <button className="w-full px-4 py-3 rounded-full bg-gray-900 text-white uppercase tracking-wide">
                            Send brief
                        </button>
                    </form>

                    <div className="space-y-4">
                        <div className="border border-gray-200 rounded-3xl p-6 bg-white shadow-md">
                            <p className="text-sm text-gray-500 uppercase tracking-widest">
                                Direct contact
                            </p>
                            <p className="text-gray-900 text-xl mt-2">
                                studio@passionatelier.com
                            </p>
                            <p className="text-gray-600">
                                WhatsApp / Signal: +92 317 000 0000
                            </p>
                        </div>
                        <div className="space-y-3">
                            {services.map((service) => (
                                <article
                                    key={service.title}
                                    className="border border-gray-200 rounded-3xl p-5 bg-white shadow-md"
                                >
                                    <h3 className="text-gray-900 text-xl">
                                        {service.title}
                                    </h3>
                                    <p className="text-gray-600">
                                        {service.details}
                                    </p>
                                    <p className="text-gray-400 text-sm">
                                        {service.timeline}
                                    </p>
                                </article>
                            ))}
                        </div>
                    </div>
                </div>
            </section>
        </StorefrontLayout>
    )
}

export default ContactView
