import StorefrontLayout from './StorefrontLayout'
import { journalEntries } from '@/data/leatherProducts'

const JournalView = () => {
    return (
        <StorefrontLayout>
            <section className="max-w-4xl mx-auto px-4 sm:px-6 py-16 space-y-10 bg-[#f5f5f3] text-gray-900">
                <header className="space-y-4">
                    <p className="text-xs uppercase tracking-[0.5em] text-gray-500">
                        Journal
                    </p>
                    <h1 className="text-4xl text-gray-900 font-light">
                        Product drops, process diaries, and monitoring updates
                    </h1>
                    <p className="text-gray-600">
                        Each entry pairs editorial storytelling with technical
                        transparency—covering craftsmanship, digital launches,
                        and uptime reports that keep clients confident.
                    </p>
                </header>

                <div className="space-y-6">
                    {journalEntries.map((entry) => (
                        <article
                            key={entry.id}
                            className="border border-gray-200 rounded-3xl p-6 bg-white space-y-3 shadow-md"
                        >
                            <p className="text-xs text-gray-500 uppercase tracking-widest">
                                {entry.published}
                            </p>
                            <h2 className="text-2xl text-gray-900">
                                {entry.title}
                            </h2>
                            <p className="text-gray-600">{entry.summary}</p>
                            <p className="text-gray-400 text-sm">
                                {entry.readingTime}
                            </p>
                        </article>
                    ))}
                </div>

                <div className="border border-gray-200 rounded-3xl p-8 grid gap-4 md:grid-cols-[2fr_1fr] bg-white shadow-lg">
                    <div>
                        <p className="text-gray-500 uppercase text-xs tracking-widest">
                            Monitoring cadence
                        </p>
                        <h3 className="text-2xl text-gray-900 mt-3">
                            Weekly vitals delivered to your inbox
                        </h3>
                        <p className="text-gray-600 mt-2">
                            Performance reports summarize conversion trends,
                            inventory risk, PWA installs, security headers, and
                            CDN metrics. Perfect for stakeholders who need a
                            concise health report.
                        </p>
                    </div>
                    <form className="space-y-3">
                        <input
                            type="email"
                            placeholder="Email address"
                            className="w-full px-4 py-3 rounded-full bg-white border border-gray-300 text-gray-900"
                        />
                        <button className="w-full px-4 py-3 rounded-full bg-gray-900 text-white uppercase tracking-wide">
                            Subscribe
                        </button>
                    </form>
                </div>
            </section>
        </StorefrontLayout>
    )
}

export default JournalView
