"""
SearchLens E-Commerce SEO Suite
Performs specialized audits for Product Detail Pages (PDP) and Product Listing Pages (PLP).
Analyzes e-commerce title formulas, schema completeness, missing commercial attributes,
image optimization, category-to-product internal linking, and faceted duplicate risks.
"""
from __future__ import annotations

import re
import json
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup


class EcommerceAnalyzer:
    """
    Audits e-commerce specific SEO signals for Product Detail Pages (PDP)
    and Product Listing / Category Pages (PLP).
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def audit_page(self, soup: BeautifulSoup, url: str, raw_html: str = "") -> Dict[str, Any]:
        """
        Analyzes the given page HTML and URL for e-commerce SEO factors.
        """
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        query = parsed_url.query

        # 1. Detect page archetype
        archetype = self._detect_archetype(soup, path)

        # 2. Extract structured data
        schemas = self._extract_schemas(soup)
        product_schema = schemas.get("Product")
        breadcrumb_schema = schemas.get("BreadcrumbList")

        # 3. Analyze PDP if product page, or PLP if category page
        issues: List[Dict[str, Any]] = []
        pdp_metrics = {}
        plp_metrics = {}

        if archetype == "Product Detail Page (PDP)":
            pdp_metrics = self._analyze_pdp(soup, url, product_schema, issues)
        elif archetype == "Product Listing / Category Page (PLP)":
            plp_metrics = self._analyze_plp(soup, url, breadcrumb_schema, issues)
        else:
            # General e-commerce checks
            self._check_general_ecom(soup, url, issues)

        # 4. Faceted Navigation & Query Parameter Duplication Check
        faceted_risk = self._check_faceted_navigation(parsed_url, soup, issues)

        # 5. Image optimization for e-commerce
        image_metrics = self._audit_product_images(soup, issues)

        # Calculate e-commerce SEO health score (0-100)
        total_deductions = sum(
            15 if i.get("severity") == "error" else (8 if i.get("severity") == "warning" else 3)
            for i in issues
        )
        ecom_score = max(20, 100 - total_deductions)

        return {
            "archetype": archetype,
            "ecom_seo_score": ecom_score,
            "has_product_schema": product_schema is not None,
            "has_breadcrumb_schema": breadcrumb_schema is not None,
            "pdp_metrics": pdp_metrics,
            "plp_metrics": plp_metrics,
            "image_metrics": image_metrics,
            "faceted_navigation_risk": faceted_risk,
            "issues": issues,
            "issues_count": len(issues),
            "is_ecommerce": archetype != "General Non-Product Page"
        }

    def _detect_archetype(self, soup: BeautifulSoup, path: str) -> str:
        # Check schemas
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                types = []
                if isinstance(data, dict):
                    types = [data.get("@type")]
                    if "@graph" in data and isinstance(data["@graph"], list):
                        types = [item.get("@type") for item in data["@graph"] if isinstance(item, dict)]
                types_str = " ".join([str(t) for t in types if t])
                if "Product" in types_str:
                    return "Product Detail Page (PDP)"
                if "CollectionPage" in types_str or "ItemList" in types_str:
                    return "Product Listing / Category Page (PLP)"
            except Exception:
                pass

        # Check URL path patterns
        if any(p in path for p in ["/product/", "/p/", "/item/", "/goods/", "/dp/"]):
            return "Product Detail Page (PDP)"
        if any(p in path for p in ["/category/", "/collection/", "/shop/", "/catalog/", "/c/"]):
            return "Product Listing / Category Page (PLP)"

        # Check DOM cues
        if soup.find(attrs={"id": re.compile(r"add-to-cart|buy-now|product-price", re.I)}) or \
           soup.find(attrs={"class": re.compile(r"add-to-cart|buy-now|product-detail", re.I)}):
            return "Product Detail Page (PDP)"

        if soup.find(attrs={"class": re.compile(r"product-grid|product-list|category-products", re.I)}):
            return "Product Listing / Category Page (PLP)"

        return "General Non-Product Page"

    def _extract_schemas(self, soup: BeautifulSoup) -> Dict[str, Any]:
        found = {}
        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                data = json.loads(script.string.strip())
                items = data.get("@graph", [data]) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                for item in items:
                    if isinstance(item, dict):
                        stype = item.get("@type")
                        if isinstance(stype, list):
                            stype = stype[0] if stype else "Unknown"
                        if isinstance(stype, str):
                            clean_t = stype.split("/")[-1]
                            found[clean_t] = item
            except Exception:
                pass
        return found

    def _analyze_pdp(self, soup: BeautifulSoup, url: str, product_schema: Optional[Dict[str, Any]], issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        h1 = soup.find("h1")
        h1_text = h1.get_text(strip=True) if h1 else ""
        title_tag = soup.find("title")
        title_text = title_tag.get_text(strip=True) if title_tag else ""

        # Title Formula Evaluation: [Brand] + [Model/Product] + [Key Feature] + [Variant]
        has_brand_in_title = bool(re.search(r"(\bby\b|\bbrand\b|\bfrom\b|[-|–—])", title_text, re.I))
        has_specs_in_title = bool(re.search(r"\b(\d+gb|\d+ml|\d+kg|\d+oz|black|white|blue|red|size\s*\d+|large|small|pro|max)\b", title_text, re.I))

        # Check Description Length in PDP
        desc_container = soup.find(attrs={"id": re.compile(r"description|product-desc|details", re.I)}) or \
                         soup.find(attrs={"class": re.compile(r"description|product-desc|details|product-overview", re.I)})
        desc_text = desc_container.get_text(separator=" ", strip=True) if desc_container else ""
        desc_words = len(desc_text.split()) if desc_text else 0

        if desc_words < 100:
            issues.append({
                "code": "ECOM_THIN_PRODUCT_DESC",
                "title": f"Thin Product Description ({desc_words} words)",
                "severity": "warning",
                "explanation": "Product descriptions under 100 words fail to answer buyer objections, provide specification clarity, and lack topical depth for search engines.",
                "recommended_fix": "Expand product copy to at least 150-300 words with key benefits, materials/ingredients, dimensions, and usage instructions."
            })

        # Structured Data Attributes (Price, Currency, Stock, SKU, Brand, Reviews)
        price = None
        currency = None
        availability = None
        sku = None
        brand = None
        rating_value = None
        review_count = None

        if product_schema:
            sku = product_schema.get("sku")
            brand_val = product_schema.get("brand")
            brand = brand_val.get("name") if isinstance(brand_val, dict) else str(brand_val) if brand_val else None

            offers = product_schema.get("offers")
            offer_dict = offers[0] if isinstance(offers, list) and offers else (offers if isinstance(offers, dict) else {})
            price = offer_dict.get("price")
            currency = offer_dict.get("priceCurrency")
            availability = offer_dict.get("availability")

            agg = product_schema.get("aggregateRating")
            if isinstance(agg, dict):
                rating_value = agg.get("ratingValue")
                review_count = agg.get("reviewCount") or agg.get("ratingCount")
        else:
            # Fallback DOM scrape for attributes
            price_tag = soup.find(attrs={"class": re.compile(r"price|product-price|offer-price", re.I)})
            if price_tag:
                price = price_tag.get_text(strip=True)

        if not price:
            issues.append({
                "code": "ECOM_MISSING_PRICE",
                "title": "Missing Product Price in Markup",
                "severity": "error",
                "explanation": "No price detected in Schema.org Offer or product pricing block. Google Merchant Center and organic rich snippets will reject this product.",
                "recommended_fix": "Declare price in Product.offers Schema (e.g. 'price': '49.99', 'priceCurrency': 'USD')."
            })

        if not availability:
            issues.append({
                "code": "ECOM_MISSING_AVAILABILITY",
                "title": "Missing In-Stock / Availability Status",
                "severity": "warning",
                "explanation": "Search engines cannot determine if this product is in-stock, out-of-stock, or on backorder, preventing availability badges in Google Shopping and SERPs.",
                "recommended_fix": "Include 'availability': 'https://schema.org/InStock' in the Offer structured data."
            })

        if not sku:
            issues.append({
                "code": "ECOM_MISSING_SKU",
                "title": "Missing Product SKU / Identifier",
                "severity": "notice",
                "explanation": "A unique SKU or GTIN is essential for product variant tracking and automated Merchant Center product feed synchronization.",
                "recommended_fix": "Add 'sku' or 'gtin13' property to the Product JSON-LD schema."
            })

        if not rating_value:
            issues.append({
                "code": "ECOM_NO_REVIEWS_SCHEMA",
                "title": "No Customer Review / Rating Schema Found",
                "severity": "notice",
                "explanation": "Customer review stars in Google SERPs dramatically increase click-through rates (CTR). No AggregateRating schema was found.",
                "recommended_fix": "Embed AggregateRating markup with genuine average rating and total review count."
            })

        # Breadcrumbs Check
        breadcrumbs = soup.find(attrs={"aria-label": re.compile(r"breadcrumb", re.I)}) or \
                      soup.find(attrs={"class": re.compile(r"breadcrumb", re.I)})
        has_breadcrumbs = breadcrumbs is not None
        if not has_breadcrumbs:
            issues.append({
                "code": "ECOM_MISSING_BREADCRUMBS",
                "title": "Missing Product Breadcrumb Navigation",
                "severity": "warning",
                "explanation": "Breadcrumbs allow buyers and crawlers to navigate back to parent category pages, reinforcing internal link hierarchy and earning SERP breadcrumb trails.",
                "recommended_fix": "Add visible breadcrumb navigation (e.g., Home > Footwear > Running Shoes) and mark it up with Schema.org BreadcrumbList."
            })

        return {
            "product_title": h1_text or title_text,
            "has_brand_in_title": has_brand_in_title,
            "has_specs_in_title": has_specs_in_title,
            "description_words": desc_words,
            "price": price,
            "currency": currency,
            "availability": availability,
            "sku": sku,
            "brand": brand,
            "rating_value": rating_value,
            "review_count": review_count,
            "has_breadcrumbs": has_breadcrumbs
        }

    def _analyze_plp(self, soup: BeautifulSoup, url: str, breadcrumb_schema: Optional[Dict[str, Any]], issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        h1 = soup.find("h1")
        h1_text = h1.get_text(strip=True) if h1 else ""

        # Check Category Intro Copy
        intro = soup.find(attrs={"class": re.compile(r"category-description|collection-desc|category-intro", re.I)})
        intro_text = intro.get_text(separator=" ", strip=True) if intro else ""
        intro_words = len(intro_text.split()) if intro_text else 0

        if intro_words < 30:
            issues.append({
                "code": "ECOM_THIN_CATEGORY_COPY",
                "title": f"Minimal or Missing Category Description ({intro_words} words)",
                "severity": "warning",
                "explanation": "Category listing pages without introductory or contextual copy are harder for search engines to rank for competitive head keywords.",
                "recommended_fix": "Add a 50-150 word category description introducing the collection, buying criteria, and key brand highlights."
            })

        # Count listed products
        product_items = soup.find_all(attrs={"class": re.compile(r"product-card|product-item|grid-item|product-box", re.I)})
        product_count = len(product_items)

        # Pagination & Filter Links
        has_pagination = bool(soup.find(attrs={"class": re.compile(r"pagination|pager", re.I)}))

        return {
            "category_name": h1_text,
            "intro_word_count": intro_words,
            "products_displayed": product_count,
            "has_pagination": has_pagination
        }

    def _check_general_ecom(self, soup: BeautifulSoup, url: str, issues: List[Dict[str, Any]]):
        # Look for trust badges or policies
        text = soup.get_text().lower()
        if "shipping" not in text and "delivery" not in text:
            issues.append({
                "code": "ECOM_NO_SHIPPING_INFO",
                "title": "Missing Shipping / Delivery Policy Information",
                "severity": "notice",
                "explanation": "Clear delivery expectations, costs, and timelines are critical Google Quality Rater signals for e-commerce transactional intent.",
                "recommended_fix": "Add shipping and return policy links in the footer or near the purchase section."
            })

    def _check_faceted_navigation(self, parsed_url, soup: BeautifulSoup, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        query_params = parse_qs(parsed_url.query)
        facet_params = [p for p in query_params.keys() if any(f in p.lower() for f in ["color", "size", "filter", "sort", "order", "price", "brand", "tag"])]

        canonical_tag = soup.find("link", rel="canonical")
        canonical_url = canonical_tag.get("href") if canonical_tag else None

        has_risk = False
        if facet_params:
            if not canonical_url:
                has_risk = True
                issues.append({
                    "code": "ECOM_FACETED_NO_CANONICAL",
                    "title": f"Faceted Filter URL ({', '.join(facet_params)}) Has No Canonical Tag",
                    "severity": "error",
                    "explanation": "Faceted navigation generates thousands of URL combinations (e.g. ?color=blue&size=10). Without canonicals pointing to the root category, crawl budget is wasted and duplicate content penalties can occur.",
                    "recommended_fix": "Ensure all filter and sorting parameter URLs point their rel=canonical tag to the clean base category URL."
                })
            elif parsed_url.query and parsed_url.query in (canonical_url or ""):
                has_risk = True
                issues.append({
                    "code": "ECOM_FACET_SELF_CANONICAL",
                    "title": "Faceted Filter URL Self-Canonicalizes",
                    "severity": "warning",
                    "explanation": "The faceted navigation URL with filters points canonical to itself instead of the root category, encouraging search bots to index thin filtered variations.",
                    "recommended_fix": "Canonicalize filtered pages back to the clean master category URL without filter parameters."
                })

        return {
            "has_faceted_parameters": len(facet_params) > 0,
            "detected_facets": facet_params,
            "has_canonical": canonical_url is not None,
            "canonical_target": canonical_url,
            "duplicate_risk_detected": has_risk
        }

    def _audit_product_images(self, soup: BeautifulSoup, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        images = soup.find_all("img")
        total_images = len(images)
        missing_alt = []
        non_modern_formats = []

        for img in images:
            src = img.get("src") or img.get("data-src") or ""
            alt = img.get("alt")
            if not alt or not alt.strip():
                missing_alt.append(src[:60] if src else "unnamed_img")

            # Check format: webp/avif vs jpg/png
            src_clean = src.split("?")[0].lower()
            if src_clean.endswith((".jpg", ".jpeg", ".png", ".gif")):
                non_modern_formats.append(src[:60])

        if len(missing_alt) > 0:
            issues.append({
                "code": "ECOM_IMAGES_NO_ALT",
                "title": f"{len(missing_alt)} Product Images Missing Alt Text",
                "severity": "warning",
                "explanation": "Product images without descriptive alt text cannot rank in Google Image Search and violate ADA/WCAG accessibility standards for visually impaired shoppers.",
                "recommended_fix": "Add descriptive alt attributes including Product Name, Color, and Angle (e.g. alt='Nike Air Zoom Pegasus 40 - Lateral View')."
            })

        if len(non_modern_formats) > 3:
            issues.append({
                "code": "ECOM_LEGACY_IMAGE_FORMATS",
                "title": f"{len(non_modern_formats)} Images Using Legacy Formats (JPG/PNG)",
                "severity": "notice",
                "explanation": "Serving product galleries in modern formats (WebP or AVIF) reduces file sizes by 30-50%, accelerating page load times and mobile conversion rates.",
                "recommended_fix": "Convert catalog images to WebP/AVIF and implement responsive <picture> elements."
            })

        return {
            "total_images": total_images,
            "missing_alt_count": len(missing_alt),
            "modern_format_percent": round(((total_images - len(non_modern_formats)) / total_images * 100), 1) if total_images else 100.0
        }
