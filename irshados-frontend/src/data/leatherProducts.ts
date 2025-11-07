export type ProductCategory =
    | 'bags'
    | 'wallets'
    | 'belts'
    | 'travel'
    | 'accessories'

export type ProductColor = {
    name: string
    hex: string
}

export type LeatherProduct = {
    id: string
    name: string
    slug: string
    tagline: string
    description: string
    craftsmanship: string[]
    price: number
    currency: 'USD'
    category: ProductCategory
    badge?: string
    bestseller?: boolean
    madeToOrder?: boolean
    heroImage: string
    lifestyleImage: string
    detailImages: string[]
    materials: string[]
    colors: ProductColor[]
    sizes?: string[]
    leadTime: string
    rating: number
    reviews: number
    stockStatus: string
}

export type CollectionHighlight = {
    title: string
    summary: string
    image: string
    pill: string
}

export type AtelierMetric = {
    label: string
    value: string
    helper: string
}

export type Testimonial = {
    quote: string
    author: string
    location: string
}

export type JournalEntry = {
    id: string
    title: string
    summary: string
    readingTime: string
    published: string
}

export const leatherProducts: LeatherProduct[] = [
    {
        id: 'lp-01',
        name: 'Palermo Weekender',
        slug: 'palermo-weekender',
        tagline: 'Hand-finished over 36 hours for the perfect getaway',
        description:
            'Our best-selling weekender balances structure and softness using Tuscan full-grain leather, reinforced edges, and a suede-lined interior with modular pockets.',
        craftsmanship: [
            'Edge-painted and burnished by hand',
            'Floating laptop sleeve with suede wrap',
            'Removable shoe compartment with ventilation',
        ],
        price: 890,
        currency: 'USD',
        category: 'travel',
        badge: 'Signature best seller',
        bestseller: true,
        madeToOrder: false,
        heroImage:
            'https://images.unsplash.com/photo-1507679799987-c73779587ccf?auto=format&fit=crop&w=1200&q=80',
        lifestyleImage:
            'https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1200&q=80',
        detailImages: [
            'https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=800&q=80',
        ],
        materials: [
            'Full-grain vegetable-tanned leather',
            'Brushed brass hardware sourced in Florence',
            'Japanese YKK Excella zippers',
        ],
        colors: [
            { name: 'Cuoio', hex: '#a97843' },
            { name: 'Espresso', hex: '#3f2a24' },
            { name: 'Noir', hex: '#1b1b1b' },
        ],
        leadTime: 'Ships in 3 days',
        rating: 4.9,
        reviews: 182,
        stockStatus: 'Ready to ship',
    },
    {
        id: 'lp-02',
        name: 'Luna Saddle Bag',
        slug: 'luna-saddle-bag',
        tagline: 'An equestrian silhouette reimagined for city hours',
        description:
            'The Luna is sculpted on a wooden form, giving it signature curves, then finished with French binding that keeps the profile feather-light yet resilient.',
        craftsmanship: [
            'Curved flap stitched with waxed linen',
            'Adjustable strap with hidden micro-padding',
            'Magnetic closure tuned for silent use',
        ],
        price: 540,
        currency: 'USD',
        category: 'bags',
        badge: 'New drop',
        bestseller: true,
        heroImage:
            'https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1200&q=80',
        lifestyleImage:
            'https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=1200&q=80',
        detailImages: [
            'https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=800&q=80',
            'https://images.unsplash.com/photo-1456926631375-92c8ce872def?auto=format&fit=crop&w=800&q=80',
        ],
        materials: [
            'French calfskin exterior',
            'Italian Alcantara interior',
            'Custom polished brass buckle',
        ],
        colors: [
            { name: 'Terracotta', hex: '#a1532f' },
            { name: 'Sable', hex: '#6a4a33' },
            { name: 'Jet', hex: '#1c1b19' },
        ],
        leadTime: 'Ships in 5 days',
        rating: 4.8,
        reviews: 96,
        stockStatus: 'Ready to ship',
    },
    {
        id: 'lp-03',
        name: 'Atlas Travel Wallet',
        slug: 'atlas-travel-wallet',
        tagline: 'Secure every border crossing with RFID-lined compartments',
        description:
            'Atlas combines the functionality of a travel folio and the slimness of a wallet. Two passport sleeves, a removable card caddy, and a lay-flat boarding pass pocket make it a frequent flyer essential.',
        craftsmanship: [
            'RFID-blocking German lining',
            'Hand-rolled edges for zero bulk',
            'Magnetically docked card wallet',
        ],
        price: 260,
        currency: 'USD',
        category: 'accessories',
        heroImage:
            'https://images.unsplash.com/photo-1522312346375-d1a52e2b99b3?auto=format&fit=crop&w=1200&q=80',
        lifestyleImage:
            'https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1200&q=80',
        detailImages: [
            'https://images.unsplash.com/photo-1475180098004-ca77a66827be?auto=format&fit=crop&w=800&q=80',
        ],
        materials: [
            'Italian pebbled leather exterior',
            'RFID-safe technical textile',
            'Seven-ply bonded thread',
        ],
        colors: [
            { name: 'Umber', hex: '#5c4032' },
            { name: 'Ink', hex: '#0f1a2b' },
        ],
        sizes: ['Compact', 'Continental'],
        leadTime: 'Ships next day',
        rating: 4.7,
        reviews: 141,
        stockStatus: 'Ready to ship',
    },
    {
        id: 'lp-04',
        name: 'Monaco Attaché',
        slug: 'monaco-attache',
        tagline: 'Boardroom presence with aviation-grade reinforcement',
        description:
            'Structured briefcase with a rigid frame wrapped in matte calfskin. Inside sits a microfiber tech core with modular panels for chargers, tablets, and fountain pens.',
        craftsmanship: [
            'Ultralight aluminum frame',
            'Drop-proof microfiber cradle',
            'Detachable shoulder sling with memory foam',
        ],
        price: 1120,
        currency: 'USD',
        category: 'bags',
        badge: 'Limited batch',
        madeToOrder: true,
        heroImage:
            'https://images.unsplash.com/photo-1484519332611-516457305ff6?auto=format&fit=crop&w=1200&q=80',
        lifestyleImage:
            'https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=1200&q=80',
        detailImages: [
            'https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=800&q=80',
        ],
        materials: [
            'Semi-aniline calfskin',
            'Microfiber tech lining',
            'PVD-coated gunmetal hardware',
        ],
        colors: [
            { name: 'Graphite', hex: '#2b2b2b' },
            { name: 'Stone', hex: '#7a736b' },
        ],
        leadTime: 'Made to order in 12 days',
        rating: 4.95,
        reviews: 58,
        stockStatus: 'Made to order',
    },
    {
        id: 'lp-05',
        name: 'Sienna Card Folio',
        slug: 'sienna-card-folio',
        tagline: 'Featherweight profile with reinforced spine',
        description:
            'Carries eight cards plus folded currency without stretching. The Sienna is skived down to 1mm at the folds, then edge-painted six times for a rich luster.',
        craftsmanship: [
            'Thermo-bonded cash sleeve',
            'Zero-stitch fold closure',
            'Waxed edge finish for patina',
        ],
        price: 150,
        currency: 'USD',
        category: 'wallets',
        heroImage:
            'https://images.unsplash.com/photo-1470309864661-68328b2cd0a5?auto=format&fit=crop&w=1200&q=80',
        lifestyleImage:
            'https://images.unsplash.com/photo-1472417583565-62e7bdeda490?auto=format&fit=crop&w=1200&q=80',
        detailImages: [
            'https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=800&q=80',
        ],
        materials: [
            'Full-grain goat leather',
            'Tone-on-tone microfiber lining',
        ],
        colors: [
            { name: 'Amber', hex: '#b46a3c' },
            { name: 'Oxblood', hex: '#4a1f1c' },
        ],
        leadTime: 'Ships in 2 days',
        rating: 4.6,
        reviews: 204,
        stockStatus: 'Ready to ship',
    },
    {
        id: 'lp-06',
        name: 'Cordova Harness Belt',
        slug: 'cordova-harness-belt',
        tagline: 'Vegetable-tanned strap that molds to its wearer',
        description:
            'Cut from a single hide and edge-finished with beeswax. The Cordova includes both polished brass and matte gunmetal buckles for seasonless styling.',
        craftsmanship: [
            'Hot-stuffed leather treated with oils',
            'Removable buckle system',
            'Seven-hole micro-adjust spacing',
        ],
        price: 220,
        currency: 'USD',
        category: 'belts',
        heroImage:
            'https://images.unsplash.com/photo-1469334031218-e382a71b716b?auto=format&fit=crop&w=1200&q=80',
        lifestyleImage:
            'https://images.unsplash.com/photo-1475180098004-ca77a66827be?auto=format&fit=crop&w=1200&q=80',
        detailImages: [
            'https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=800&q=80',
        ],
        materials: [
            '2.8mm vegetable-tanned leather',
            'Detachable hardware set',
        ],
        colors: [
            { name: 'Chestnut', hex: '#6d3d25' },
            { name: 'Black', hex: '#1a1917' },
        ],
        sizes: ['S', 'M', 'L', 'XL'],
        leadTime: 'Ships next day',
        rating: 4.85,
        reviews: 76,
        stockStatus: 'Ready to ship',
    },
]

