"""
Curated Realistic E-Commerce Sample Store Pages for Testing and Demonstration.
All sample stores are clearly labeled as sample data.
"""
from __future__ import annotations
from typing import List, Dict, Any


SAMPLE_STORES = {
    "OptiFootwear - Elite Trail Running Shoes (Optimized PDP)": {
        "is_sample_data": True,
        "sample_store_notice": "Curated E-Commerce Audit Sample Data (Fully Optimized Store)",
        "url": "https://sample-store.searchlens.internal/products/optifootwear-apex-trail-runner-black",
        "html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OptiFootwear Apex Trail Running Shoes - Waterproof Black | OptiFootwear</title>
    <meta name="description" content="Conquer all terrains with the OptiFootwear Apex Trail Runner. Features breathable waterproof Gore-Tex, Vibram grip lugs, and responsive cushioning. Free shipping.">
    <link rel="canonical" href="https://sample-store.searchlens.internal/products/optifootwear-apex-trail-runner-black">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": "OptiFootwear Apex Trail Running Shoes - Waterproof Black",
        "image": [
            "https://sample-store.searchlens.internal/images/apex-runner-main.webp",
            "https://sample-store.searchlens.internal/images/apex-runner-side.webp"
        ],
        "description": "High-performance waterproof trail running shoes designed for ultra-marathons and rugged mountainous trails.",
        "sku": "OPT-APX-TR-BLK-10",
        "mpn": "92837482",
        "brand": {
            "@type": "Brand",
            "name": "OptiFootwear"
        },
        "offers": {
            "@type": "Offer",
            "url": "https://sample-store.searchlens.internal/products/optifootwear-apex-trail-runner-black",
            "priceCurrency": "USD",
            "price": "149.99",
            "priceValidUntil": "2027-12-31",
            "itemCondition": "https://schema.org/NewCondition",
            "availability": "https://schema.org/InStock"
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.8",
            "reviewCount": "142"
        }
    }
    </script>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org/",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://sample-store.searchlens.internal/"},
            {"@type": "ListItem", "position": 2, "name": "Footwear", "item": "https://sample-store.searchlens.internal/footwear"},
            {"@type": "ListItem", "position": 3, "name": "Trail Running", "item": "https://sample-store.searchlens.internal/footwear/trail-running"},
            {"@type": "ListItem", "position": 4, "name": "Apex Trail Runner", "item": "https://sample-store.searchlens.internal/products/optifootwear-apex-trail-runner-black"}
        ]
    }
    </script>
</head>
<body>
    <header>
        <nav aria-label="breadcrumb" class="breadcrumb">
            <a href="/">Home</a> &gt; <a href="/footwear">Footwear</a> &gt; <a href="/footwear/trail-running">Trail Running</a> &gt; <span>Apex Trail Runner</span>
        </nav>
    </header>
    <main>
        <div class="product-gallery">
            <img src="/images/apex-runner-main.webp" alt="OptiFootwear Apex Trail Running Shoes in Waterproof Black - Lateral Angle" width="800" height="800">
            <img src="/images/apex-runner-side.webp" alt="OptiFootwear Apex Trail Running Shoes Vibram Sole Outsole Tread" width="800" height="800">
        </div>
        <div class="product-details">
            <h1>OptiFootwear Apex Trail Running Shoes - Waterproof Black</h1>
            <div class="product-price">$149.99</div>
            <div class="rating-badge">Rated 4.8 / 5 based on 142 reviews</div>
            <button class="add-to-cart">Add to Cart</button>
            <div id="product-desc" class="product-description">
                <h2>Engineered for Extreme Terrain Performance</h2>
                <p>The OptiFootwear Apex Trail Runner combines relentless traction, waterproof breathable Gore-Tex membranes, and responsive dual-density midsole foam. Engineered specifically for trail marathoners and weekend hikers demanding stability across muddy roots, rocky climbs, and wet scree.</p>
                <h3>Key Technical Specifications</h3>
                <ul>
                    <li>Waterproofing: Multi-layer Gore-Tex Extended Comfort Membrane</li>
                    <li>Outsole: 5mm directional Vibram Megagrip rubber lugs</li>
                    <li>Drop: 6mm heel-to-toe offset for neutral natural biomechanics</li>
                    <li>Weight: 298g (Men's US size 10)</li>
                    <li>Upper: Ripstop ballistic mesh with reinforced TPU toe bumper</li>
                </ul>
                <p>Every pair comes backed by OptiFootwear's 30-day trail guarantee and lifetime manufacturer craftsmanship warranty. Fast carbon-neutral shipping on all domestic orders.</p>
            </div>
        </div>
    </main>
    <footer>
        <p>Shipping & Returns: Free 30-day returns and exchanges on unworn shoes.</p>
    </footer>
</body>
</html>"""
    },

    "LuxeGlow Skincare - Anti-Aging Serum (Flawed PDP with SEO Errors)": {
        "is_sample_data": True,
        "sample_store_notice": "Curated E-Commerce Audit Sample Data (Flawed Store with Deliberate Technical & Ecom Issues)",
        "url": "https://sample-store.searchlens.internal/product/serum?color=gold&sort=price",
        "html": """<!DOCTYPE html>
<html>
<head>
    <title>Serum</title>
    <!-- Missing meta description, missing mobile viewport, missing self-canonical -->
    <link rel="canonical" href="http://sample-store.searchlens.internal/product/serum?color=gold&sort=price">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": "Serum",
        "description": "Skin serum"
        /* Missing offers, price, currency, availability, and SKU */
    }
    </script>
