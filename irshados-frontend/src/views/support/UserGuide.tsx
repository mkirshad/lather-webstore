type GuideSection = {
    id: string
    title: string
    summary: string
    demoSteps: string[]
    backendRefs: string[]
    tips?: string[]
}

const guideSections: GuideSection[] = [
    {
        id: 'workspace',
        title: 'Workspace Overview',
        summary:
            'Use the dashboard to mirror the ECME demo landing page with KPIs for sales, purchasing, inventory, and POS health.',
        demoSteps: [
            'Open the Home workspace and align the date range with your Fishbowl comparison window.',
            'Click View report on a tile to drill into the same table that powers the ECME walkthrough.',
            'Customize the dashboard layout to pin shortcuts your team relies on for daily standups.',
        ],
        backendRefs: [
            'GET /api/reports/dashboard aggregates the glanceable metrics rendered on this screen.',
            'GET /api/auth/session includes the tenant and role context displayed beside your avatar.',
        ],
        tips: [
            'Save dashboard presets by role so operators, managers, and finance see the metrics that matter most.',
        ],
    },
    {
        id: 'auth',
        title: 'Authentication and Onboarding',
        summary:
            'The sign up, sign in, and invite acceptance flows mirror the ECME onboarding demo with tenant aware JWTs.',
        demoSteps: [
            'Sign up with Create a new organization to provision a tenant and seed roles in one transaction.',
            'Join an existing tenant by submitting the invite code or slug provided by an owner.',
            'Sign in with your email and tenant slug, then switch organizations from the avatar menu when needed.',
            'Trigger forgot password to receive the time boxed reset token and complete the flow from the link.',
        ],
        backendRefs: [
            'POST /api/auth/sign-up provisions tenants, default roles, and initial memberships.',
            'POST /api/auth/sign-in issues JWTs scoped by tenant with row level security enforced claims.',
            'POST /api/auth/password-reset and POST /api/auth/password-reset/confirm manage recovery with audit trails.',
        ],
        tips: [
            'Single sign on buttons reappear once the provider is re-enabled in settings.',
            'Copy the tenant slug from the invite email to avoid subtle casing differences.',
        ],
    },
    {
        id: 'inventory',
        title: 'Inventory and Products',
        summary:
            'Maintain catalog data, variants, and warehouses while syncing weighted average costing to the backend ledger.',
        demoSteps: [
            'Create a product with variants using the ECME slide over form and upload a photo or barcode if available.',
            'Bulk import SKUs by downloading the template, filling it with Fishbowl exports, and uploading the CSV.',
            'Allocate stock to bins and confirm a transfer to update on hand quantities and valuation.',
        ],
        backendRefs: [
            'POST /api/inventory/products creates products, variants, and UoM mappings in one call.',
            'POST /api/inventory/transfers publishes weighted average adjustments to the inventory ledger.',
            'GET /api/inventory/ledger exposes the same balances used in the Fishbowl parity report.',
        ],
        tips: [
            'Name bins after your Fishbowl warehouse codes to keep reconciliation straightforward.',
            'Use the inline costing preview to confirm average cost before committing bulk imports.',
        ],
    },
    {
        id: 'purchasing',
        title: 'Purchasing Lifecycle',
        summary:
            'Drive the Purchase Order to Goods Receipt to Bill to Payment flow without leaving the purchasing workspace.',
        demoSteps: [
            'Raise a purchase order and email it to the supplier straight from the grid action menu.',
            'Post a goods receipt to update inventory, trigger the costing task, and log supplier notifications.',
            'Convert the receipt to a vendor bill and settle it with the payment wizard to close the cycle.',
        ],
        backendRefs: [
            'POST /api/purchasing/orders manages the PO creation and status transitions.',
            'POST /api/purchasing/receipts enqueues Celery costing jobs and stock movements.',
            'POST /api/purchasing/payments records settlements and supplier credits.',
        ],
        tips: [
            'Reconcile the purchasing pipeline export with your finance system to spot delays early.',
            'Tag purchase orders with Fishbowl job codes using custom fields to maintain traceability.',
        ],
    },
    {
        id: 'sales',
        title: 'Sales and Invoicing',
        summary:
            'Convert quotes, ship goods, and capture cash within the kanban inspired sales workspace.',
        demoSteps: [
            'Draft a quote, attach customer specific price rules, and promote it to an order.',
            'Allocate stock from preferred warehouses before scheduling delivery or pickup.',
            'Generate an invoice, capture payment or issue a refund, and email documents to the customer.',
        ],
        backendRefs: [
            'POST /api/sales/orders manages quote, order, and delivery lifecycles.',
            'POST /api/sales/invoices handles billing, payment capture, and credit memos.',
            'GET /api/sales/performance feeds the revenue widgets that mirror ECME demo charts.',
        ],
        tips: [
            'Use automation rules to notify account managers when large orders enter the fulfilment stage.',
            'Keep the kanban stages aligned with Fishbowl pipeline steps so both systems tell the same story.',
        ],
    },
    {
        id: 'pos',
        title: 'POS and Offline Resilience',
        summary:
            'Run in store transactions with offline tolerant cart, payment, and receipt tooling inspired by the POS demo.',
        demoSteps: [
            'Select a register, confirm the starting float, and open the shift for the day.',
            'Build a cart with barcode scans or quick keys and apply customer pricing or taxes automatically.',
            'Complete payment, print or email the receipt, and close the shift with a drawer reconciliation.',
            'Stay on the page if the offline banner appears so queued transactions can sync once the signal returns.',
        ],
        backendRefs: [
            'POST /api/pos/registers/open and /close track shift cash balances.',
            'POST /api/pos/sales queues orders for sync and cost reconciliation.',
            'Websocket channel pos.tickets broadcasts KOT and KDS updates in real time.',
        ],
        tips: [
            'Install the service worker so offline cart persistence is enabled for every register device.',
            'Use the ESC POS hook for standard printers or the Sunmi placeholder to integrate with Android handhelds.',
        ],
    },
    {
        id: 'reports',
        title: 'Reporting and Analytics',
        summary:
            'Answer operational questions with ledger, margin, and exception reports that line up with Fishbowl snapshots.',
        demoSteps: [
            'Filter the inventory ledger by warehouse or bin to validate nightly counts.',
            'Export purchasing and sales pipeline summaries before finance closes the books.',
            'Schedule a cost variance report and distribute it to department heads each Monday.',
        ],
        backendRefs: [
            'GET /api/reports/inventory-ledger exposes weighted average balances per SKU.',
            'GET /api/reports/purchasing-pipeline and /sales-pipeline align with the exports in this module.',
            'POST /api/reports/subscriptions schedules recurring deliveries through Celery tasks.',
        ],
        tips: [
            'Save frequently used filters so the widgets and exports stay in sync for audits.',
            'Compare margin trends with your Fishbowl cost buckets to surface configuration drift.',
        ],
    },
    {
        id: 'support',
        title: 'Support and Next Steps',
        summary:
            'Access embedded help, contact information, and change logs without leaving the application.',
        demoSteps: [
            'Open the help icon in the header to review contextual tips for the current route.',
            'Jump to this guide from the Support menu item when you need the full DEMO walkthrough.',
            'Email support@irshados.dev with logs or paste cURL output from the backend endpoints for faster triage.',
        ],
        backendRefs: [
            'GET /api/status verifies backend health before you file a ticket.',
            'GET /api/changelog surfaces the latest feature releases referenced in the help drawer.',
        ],
        tips: [
            'Capture screenshots of the help drawer alongside any error messages so the support team can reproduce quickly.',
            'Subscribe to release notes to stay informed about new modules and POS hardware integrations.',
        ],
    },
]