export const collectionHighlights: CollectionHighlight[] = [
    {
        title: 'Atelier Essentials',
        summary:
            'Daily companions focused on organization, from structured totes to zero-bulk wallets with RFID shielding.',
        image:
            'https://images.unsplash.com/photo-1522312346375-d1a52e2b99b3?auto=format&fit=crop&w=900&q=80',
        pill: 'Everyday carry',
    },
    {
        title: 'Voyage Editions',
        summary:
            'Travel pieces engineered with reinforced panels, removable shoe compartments, and storm-proof hardware.',
        image:
            'https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=900&q=80',
        pill: 'Travel ready',
    },
    {
        title: 'Made-to-Measure',
        summary:
            'Bespoke program for belts, folios, and executive accessories sculpted to exact specifications.',
        image:
            'https://images.unsplash.com/photo-1472417583565-62e7bdeda490?auto=format&fit=crop&w=900&q=80',
        pill: 'By appointment',
    },
]

export const atelierMetrics: AtelierMetric[] = [
    { label: 'Bespoke orders delivered', value: '2.4K', helper: 'Since 2019' },
    { label: 'Average lead time', value: '5.2 days', helper: 'Ready-to-ship' },
    { label: 'Global on-time rate', value: '98%', helper: 'Tracked deliveries' },
    { label: 'Client satisfaction', value: '4.9 / 5', helper: 'Verified reviews' },
]