</head>
<body>
    <div class="product-container">
        <h1>Serum</h1>
        <!-- Thin 25-word description -->
        <div class="product-desc">
            <p>Our serum is good for wrinkles. Put it on your face every night before bed for best results. Buy now online today.</p>
        </div>
        <!-- Images without alt text and using legacy formats -->
        <img src="serum_bottle.jpg">
        <img src="serum_box.png">
        <div class="price">$89.00</div>
        <button class="add-to-cart">Buy Now</button>
        <!-- Missing breadcrumbs, missing shipping info, faceted URL with self-canonical -->
    </div>
</body>
</html>"""
    },

    "PeakGear Outdoor Store - Men's Hiking Apparel (PLP Category Page)": {
        "is_sample_data": True,
        "sample_store_notice": "Curated E-Commerce Audit Sample Data (Category Listing Page)",
        "url": "https://sample-store.searchlens.internal/category/mens-hiking-apparel",
        "html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Men's Hiking Apparel & Outdoor Clothing | PeakGear</title>
    <meta name="description" content="Shop durable Men's Hiking Apparel at PeakGear. Discover breathable trail shirts, waterproof trekking pants, and lightweight weather-resistant jackets. Free delivery over $75.">
    <link rel="canonical" href="https://sample-store.searchlens.internal/category/mens-hiking-apparel">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org/",
        "@type": "CollectionPage",
        "name": "Men's Hiking Apparel",
        "description": "High-durability technical apparel designed for alpine hiking and outdoor adventures."
    }
    </script>
</head>
<body>
    <header>
        <nav class="breadcrumb">
            <a href="/">Home</a> &gt; <a href="/apparel">Apparel</a> &gt; <span>Men's Hiking</span>
        </nav>
    </header>
    <main>
        <h1>Men's Technical Hiking Apparel</h1>
        <div class="category-description">
            <p>Explore PeakGear's rugged collection of men's hiking clothes built for unpredictable mountain weather. From moisture-wicking merino base layers to abrasion-resistant ripstop trekking pants and packable rain shells, our apparel delivers freedom of movement and enduring weather defense on every expedition.</p>
        </div>
        <div class="product-grid">
            <div class="product-card">
                <img src="/images/summit-pant.webp" alt="PeakGear Summit Flex Trekking Pant - Slate Grey">
                <h2>Summit Flex Trekking Pant</h2>
                <div class="price">$119.00</div>
            </div>
            <div class="product-card">
                <img src="/images/alpine-shell.webp" alt="PeakGear Alpine Wind & Rain Shell - Burnt Orange">
                <h2>Alpine Wind & Rain Shell</h2>
                <div class="price">$189.00</div>
            </div>
            <div class="product-card">
                <img src="/images/merino-tee.webp" alt="PeakGear Active Trail Merino T-Shirt - Forest Green">
                <h2>Active Trail Merino T-Shirt</h2>
                <div class="price">$65.00</div>
            </div>
        </div>
        <div class="pagination">
            <span>Page 1 of 4</span>
        </div>
    </main>
    <footer>
        <p>Free standard shipping on orders over $75. 60-day satisfaction guarantee.</p>
    </footer>
</body>
</html>"""
    }
}


def get_sample_store_names() -> List[str]:
    return list(SAMPLE_STORES.keys())


def load_sample_store(name: str) -> Dict[str, Any]:
    return SAMPLE_STORES.get(name, {})