const UserGuide = () => {
    return (
        <div className="flex flex-col gap-10 lg:flex-row">
            <aside className="lg:w-64">
                <div className="sticky top-24 space-y-4 rounded-xl border border-gray-200 p-4 dark:border-gray-700">
                    <div>
                        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                            Guide Menu
                        </h3>
                        <ul className="mt-3 space-y-2">
                            {guideSections.map((section) => (
                                <li key={section.id}>
                                    <a
                                        className="text-sm font-medium text-primary-600 hover:underline dark:text-primary-400"
                                        href={`#${section.id}`}
                                    >
                                        {section.title}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>
                    <div className="rounded-lg bg-primary-50 p-3 text-xs text-primary-800 dark:bg-primary-900/40 dark:text-primary-200">
                        <p className="font-semibold">Need Live Help?</p>
                        <p className="mt-1">
                            Tap the help icon in the header to open the contextual drawer for any module.
                        </p>
                    </div>
                </div>
            </aside>
            <div className="flex-1 space-y-12">
                {guideSections.map((section) => (
                    <section
                        key={section.id}
                        id={section.id}
                        className="scroll-mt-28 space-y-6"
                    >
                        <header>
                            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                                {section.title}
                            </h2>
                            <p className="mt-2 text-sm leading-relaxed text-gray-600 dark:text-gray-300">
                                {section.summary}
                            </p>
                        </header>
                        <div className="rounded-xl border border-gray-200 p-5 dark:border-gray-700">
                            <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                                Demo Walkthrough
                            </h3>
                            <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm leading-relaxed text-gray-700 dark:text-gray-200">
                                {section.demoSteps.map((step, index) => (
                                    <li key={index}>{step}</li>
                                ))}
                            </ol>
                        </div>
                        <div className="rounded-xl border border-dashed border-gray-200 p-5 dark:border-gray-700">
                            <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
                                Backend Touchpoints
                            </h3>
                            <ul className="mt-3 space-y-2 text-sm leading-relaxed text-gray-700 dark:text-gray-200">
                                {section.backendRefs.map((ref, index) => (
                                    <li key={index}>{ref}</li>
                                ))}
                            </ul>
                        </div>
                        {section.tips?.length ? (
                            <div className="rounded-xl bg-gray-900/5 p-5 text-sm text-gray-700 dark:bg-white/5 dark:text-gray-200">
                                <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-600 dark:text-gray-300">
                                    Pro Tips
                                </h3>
                                <ul className="mt-2 space-y-1">
                                    {section.tips.map((tip, index) => (
                                        <li key={index}>- {tip}</li>
                                    ))}
                                </ul>
                            </div>
                        ) : null}
                    </section>
                ))}
            </div>
        </div>
    )
}

export default UserGuide