export const testimonials: Testimonial[] = [
    {
        quote:
            'The Palermo Weekender survived six countries and still looks showroom fresh. The modular interior is the smartest layout I have seen.',
        author: 'Maya Ren',
        location: 'Los Angeles, USA',
    },
    {
        quote:
            'I commissioned a made-to-measure Cordova belt for my wardrobe clients. The patina and fit rival heritage houses at double the price.',
        author: 'Luca Moretti',
        location: 'Milan, Italy',
    },
    {
        quote:
            'Passion Atelier kept me updated from pattern cutting to final QA. Transparency plus impeccable finishing made me a loyal customer.',
        author: 'Rachel Singh',
        location: 'Singapore',
    },
]

export const journalEntries: JournalEntry[] = [
    {
        id: 'journal-01',
        title: 'Tracing the Journey of Vegetable-Tanned Leather',
        summary:
            'We visit Tuscan tanneries to document how slow tanning techniques create richer hues and longer-lasting finishes.',
        readingTime: '6 min read',
        published: 'Nov 2, 2025',
    },
    {
        id: 'journal-02',
        title: 'Designing the Palermo: From Sketch to Final Stitch',
        summary:
            'A behind-the-scenes look at the Palermo prototyping sprint, including newfound ways to lighten the frame without sacrificing strength.',
        readingTime: '8 min read',
        published: 'Oct 21, 2025',
    },
    {
        id: 'journal-03',
        title: 'How We Monitor Craft and Delivery in Real Time',
        summary:
            'Our internal dashboard blends production telemetry with carrier data to keep promise dates honest and customer care proactive.',
        readingTime: '5 min read',
        published: 'Oct 8, 2025',
    },
]
