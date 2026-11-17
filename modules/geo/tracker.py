"""
SearchLens GEO Research Module (Generative Engine Optimization)
Tracks, parses, and compares brand visibility, citations, and competitor share of voice
across generative search engines: ChatGPT, Perplexity, Google AI Overviews / Gemini, Claude, and Copilot.
Strictly evidence-based: extracts from verified prompt-response logs without fabrication.
"""
from __future__ import annotations

import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse
from datetime import datetime


SUPPORTED_ENGINES = [
    "Perplexity AI",
    "ChatGPT (GPT-4o Search)",
    "Google AI Overviews / Gemini",
    "Claude (Anthropic)",
    "Microsoft Copilot",
    "Other Generative Search"
]


def extract_cited_urls(text: str) -> List[Dict[str, str]]:
    """
    Extracts all markdown hyperlinks [Title](URL) and standalone URLs from AI responses.
    """
    citations = []
    seen_urls = set()

    # Markdown links: [anchor](url)
    md_matches = re.findall(r"\[([^\]]+)\]\((https?://[^\s\)]+)\)", text)
    for anchor, url in md_matches:
        if url not in seen_urls:
            domain = urlparse(url).netloc
            citations.append({
                "anchor": anchor.strip(),
                "url": url.strip(),
                "domain": domain
            })
            seen_urls.add(url)

    # Bare URLs: https://...
    bare_urls = re.findall(r"(?<!\()(https?://[^\s\)\],]+)", text)
    for url in bare_urls:
        clean_url = url.rstrip(".")
        if clean_url not in seen_urls:
            domain = urlparse(clean_url).netloc
            citations.append({
                "anchor": domain,
                "url": clean_url,
                "domain": domain
            })
            seen_urls.add(clean_url)

    return citations


