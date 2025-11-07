export type HelpTopic = {
    key: string
    title: string
    summary: string
    bullets: string[]
    links?: { label: string; path?: string }[]
}

export const defaultHelpTopicKey = 'home'

export const helpTopics: HelpTopic[] = [
    {
        key: 'home',
        title: 'Workspace Overview',
        summary:
            'The home dashboard surfaces glanceable metrics for sales, purchasing, inventory, and POS status.',
        bullets: [
            'Use the range selector to compare performance with previous periods.',
            'Hover over any widget to reveal quick links to the underlying report.',
            'Switch tenants from the avatar menu whenever you need to impersonate another workspace.',
        ],
        links: [
            {
                label: 'Read the workspace quick start',
                path: '/support/user-guide#workspace',
            },
        ],
    },
    {
        key: 'signIn',
        title: 'Sign In',
        summary:
            'Authenticate with your tenant slug and email to unlock protected workspaces.',
        bullets: [
            'Supply the tenant slug so the platform can scope your session.',
            'Usernames mirror the email address and fill in automatically.',
            'If your admin enabled SSO, click the provider button when it is re-enabled.',
        ],
        links: [
            {
                label: 'Authentication walkthrough',
                path: '/support/user-guide#auth',
            },
        ],
    },
    {
        key: 'signUp',
        title: 'Create an Account',
        summary:
            'Spin up a tenant or join an existing one with invitation-aware onboarding.',
        bullets: [
            'Pick Create a new organization to provision a tenant in one step.',
            'Joining an existing tenant makes you a member until an owner promotes you.',
            'Invite accept flows reconcile role requests with backend audit trails.',
        ],
        links: [
            {
                label: 'Authentication walkthrough',
                path: '/support/user-guide#auth',
            },
        ],
    },
    {
        key: 'forgotPassword',
        title: 'Forgot Password',
        summary:
            'Request a reset link that expires according to your tenant security policy.',
        bullets: [
            'Enter the email that was verified on your account.',
            'Check the reset email for the short lived token and submit it before expiry.',
            'If the email does not arrive, confirm spam filters or contact an administrator.',
        ],
        links: [
            {
                label: 'Authentication walkthrough',
                path: '/support/user-guide#auth',
            },
        ],
    },
    {
        key: 'resetPassword',
        title: 'Reset Password',
        summary:
            'Set a new password that satisfies the tenant policy and logs you back in automatically.',
        bullets: [
            'Paste the reset token from the email or use the deep link to pre-fill it.',
            'Passwords must meet the configured strength rules before submission.',
            'Successful resets rotate existing sessions and sign you in with the new credentials.',
        ],
        links: [
            {
                label: 'Authentication walkthrough',
                path: '/support/user-guide#auth',
            },
        ],
    },
    {
        key: 'inventory.products',
        title: 'Products and Variants',
        summary:
            'Create, edit, or bulk import catalog items that sync with weighted average costing in the backend.',
        bullets: [
            'Use New Product to open the ECME style slide over form with inline validation.',
            'Import CSV files that match the downloadable template for quick onboarding.',
            'Scan a barcode to populate variant details and queue the related stock lookup.',
        ],
        links: [
            {
                label: 'Inventory operations guide',
                path: '/support/user-guide#inventory',
            },
        ],
    },
    {
        key: 'inventory.warehouses',
        title: 'Warehouses and Transfers',
        summary:
            'Manage stocking locations, bins, and transfer orders that feed the inventory ledger.',
        bullets: [
            'Toggle Show inactive to reveal archived locations before reactivating them.',
            'Draft a transfer to move stock between bins and submit it to post adjusted quantities.',
            'Export the ledger to reconcile counts with Fishbowl warehouse reports.',
        ],
        links: [
            {
                label: 'Inventory operations guide',
                path: '/support/user-guide#inventory',
            },
        ],
    },
    {
        key: 'purchasing.orders',
        title: 'Purchasing',
        summary:
            'Walk through the PO to GRN to Bill to Payment flow directly from a single workspace.',
        bullets: [
            'Use the status tabs to filter open versus received purchase orders.',
            'Posting a receipt calls the costing service and emails suppliers automatically.',
            'Download the pipeline summary that mirrors the /api/reports/purchasing-pipeline endpoint.',
        ],
        links: [
            {
                label: 'Purchasing operations guide',
                path: '/support/user-guide#purchasing',
            },
        ],
    },
    {
        key: 'sales.orders',
        title: 'Sales Orders and Invoices',
        summary:
            'Convert quotes, allocate stock, and capture payments without leaving the sales pipeline.',
        bullets: [
            'Drag cards between kanban stages to update the order status in real time.',
            'Generate delivery notes or invoices from the actions menu tied to /api/sales endpoints.',
            'Process refunds through the Payments tab which respects staff permission scopes.',
        ],
        links: [
            {
                label: 'Sales operations guide',
                path: '/support/user-guide#sales',
            },
        ],
    },
    {
        key: 'pos.sales',
        title: 'POS Register',
        summary:
            'Touch friendly order entry that works offline and syncs to the backend queue once connected.',
        bullets: [
            'Pick a register to load the cash drawer state and active shift.',
            'An offline badge turns yellow when IndexedDB queues receipts that still need to sync.',
            'Print receipts from ESC POS printers on desktop or the Sunmi integration placeholder on Android.',
        ],
        links: [
            {
                label: 'POS quick start',
                path: '/support/user-guide#pos',
            },
        ],
    },
    {
        key: 'reports.analytics',
        title: 'Reports and Analytics',
        summary:
            'Track operational insights with ledger, cost, and performance reports that mirror backend APIs.',
        bullets: [
            'Use filters and saved views to replay the same query during audits.',
            'Export CSV snapshots for reconciliation or further modelling outside the app.',
            'Cross check numbers with the backend reports endpoints when investigating variances.',
        ],
        links: [
            {
                label: 'Reporting guide',
                path: '/support/user-guide#reports',
            },
        ],
    },
    {
        key: 'support.userGuide',
        title: 'In App User Guide',
        summary:
            'Browse the full DEMO playbook, including onboarding, inventory, sales, purchasing, POS, and reporting scenarios.',
        bullets: [
            'Use the left menu to jump straight to a module specific tutorial.',
            'Each section links back to the backend endpoint for deeper troubleshooting.',
            'Reach out via the support email at the bottom of the panel if you still need assistance.',
        ],
        links: [
            {
                label: 'Open the user guide',
                path: '/support/user-guide',
            },
        ],
    },
]
