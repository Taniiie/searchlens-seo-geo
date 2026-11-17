# SearchLens – SEO & GEO Intelligence Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.40+-FF4B4B.svg)](https://streamlit.io/)
[![Tests Passing](https://img.shields.io/badge/tests-25%20passed-brightgreen.svg)]()

> **Target Role:** E-Commerce SEO Intern / SEO-GEO Analyst Intern Portfolio Project  
> **Repository:** [https://github.com/Taniiie/searchlens-seo-geo.git](https://github.com/Taniiie/searchlens-seo-geo.git)

---

## 📌 Executive Summary

**SearchLens** is an end-to-end SEO and Generative Engine Optimization (GEO) platform architected for modern search landscapes. As search evolves beyond classical 10-blue-link SERPs into AI answer engines (ChatGPT Search, Perplexity AI, Google AI Overviews), SEO analysts need tools that audit both classical crawler fundamentals and generative brand visibility.

SearchLens bridges this gap by unifying:
1. **Technical & On-Page SEO Auditing** (Schema.org JSON-LD, crawlability, indexability, status codes, canonicals, robots.txt, sitemaps).
2. **E-Commerce Specific Diagnostics** (Product Detail Page & Category Page auditing, title formulas, missing commercial attributes, image alt text, faceted duplicate risk).
3. **Keyword Intelligence & Opportunity Modeling** (search intent classification, long-tail identification, topic clustering, and honest metric transparency).
4. **Generative Engine Optimization (GEO) Research** (evidence-based prompt-response tracking, citation domain attribution, and competitor share-of-voice across AI engines without synthetic hallucination).
5. **Relational SQLite Database & Analytics** (historical tracking, audit comparisons, issue trends, and bulk CSV/JSON data exports).
6. **Interactive Streamlit Dashboard** with real-time analytics, responsive charts, and an intuitive UI.

---

## 🏗️ Architecture & System Design

```
searchlens-seo-geo/
├── app.py                      # Classical CLI & Flask REST API entry point
├── dashboard.py                # Comprehensive Streamlit 9-section UI Dashboard
├── streamlit_app.py            # Streamlit Cloud deployment entry point
├── searchlens.db               # SQLite Relational Database (auto-initialized & seeded)
├── requirements.txt            # Dependency manifest
├── LICENSE                     # Original MIT License (Huzaifa Shoukat)
├── README.md                   # Full documentation & interview guide
│
├── modules/                    # Core Modular Architecture
│   ├── on_page/                # On-page elements (titles, meta, headings, images, links)
│   ├── technical/              # Technical SEO (network, HTML core, metrics, site checks)
│   │   └── structured_data.py  # Rich Schema.org validator (Product, Breadcrumbs, FAQ, Article)
│   ├── content/                # Content quality (readability, text-to-html ratio, spellcheck)
│   ├── scoring/                # Unified weighted scoring module
│   ├── site_audit/             # Multi-threaded crawler, duplication detection, CSV exports
│   │   └── issues.py           # Structured issues model with severity, explanation & fix
│   ├── ecommerce/              # [NEW] E-Commerce SEO Suite
│   │   ├── analyzer.py         # PDP & PLP auditor, title formula, faceted risk checks
│   │   └── sample_stores.py    # Curated sample e-commerce stores (OptiFootwear, LuxeGlow, PeakGear)
│   ├── keywords/               # [NEW] Keyword Intelligence & Clustering
│   │   └── processor.py        # Dataset cleaner, intent classification, opportunity score, suggestions
│   ├── geo/                    # [NEW] Generative Engine Optimization (GEO)
│   │   └── tracker.py          # Evidence-based AI search parser, citations extractor, competitor SOV
│   └── storage/                # [NEW] SQLite Relational Storage
│       ├── db.py               # Database manager, schema migrations, analytical queries, CSV/JSON
│       └── seed.py             # Portfolio benchmark seed utility
│
└── tests/                      # Automated Test Suite (25 Unit & Integration Tests)
    ├── test_on_page.py
    ├── test_technical_and_schema.py
    ├── test_crawler_and_site_audit.py
    ├── test_keywords.py
    ├── test_ecommerce.py
    └── test_geo_and_storage.py
```

---

## ✨ Key Features by Phase

### 1. Technical SEO Auditing
- **Title & Meta Description**: Checks length (characters & pixel approximation), duplicate word counts, power words, and primary keyword presence.
- **Heading Hierarchy**: Enforces clean semantic outlines ($H_1 \to H_2 \to H_3$); flags missing or multiple $H_1$ tags.
- **Indexability & Directives**: Scrutinizes `meta robots` (`noindex`, `nofollow`), `X-Robots-Tag` HTTP response headers, and canonicalization integrity.
- **Canonical Auditing**: Detects missing canonicals, cross-protocol canonicals (HTTP $\to$ HTTPS), self-referencing canonicals, and broken canonical targets.
- **Structured Data Validator**: Deep validation of JSON-LD Schema.org types (`Product`, `Offer`, `BreadcrumbList`, `Organization`, `FAQPage`, `Article`); validates required vs recommended properties and rich result eligibility.
- **Robots.txt & Sitemap Discovery**: Parses disallow directives line-by-line, identifies crawl blockages, and discovers XML sitemaps.

### 2. Website Crawler & Site Audit
- Safe, polite crawling with configurable page limits (default: 15–50 pages) and max depth limits (1–4).
- Internal vs external link discovery, HTTP status distribution (200, 3xx, 4xx, 5xx), redirect loop & chain detection.
- Content duplication detection via `visibleTextHash` and title grouping across crawled pages.
- Every discovered issue includes:
  - **Affected URL**
  - **Issue Code & Category**
  - **Severity** (`error`, `warning`, `notice`)
  - **Root Cause Explanation**
  - **Actionable Step-by-Step Fix**

### 3. Keyword Intelligence & Intent Classification
- Supports **CSV and Excel (`.xlsx`, `.xls`) file uploads**, seed lists, or curated e-commerce sets.
- Automatic text cleaning, deduplication, and tokenization.
- **Search Intent Classifier**: Categorizes queries into **Transactional**, **Commercial**, **Informational**, or **Navigational** with confidence scores.
- **Long-Tail Keyword Identification**: Queries with $\ge 3$ words or intent-rich modifiers.
- **Thematic Clustering**: Groups keywords by semantic modifiers and parent product categories.
- **Opportunity Score Formula ($0-100$)**:
  $$\text{Opportunity} = \text{Volume Score} (0-50) + \text{Difficulty Score} (0-40) + \text{Intent Bonus} (0-10)$$
- **Strict Metric Honesty**: If source data omits search volume or difficulty, SearchLens explicitly tags scores as `Estimated via Query Specificity & Intent (Search Volume/KD Not In Source Data)` rather than inventing numbers.

### 4. E-Commerce SEO Suite
- Page archetype classifier: **PDP (Product Detail Page)** vs **PLP (Category Listing)** vs General page.
- **PDP Checks**:
  - Title formula check: `[Brand] + [Product/Model] + [Key Feature] + [Variant/Specs]`.
  - Description depth: Flags thin descriptions under 100 words.
  - Missing commercial attributes: Price, ISO 4217 Currency, Availability/Stock, SKU, and AggregateRating review stars.
  - Media audit: Product images missing descriptive alt text, responsive sizing, and modern WebP/AVIF format checks.
  - Breadcrumb navigation verification.
- **PLP Checks**: Category intro copy depth (avoiding zero-text category pages), product card counts, and pagination tags.
- **Faceted Navigation Risk**: Flags filtered query parameters (`?color=`, `?sort=`, `?size=`) that lack canonical tags pointing to root category pages.

### 5. Generative Engine Optimization (GEO) Research
- Tracks and measures brand visibility across AI answer engines: **ChatGPT (GPT-4o Search)**, **Perplexity AI**, **Google AI Overviews / Gemini**, **Claude**, and **Microsoft Copilot**.
- Evidence-based prompt and response parser:
  - **Brand & Product Mention Detection**: Measures frequency, sentiment (Positive/Endorsed, Neutral, Critical), and position rank (Top Recommendation vs Comparative vs Not Mentioned).
  - **Citation & Domain Attribution Extractor**: Identifies all hyperlinks and bare URLs cited by the AI model; checks if the brand's own domain was referenced as an authoritative source.
  - **Competitor Share of Voice**: Identifies competing brands cited in the same answer and logs their order of appearance.
  - **Zero Fabrication**: Verified evidence logging with honest disclosures.

### 6. Relational SQLite Database & Data Analytics
- Seven relational tables: `projects`, `crawled_pages`, `audit_results`, `seo_issues`, `keywords`, `geo_research`, `audit_history`.
- Built-in SQL analytical queries:
  - Most common issues by category and severity
  - Most affected pages with issue severity breakdowns
  - Multi-audit comparison (score delta and progress tracking)
  - Keyword opportunity ranking
  - Cross-platform AI engine comparison
- One-click bulk exports to **CSV and JSON** for every table.

---

## 🖥️ Streamlit Dashboard Walkthrough

The platform features a 9-view responsive dashboard:

| View | Purpose |
|------|---------|
| 🏠 **Overview & Executive Dashboard** | High-level KPI cards, category performance radar, issue frequency chart, and recent audit diffs. |
| 🔍 **Website SEO Audit** | Deep single-URL audit with visual gauges, issue accordions, on-page inspect, and JSON-LD schema testing. |
| 🕷️ **Website Crawler** | Multi-page crawler with live progress bars, internal link table, duplicate alerts, and CSV exports. |
| ⚙️ **Technical SEO Deep Dive** | Standalone tools for robots.txt analysis, sitemap health inspection, redirect hops, and schema validation. |
| 📊 **Keyword Intelligence** | File uploader, intent pie chart, cluster bar charts, opportunity matrix, and seed suggestions generator. |
| 🛒 **E-Commerce SEO Suite** | Audits PDP and PLP store pages, title formula compliance, missing attributes, and faceted duplicate risks. |
| 🤖 **GEO Research (AI Search)** | Prompt-response parser, brand visibility score, citation domains, and competitor share-of-voice charts. |
| 📜 **Audit History & Tracking** | Historical score trend lines over time and comparative delta audit reports. |
| 💾 **Database & Data Exports** | Relational table inspector and one-click bulk CSV / JSON data downloads. |

---

## 🚀 Quick Start & Installation

### Prerequisites
- Python 3.11 or higher
- Git

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Taniiie/searchlens-seo-geo.git
   cd searchlens-seo-geo
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the Streamlit Dashboard:**
   ```bash
   streamlit run dashboard.py
   # or
   streamlit run streamlit_app.py
   ```
   Open your browser to `http://localhost:8501`.

5. **(Optional) Run classical CLI audit:**
   ```bash
   python app.py https://example.com --keywords "ecommerce shoes"
   ```

---

## 🧪 Automated Testing

SearchLens includes a complete unit and integration test suite with 25 passing test cases:

```bash
python -m pytest -v
```

### Test Coverage Summary:
- `tests/test_on_page.py`: Title length/pixels/keywords, meta descriptions, heading order, image alt text, Flesch reading ease, text-to-HTML ratio.
- `tests/test_technical_and_schema.py`: Doctype, charset, viewport, canonicals, robots meta, valid Product schema, missing offers/price detection, BreadcrumbList validation.
- `tests/test_crawler_and_site_audit.py`: URL normalization, duplicate content hashing, issue derivation with severity, explanation, and recommended fix.
- `tests/test_keywords.py`: Intent classification, long-tail query filtering, opportunity score modeling, clustering, and e-commerce suggestions.
- `tests/test_ecommerce.py`: PDP vs PLP detection, title formula check, missing SKU/availability/price, faceted self-canonicals, sample store audits.
- `tests/test_geo_and_storage.py`: Citation extraction, brand mention parsing, competitor share of voice, SQLite CRUD lifecycle, and CSV/JSON exports.

---

## 🎯 Interview Concepts Guide (For E-Commerce SEO / SEO-GEO Analyst Roles)

When presenting this project in technical interviews, be prepared to discuss:

1. **Faceted Navigation in E-Commerce:**
   - *Problem:* Filtering and sorting parameters (e.g. `?size=10&color=blue&sort=price_asc`) create exponential duplicate URL combinations that drain crawl budget and split link equity.
   - *Solution:* Enforce canonical tags pointing from filtered variations to the root category URL, block irrelevant filter combinations in `robots.txt`, and use `rel="nofollow"` on multi-select filters where appropriate.

2. **Schema.org for Product & Shopping SERP Features:**
   - *Concept:* `Product` schema with nested `Offer` (price, priceCurrency, availability) and `AggregateRating` enables rich SERP snippets (star ratings, price, in-stock badges) that lift click-through rates (CTR) by 20–30%.
   - *Common Pitfall:* Missing ISO 4217 currency codes or missing `availability` prevents Google Shopping and rich result validation.

3. **Generative Engine Optimization (GEO):**
   - *Concept:* AI search engines (Perplexity, ChatGPT, Gemini) synthesize answers using Retrieval-Augmented Generation (RAG) by crawling trusted third-party review sites, Reddit consensus, and clear structured brand websites.
   - *Optimization Strategy:* Gain citations on high-authority domain hubs that AI models cite, implement clean `/llms.txt` markdown files, and maintain consistent entity naming across directories.

4. **Search Intent & Keyword Specificity:**
   - *Concept:* Aligning content with user intent (Transactional vs Commercial vs Informational). High-intent long-tail keywords (3+ words) frequently deliver higher conversion rates than high-volume head terms due to purchase readiness.

---

## ⚠️ Limitations & Future Work

- **Live AI Query Execution:** Current GEO tracking relies on recorded prompt-response logs (or curated benchmarks). Future work includes integrating authenticated API connections (e.g. Perplexity API, OpenAI API) to automate real-time query sweeps.
- **Headless Browser Rendering:** The crawler includes optional Playwright JS discovery for single pages; expanding distributed headless rendering across full multi-thousand page enterprise crawls is planned.
- **Log File Analysis:** Integrating web server access logs (Apache/Nginx/Cloudflare) to cross-reference bot crawl frequency against indexed URLs.

---

## 📜 Attribution & License

- **License:** [MIT License](LICENSE)
- **Original Foundation:** Inherited and extended from the [Advanced SEO Analyzer](https://github.com/Huzaifa-coder/advanced-seo-analyzer) created by **Huzaifa Shoukat** (Copyright © 2025 Huzaifa Shoukat).
- **Transformations & Extensions:** All E-Commerce SEO modules, Generative Engine Optimization (GEO) tracking, Keyword Intelligence processor, SQLite storage engine, test suite, and the Streamlit dashboard were engineered specifically for **SearchLens – SEO & GEO Intelligence Platform**.