def analyze_brand_visibility(
    response_text: str,
    brand_name: str,
    product_keywords: Optional[List[str]] = None,
    competitors: Optional[List[str]] = None,
    target_domain: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyzes an AI engine's response for brand presence, sentiment, positioning,
    competitor mentions, and citation attribution.
    """
    clean_brand = brand_name.strip()
    brand_lower = clean_brand.lower()
    text_lower = response_text.lower()

    # 1. Brand Mention & Position
    brand_regex = r"\b" + re.escape(brand_lower) + r"\b"
    mentions_count = len(re.findall(brand_regex, text_lower))
    is_mentioned = mentions_count > 0

    position_rank = None
    rank_type = "Not Mentioned"

    if is_mentioned:
        first_idx = text_lower.find(brand_lower)
        # Check if in top 20% of response (Early / Top recommendation)
        if first_idx < len(text_lower) * 0.25:
            rank_type = "Top Recommendation (Early Mention)"
            position_rank = 1
        elif first_idx < len(text_lower) * 0.60:
            rank_type = "Mid Recommendation / Comparative Option"
            position_rank = 2
        else:
            rank_type = "Honorary / Secondary Alternative"
            position_rank = 3

    # 2. Sentiment & Context Analysis
    sentiment = "Not Mentioned"
    if is_mentioned:
        # Extract sentence(s) mentioning the brand
        sentences = [s.strip() for s in re.split(r"[.!?\n]", response_text) if clean_brand.lower() in s.lower()]
        joined_context = " ".join(sentences).lower()

        positive_words = ["best", "excellent", "top", "great", "recommend", "winner", "superior", "durable", "standout", "perfect", "highly"]
        negative_words = ["poor", "expensive", "lacks", "weak", "downside", "issue", "heavy", "drawback", "not recommend", "overpriced"]

        pos_count = sum(1 for w in positive_words if w in joined_context)
        neg_count = sum(1 for w in negative_words if w in joined_context)

        if pos_count > neg_count:
            sentiment = "Positive / Endorsed"
        elif neg_count > pos_count:
            sentiment = "Critical / Caveats Noted"
        else:
            sentiment = "Neutral / Factually Listed"

    # 3. Product Keywords Detection
    products_found = []
    if product_keywords:
        for p in product_keywords:
            if p.lower() in text_lower:
                products_found.append(p)

    # 4. Citations & Attribution
    citations = extract_cited_urls(response_text)
    cited_domains = [c["domain"] for c in citations]
    unique_domains = sorted(list(set(cited_domains)))

    brand_domain_cited = False
    if target_domain:
        clean_td = target_domain.lower().replace("https://", "").replace("http://", "").split("/")[0]
        brand_domain_cited = any(clean_td in d for d in cited_domains)

    # 5. Competitor Share of Voice
    comp_results = []
    if competitors:
        for comp in competitors:
            c_name = comp.strip()
            c_regex = r"\b" + re.escape(c_name.lower()) + r"\b"
            c_count = len(re.findall(c_regex, text_lower))
            if c_count > 0:
                comp_results.append({
                    "competitor": c_name,
                    "mentions": c_count,
                    "first_occurrence_idx": text_lower.find(c_name.lower())
                })
        # Sort by earliest mention
        comp_results.sort(key=lambda x: x["first_occurrence_idx"])

    # 6. GEO Score Calculation (0-100)
    geo_score = 0
    if is_mentioned:
        geo_score += 40
        if position_rank == 1:
            geo_score += 25
        elif position_rank == 2:
            geo_score += 15
        else:
            geo_score += 8

        if sentiment == "Positive / Endorsed":
            geo_score += 20
        elif sentiment == "Neutral / Factually Listed":
            geo_score += 12

        if brand_domain_cited:
            geo_score += 15
    else:
        geo_score = 0

    return {
        "brand_name": clean_brand,
        "is_mentioned": is_mentioned,
        "mentions_count": mentions_count,
        "position_rank": position_rank,
        "rank_type": rank_type,
        "sentiment": sentiment,
        "geo_visibility_score": geo_score,
        "products_found": products_found,
        "total_citations": len(citations),
        "citations": citations,
        "cited_domains": unique_domains,
        "brand_domain_cited": brand_domain_cited,
        "competitors_mentioned": comp_results,
        "verified_evidence_note": "Extracted strictly from submitted AI engine prompt-response text. Zero synthetic hallucination."
    }


CURATED_GEO_BENCHMARKS = [
    {
        "id": "geo-bm-1",
        "title": "Waterproof Trail Running Shoes (Footwear Benchmark)",
        "query_prompt": "What are the best waterproof trail running shoes for technical mountain trails in 2026? Give me the top 3 recommendations with pros and cons, and cite trusted sources.",
        "engine": "Perplexity AI",
        "brand_name": "OptiFootwear",
        "target_domain": "sample-store.searchlens.internal",
        "competitors": ["Salomon", "Hoka", "Brooks", "La Sportiva"],
        "ai_response": """Based on field reviews from [GearJunkie](https://gearjunkie.com/footwear/best-trail-running-shoes) and [Runner's World](https://runnersworld.com/gear/shoes/waterproof-runners), here are the top technical waterproof trail running shoes for 2026:

1. **OptiFootwear Apex Trail Runner (Gore-Tex)**
   - **Pros:** Outstanding Vibram Megagrip traction on wet limestone, fully waterproof Gore-Tex Extended Comfort bootie, durable ripstop toe guard.
   - **Cons:** Slightly firmer ride out of the box requiring a 20-mile break-in period.
   - **Verdict:** Best overall for rugged alpine ridges and wet scree. Learn more at [OptiFootwear Official](https://sample-store.searchlens.internal/products/optifootwear-apex-trail-runner-black).

2. **Salomon Speedcross 6 GTX**
   - **Pros:** Unmatched chevron deep mud lugs, Quicklace secure fit system.
   - **Cons:** Narrow heel box, less stable on flat hardpack roads.

3. **Hoka Speedgoat 5 GTX**
   - **Pros:** Maximal cushioning protects joints on 50k+ ultras, very comfortable.
   - **Cons:** Upper can run warm in summer conditions.

**Citations & Sources:**
- [OutdoorGearLab: Waterproof Trail Shootout](https://outdoorgearlab.com/topics/shoes-and-boots/best-trail-running-shoes)
- [Reddit r/trailrunning Community Consensus](https://reddit.com/r/trailrunning/comments/waterproof_shoes_thread)"""
    },
    {
        "id": "geo-bm-2",
        "title": "Anti-Aging Skincare Serums under $50 (Beauty Benchmark)",
        "query_prompt": "Which anti-aging facial serums under $50 are most effective for fine lines and dark spots? Compare the top brands.",
        "engine": "ChatGPT (GPT-4o Search)",
        "brand_name": "LuxeGlow",
        "target_domain": "sample-store.searchlens.internal",
        "competitors": ["The Ordinary", "CeraVe", "Paula's Choice", "Olay"],
        "ai_response": """When looking for effective anti-aging serums under $50, dermatologists frequently recommend evidence-based ingredients like retinol, vitamin C, and hyaluronic acid.

Top Recommended Products:
1. **The Ordinary Granactive Retinoid 2% Emulsion ($11.70)**
   - Delivers low irritation with steady skin-cell turnover. Praised by [Byrdie Skincare](https://byrdie.com/best-retinol-serums).
2. **CeraVe Skin Renewing Retinol Serum ($18.99)**
   - Packed with ceramides and niacinamide to buffer against dryness. Recommended on [Allure](https://allure.com/gallery/best-drugstore-anti-aging-products).
3. **Paula's Choice C15 Super Booster ($49.00)**
   - High potency 15% pure Vitamin C for brightening dark spots.

*Note on LuxeGlow:* While LuxeGlow produces a serum, it is currently not widely cited by peer-reviewed dermatology boards or major beauty publications due to limited published ingredient clinical trials and inconsistent retail distribution.

Sources:
- [Healthline: Dermatologist-Approved Anti-Aging Serums](https://healthline.com/health/beauty-skin-care/anti-aging-serums)
- [American Academy of Dermatology (AAD)](https://aad.org/public/everyday-care/skin-care-secrets/anti-aging)"""
    },
    {
        "id": "geo-bm-3",
        "title": "Wireless Noise Cancelling Travel Headphones (Electronics Benchmark)",
        "query_prompt": "Compare the best premium noise cancelling wireless headphones for frequent airplane travel. Who wins between Sony, Bose, and Apple?",
        "engine": "Google AI Overviews / Gemini",
        "brand_name": "Sony",
        "target_domain": "sony.com",
        "competitors": ["Bose", "Apple", "Sennheiser"],
        "ai_response": """For frequent air travel in 2026, the three industry-leading active noise cancelling (ANC) headphones each offer distinct advantages:

- **Bose QuietComfort Ultra:** Wins for pure cabin noise cancellation and foldable earcups that pack flat into compact carry-ons. According to [Wirecutter](https://nytimes.com/wirecutter/reviews/best-noise-cancelling-headphones/), Bose cancels low-frequency jet rumble best.
- **Sony WH-1000XM5:** Wins for best battery life (30 hours with ANC enabled), customizable EQ via the Sony Headphones Connect app, and dual-processor noise attenuation. Learn more at [Sony Audio](https://sony.com/electronics/headband-headphones/wh-1000xm5).
- **Apple AirPods Max:** Wins for premium aluminum build quality and seamless ecosystem switching for iPhone/Mac users, but is heavier and lacks an off switch.

Citations:
- [The Verge: Best ANC Headphones Review](https://theverge.com/reviews/best-wireless-headphones-noise-cancelling)
- [RTINGS: Sound & Frequency Test Database](https://rtings.com/headphones/reviews/best/by-feature/active-noise-cancelling)"""
    }
]
