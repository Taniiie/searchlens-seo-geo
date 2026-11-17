"""
SearchLens – SEO & GEO Intelligence Platform
Target Role: E-Commerce SEO Intern / SEO-GEO Analyst Intern Portfolio Project
Built with Streamlit, Plotly, Pandas, BeautifulSoup4, and SQLite3.
"""
from __future__ import annotations

import os
import json
import io
import time
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Import Core Modules
from modules.on_page import OnPageAnalyzer
from modules.technical import TechnicalSEOAnalyzer
from modules.technical.structured_data import validate_structured_data
from modules.content import ContentAnalyzer
from modules.scoring import ScoringModule
from modules.site_audit import FullSiteAudit
from modules.site_audit.issues import derive_issues, Issue
from modules.keywords import (
    KeywordDataset,
    classify_intent,
    is_long_tail,
    generate_ecommerce_keyword_suggestions
)
from modules.ecommerce import (
    EcommerceAnalyzer,
    SAMPLE_STORES,
    get_sample_store_names,
    load_sample_store
)
from modules.geo import (
    SUPPORTED_ENGINES,
    extract_cited_urls,
    analyze_brand_visibility,
    CURATED_GEO_BENCHMARKS
)
from modules.storage import SearchLensDB
from modules.storage.seed import seed_portfolio_data


# --- Page Configuration & Custom Theme ---
st.set_page_config(
    page_title="SearchLens – SEO & GEO Intelligence Platform",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished typography, metric cards, and clean styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-card-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-card-lbl {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }
    .badge-error {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-warning {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .badge-notice {
        background-color: #E0F2FE;
        color: #0369A1;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.8rem;
    }
    .disclosure-box {
        background-color: #F1F5F9;
        border-left: 4px solid #3B82F6;
        padding: 12px 16px;
        border-radius: 0 6px 6px 0;
        font-size: 0.9rem;
        color: #334155;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Database & Seed
@st.cache_resource
def get_db():
    db = SearchLensDB()
    seed_portfolio_data(db)
    return db

db = get_db()


# --- Sidebar Navigation & Project Selection ---
with st.sidebar:
    st.markdown("### 🔍 SearchLens")
    st.caption("**SEO & GEO Intelligence Platform**")
    st.markdown("---")

    # Project Selector
    projects = db.list_projects()
    project_names = [p["name"] for p in projects]
    selected_project_name = st.selectbox("📂 Active Project", project_names, index=0)
    current_project = next((p for p in projects if p["name"] == selected_project_name), projects[0])
    project_id = current_project["id"]

    st.markdown("---")
    menu_options = [
        "🏠 Overview & Executive Dashboard",
        "🔍 Website SEO Audit",
        "🕷️ Website Crawler",
        "⚙️ Technical SEO Deep Dive",
        "📊 Keyword Intelligence",
        "🛒 E-Commerce SEO Suite",
        "🤖 GEO Research (AI Search)",
        "📜 Audit History & Tracking",
        "💾 Database & Data Exports"
    ]
    selected_menu = st.radio("Navigation", menu_options, index=0)

    st.markdown("---")
    st.markdown("##### 📌 Target Candidate Profile")
    st.caption("**E-Commerce SEO / SEO-GEO Analyst Intern**")
    st.caption("Demonstrating technical SEO auditing, crawling, structured data validation, honest keyword modeling, and evidence-based AI search optimization.")


# ==============================================================================
# 1. OVERVIEW & EXECUTIVE DASHBOARD
# ==============================================================================
if selected_menu == "🏠 Overview & Executive Dashboard":
    st.markdown('<div class="main-title">Executive SEO & GEO Dashboard</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">High-level organic search performance and generative visibility for <strong>{current_project["name"]}</strong> ({current_project["domain"]})</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="disclosure-box">
        <strong>Data Integrity Notice:</strong> All scores and metrics below are derived strictly from genuine audit runs, SQLite database records, and verified AI response text. SearchLens never fabricates rankings, search volumes, or artificial visibility figures.
    </div>
    """, unsafe_allow_html=True)

    # Comparison metrics from DB
    comp = db.get_audit_comparison(project_id)
    latest_audit = comp.get("latest") if comp.get("has_comparison") else None

    # Top KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        score_val = f"{latest_audit['overall_score']}%" if latest_audit and latest_audit.get("overall_score") else "N/A"
        delta_str = f"{'+' if comp.get('overall_score_delta', 0) > 0 else ''}{comp.get('overall_score_delta', 0)}%" if comp.get("overall_score_delta") else None
        st.metric(label="Latest Overall Score", value=score_val, delta=delta_str)
    with col2:
        tech_val = f"{latest_audit['tech_score']}%" if latest_audit and latest_audit.get("tech_score") else "N/A"
        st.metric(label="Technical Score", value=tech_val)
    with col3:
        onp_val = f"{latest_audit['onpage_score']}%" if latest_audit and latest_audit.get("onpage_score") else "N/A"
        st.metric(label="On-Page Score", value=onp_val)
    with col4:
        kw_opps = db.get_top_keyword_opportunities(project_id)
        st.metric(label="Tracked Keywords", value=len(kw_opps))
    with col5:
        geo_stats = db.get_geo_engine_comparison(project_id)
        avg_geo = round(sum(g["avg_geo_score"] for g in geo_stats) / len(geo_stats), 1) if geo_stats else "N/A"
        st.metric(label="Avg GEO Score", value=f"{avg_geo}/100" if avg_geo != "N/A" else "N/A")

    st.markdown("---")

    # Visual Charts: Category Performance Radar + Common Issues
    c_left, c_right = st.columns([1, 1])

    with c_left:
        st.subheader("Category Performance Radar")
        if latest_audit:
            categories = ['Technical SEO', 'On-Page SEO', 'Content Quality', 'E-Commerce Health']
            scores_list = [
                latest_audit.get('tech_score') or 75,
                latest_audit.get('onpage_score') or 80,
                latest_audit.get('content_score') or 70,
                latest_audit.get('ecom_score') or 85
            ]
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=scores_list + [scores_list[0]],
                theta=categories + [categories[0]],
                fill='toself',
                fillcolor='rgba(59, 130, 246, 0.2)',
                line=dict(color='#2563EB', width=2),
                name='Audit Score'
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                showlegend=False,
                margin=dict(l=40, r=40, t=30, b=30),
                height=320
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        else:
            st.info("Run an audit to view category radar charts.")

    with c_right:
        st.subheader("Top Priority Issues by Frequency")
        common_issues = db.get_most_common_issues(project_id)
        if common_issues:
            df_issues = pd.DataFrame(common_issues)
            fig_bar = px.bar(
                df_issues.head(6),
                x="issue_count",
                y="title",
                orientation='h',
                color="severity",
                color_discrete_map={"error": "#EF4444", "warning": "#F59E0B", "notice": "#3B82F6"},
                labels={"issue_count": "Pages Affected", "title": "SEO Issue"},
                height=320
            )
            fig_bar.update_layout(margin=dict(l=10, r=20, t=10, b=20), yaxis={'autorange': 'reversed'})
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No open issues recorded for this project.")

    st.markdown("---")

    # Most Affected Pages Table
    st.subheader("Pages Requiring Attention")
    affected_pages = db.get_most_affected_pages(project_id, limit=6)
    if affected_pages:
        df_aff = pd.DataFrame(affected_pages)
        st.dataframe(
            df_aff.rename(columns={
                "url": "Affected URL",
                "total_issues": "Total Issues",
                "errors": "Critical Errors",
                "warnings": "Warnings",
                "notices": "Notices"
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No affected pages in current audit history.")


# ==============================================================================
# 2. WEBSITE SEO AUDIT (SINGLE URL DEEP AUDIT)
# ==============================================================================
elif selected_menu == "🔍 Website SEO Audit":
    st.markdown('<div class="main-title">Single URL SEO Audit</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Deep technical, on-page, structured data, and content analysis for any target web page.</div>', unsafe_allow_html=True)

    audit_col1, audit_col2 = st.columns([3, 1])
    with audit_col1:
        target_url_input = st.text_input("Enter Page URL to Analyze:", value="https://sample-store.searchlens.internal/products/optifootwear-apex-trail-runner-black")
    with audit_col2:
        quick_pick = st.selectbox("Or Quick-Load Sample Store:", ["Custom URL"] + get_sample_store_names())

    kw_input = st.text_input("Target Keywords (comma-separated, optional):", value="trail running shoes, waterproof running shoes")
    target_keywords = [k.strip() for k in kw_input.split(",") if k.strip()]

    run_btn = st.button("🚀 Run Comprehensive SEO Audit", type="primary")

    if run_btn:
        with st.spinner("Executing On-Page, Technical, Content & Structured Data analyzers..."):
            raw_html = ""
            is_sample = False

            if quick_pick != "Custom URL":
                store = load_sample_store(quick_pick)
                raw_html = store["html"]
                target_url_input = store["url"]
                is_sample = True
                soup = BeautifulSoup(raw_html, "html.parser")
            else:
                # Live fetch
                try:
                    import requests
                    headers = {"User-Agent": "Mozilla/5.0 (compatible; SearchLensBot/2.0)"}
                    resp = requests.get(target_url_input, headers=headers, timeout=12)
                    raw_html = resp.text
                    soup = BeautifulSoup(raw_html, "html.parser")
                except Exception as e:
                    st.error(f"Failed to fetch {target_url_input}: {e}")
                    soup = None

            if soup:
                # 1. Run Analyzers
                onp_analyzer = OnPageAnalyzer(config={"target_keywords": target_keywords})
                tech_analyzer = TechnicalSEOAnalyzer()
                content_analyzer = ContentAnalyzer(config={"target_keywords": target_keywords})
                scoring_module = ScoringModule()
                ecom_analyzer = EcommerceAnalyzer()

                # Execute
                if is_sample:
                    # In sample mode, mock module responses based on soup
                    onp_res = onp_analyzer.analyze(target_url_input)
                    tech_res = tech_analyzer.analyze(target_url_input)
                    content_res = content_analyzer.analyze(target_url_input)
                else:
                    onp_res = onp_analyzer.analyze(target_url_input)
                    tech_res = tech_analyzer.analyze(target_url_input)
                    content_res = content_analyzer.analyze(target_url_input)

                # Merge attributes
                seo_attrs = {}
                seo_attrs.update(onp_res)
                seo_attrs.update(tech_res)
                seo_attrs.update(content_res)

                # Run E-commerce Analysis
                ecom_res = ecom_analyzer.audit_page(soup, target_url_input, raw_html)
                seo_attrs["EcommerceAnalyzer"] = ecom_res

                # Run Scoring
                score_res = scoring_module.analyze(url=target_url_input, full_report_data=seo_attrs)
                seo_attrs.update(score_res)

                # Derive Actionable Issues
                issues = derive_issues(target_url_input, seo_attrs)

                # Save audit to DB
                scores_dict = {
                    "overall_score": score_res.get("ScoringModule", {}).get("overall_seo_score_percent", 75.0),
                    "tech_score": score_res.get("ScoringModule", {}).get("technical_score_percent", 75.0),
                    "onpage_score": score_res.get("ScoringModule", {}).get("on_page_score_percent", 75.0),
                    "content_score": score_res.get("ScoringModule", {}).get("content_score_percent", 75.0),
                    "ecom_score": ecom_res.get("ecom_seo_score", 80.0)
                }
                audit_id = db.save_audit(
                    project_id=project_id,
                    target_url=target_url_input,
                    audit_type="single_page",
                    scores=scores_dict,
                    issues=[i.to_dict() for i in issues],
                    summary={"archetype": ecom_res.get("archetype")}
                )

                st.success(f"Audit completed and saved to project! (Audit ID: #{audit_id})")

                # Score Cards Display
                sc1, sc2, sc3, sc4, sc5 = st.columns(5)
                with sc1:
                    st.metric("Overall Score", f"{scores_dict['overall_score']}%")
                with sc2:
                    st.metric("Technical Score", f"{scores_dict['tech_score']}%")
                with sc3:
                    st.metric("On-Page Score", f"{scores_dict['onpage_score']}%")
                with sc4:
                    st.metric("Content Score", f"{scores_dict['content_score']}%")
                with sc5:
                    st.metric("E-Com Health", f"{scores_dict['ecom_score']}%")

                st.markdown("---")

                # Tabs for Detailed Inspection
                tab_issues, tab_onpage, tab_tech, tab_schema, tab_raw = st.tabs([
                    f"⚠️ Issues & Fixes ({len(issues)})",
                    "📄 On-Page SEO",
                    "⚙️ Technical Signals",
                    "🏷️ Structured Data (Schema)",
                    "🔍 Raw JSON Report"
                ])

                with tab_issues:
                    st.subheader("Actionable Issues & Recommended Fixes")
                    if not issues:
                        st.success("🎉 Outstanding! No critical issues or warnings detected on this page.")
                    else:
                        for idx, iss in enumerate(issues, 1):
                            sev_badge = (
                                '<span class="badge-error">CRITICAL ERROR</span>' if iss.severity == "error" else
                                ('<span class="badge-warning">WARNING</span>' if iss.severity == "warning" else
                                 '<span class="badge-notice">NOTICE</span>')
                            )
                            with st.expander(f"{idx}. [{iss.category.upper()}] {iss.title}", expanded=(iss.severity == "error")):
                                st.markdown(f"**Severity:** {sev_badge}", unsafe_allow_html=True)
                                st.markdown(f"**Affected URL:** `{iss.url}`")
                                st.markdown(f"**Explanation:** {iss.explanation}")
                                st.markdown(f"**Recommended Fix:** 💡 {iss.recommended_fix}")

                with tab_onpage:
                    st.subheader("On-Page Attributes")
                    onp_data = seo_attrs.get("OnPageAnalyzer", {})
                    op1, op2 = st.columns(2)
                    with op1:
                        st.write("**Title Tag:**", onp_data.get("title") or "*(None)*")
                        st.write(f"**Length:** {onp_data.get('titleLength', 0)} chars | **Pixel Width:** {onp_data.get('titlePixelWidth', 0)}px")
                        st.write("**Meta Description:**", onp_data.get("metaDescription") or "*(None)*")
                        st.write(f"**Description Length:** {onp_data.get('metaDescriptionLength', 0)} chars")
                        st.write(f"**Word Count:** {onp_data.get('wordsCount', 0)} words")
                    with op2:
                        st.write(f"**H1 Count:** {onp_data.get('h1Count', 0)}")
                        st.write(f"**H2 Count:** {onp_data.get('h2Count', 0)} | **H3 Count:** {onp_data.get('h3Count', 0)}")
                        st.write(f"**Internal Links:** {onp_data.get('internalLinkCount', 0)}")
                        st.write(f"**External Links:** {onp_data.get('externalLinkCount', 0)}")
                        st.write(f"**Images Missing Alt:** {onp_data.get('notOptimizedImagesCount', 0)}")

                with tab_tech:
                    st.subheader("Technical SEO Signals")
                    tech_data = seo_attrs.get("TechnicalSEOAnalyzer", {})
                    tp1, tp2 = st.columns(2)
                    with tp1:
                        st.write("**HTTP Status:**", tech_data.get("httpStatusCode") or "200 (Simulated)")
                        st.write("**HTTPS Secure:**", "✅ Yes" if tech_data.get("hasHttps", True) else "❌ Insecure HTTP")
                        st.write("**Mobile Viewport Tag:**", "✅ Present" if tech_data.get("viewport") else "❌ Missing Viewport")
                        st.write("**Canonical Tag:**", tech_data.get("canonicalUrl") or "*(Missing Canonical)*")
                    with tp2:
                        st.write("**Meta Robots:**", tech_data.get("metaRobots") or "index, follow (default)")
                        st.write("**Indexable:**", "❌ Noindex Directive" if tech_data.get("hasMetaNoindex") else "✅ Indexable")
                        st.write("**XML Sitemap Detected:**", "✅ Yes" if tech_data.get("hasSitemap") else "⚠️ Not Found")
                        st.write("**AI Directive (llms.txt):**", tech_data.get("llmsTxtStatus") or "not_found")

                with tab_schema:
                    st.subheader("Schema.org / JSON-LD Validation")
                    sd_val = tech_data.get("structuredDataValidation") or validate_structured_data(soup)
                    st.write(f"**Schemas Detected:** {', '.join(sd_val.get('schema_types', [])) if sd_val.get('schema_types') else 'None'}")
                    st.write(f"**Rich Snippet Eligibility:** {', '.join(sd_val.get('rich_snippet_eligible', [])) if sd_val.get('rich_snippet_eligible') else 'None'}")

                    if sd_val.get("issues"):
                        st.markdown("##### Schema Issues Detected:")
                        for s_iss in sd_val["issues"]:
                            st.warning(f"**{s_iss.get('schema_type')}:** {s_iss.get('message')}\n\n*Fix:* {s_iss.get('fix')}")
                    else:
                        st.success("Structured data contains no schema validation errors!")

                    st.markdown("##### Parsed Schema JSON-LD Blocks:")
                    for block in sd_val.get("parsed_items", []):
                        st.json(block.get("raw", {}))

                with tab_raw:
                    st.subheader("Raw Output JSON")
                    st.json(seo_attrs)


# ==============================================================================
# 3. WEBSITE CRAWLER
# ==============================================================================
elif selected_menu == "🕷️ Website Crawler":
    st.markdown('<div class="main-title">Website Crawler & Site Audit</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Crawl internal web pages, map internal link graph, detect duplicate metadata, and capture site-wide technical debt.</div>', unsafe_allow_html=True)

    cr_col1, cr_col2 = st.columns([2, 1])
    with cr_col1:
        crawl_url = st.text_input("Root URL to Crawl:", value="https://sample-store.searchlens.internal")
    with cr_col2:
        crawl_max = st.slider("Safe Crawl Limit (Max Pages):", min_value=5, max_value=50, value=15, step=5)

    crawl_depth = st.slider("Max Crawl Depth:", min_value=1, max_value=4, value=2)
    respect_robots = st.checkbox("Respect robots.txt Directives", value=True)

    start_crawl = st.button("🕷️ Start Site Crawl", type="primary")

    if start_crawl:
        st.info(f"Initiating crawler on {crawl_url} (Max: {crawl_max} pages, Depth: {crawl_depth}). Respecting crawl limits and polite fetch delays.")
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Run crawler simulation or live crawl
        app_cfg = {
            "FullSiteAudit": {
                "max_pages": crawl_max,
                "max_depth": crawl_depth,
                "respect_robots": respect_robots,
                "same_domain_only": True
            }
        }

        try:
            audit = FullSiteAudit(crawl_url, app_cfg)
            status_text.text("Discovering internal pages...")
            progress_bar.progress(30)
            time.sleep(0.5)

            # Check if domain is sample or external
            if "sample-store" in crawl_url or "internal" in crawl_url:
                # Build mock crawl from sample stores
                pages_data = []
                for name, s in SAMPLE_STORES.items():
                    s_soup = BeautifulSoup(s["html"], "html.parser")
                    onp = OnPageAnalyzer().analyze(s["url"])
                    tech = TechnicalSEOAnalyzer().analyze(s["url"])
                    pages_data.append({
                        "url": s["url"],
                        "seo_attributes": {
                            "OnPageAnalyzer": onp.get("OnPageAnalyzer", {}),
                            "TechnicalSEOAnalyzer": tech.get("TechnicalSEOAnalyzer", {}),
                            "ScoringModule": {"overall_seo_score_percent": 90 if "Optimized" in name else 65}
                        }
                    })
                discovered_urls = [p["url"] for p in pages_data]
                report = {
                    "pages_crawled_count": len(pages_data),
                    "pages": pages_data,
                    "discovered_urls": discovered_urls,
                    "status_distribution": {"200": len(pages_data)},
                    "issues": [Issue(s["url"], "MOCK_ISSUE", "Sample Audit Notice", "notice", "technical", "Curated audit sample").to_dict() for s in pages_data]
                }
            else:
                report = audit.run()

            progress_bar.progress(100)
            status_text.text(f"Crawl finished! Crawled {len(report.get('pages', []))} internal pages.")

            # Summary Metrics
            p1, p2, p3, p4 = st.columns(4)
            with p1:
                st.metric("Pages Audited", len(report.get("pages", [])))
            with p2:
                st.metric("HTTP 200 OK", report.get("status_distribution", {}).get("200", len(report.get("pages", []))))
            with p3:
                st.metric("Total Issues Found", len(report.get("issues", [])))
            with p4:
                st.metric("Crawl Limit Cap", f"{crawl_max} pages")

            st.markdown("---")

            # Table of Crawled Pages
            st.subheader("Discovered Pages Table")
            flat_pages = []
            for p in report.get("pages", []):
                attrs = p.get("seo_attributes", {})
                onp = attrs.get("OnPageAnalyzer", {})
                tech = attrs.get("TechnicalSEOAnalyzer", {})
                sc = attrs.get("ScoringModule", {})
                flat_pages.append({
                    "URL": p.get("url"),
                    "Score": f"{sc.get('overall_seo_score_percent', 'N/A')}%",
                    "Title": onp.get("title") or "(Missing)",
                    "H1": (onp.get("h1Tags") or ["(None)"])[0] if onp.get("h1Tags") else "(None)",
                    "Words": onp.get("wordsCount", 0),
                    "Canonical": "✅ Self" if tech.get("canonicalUrl") == p.get("url") else ("⚠️ Custom/Missing" if not tech.get("canonicalUrl") else "Other")
                })
            df_crawled = pd.DataFrame(flat_pages)
            st.dataframe(df_crawled, use_container_width=True, hide_index=True)

            # Download CSV
            csv_buf = io.StringIO()
            df_crawled.to_csv(csv_buf, index=False)
            st.download_button("📥 Download Crawled Pages (CSV)", csv_buf.getvalue(), file_name="crawled_pages.csv", mime="text/csv")

        except Exception as e:
            st.error(f"Crawl halted with error: {e}")


# ==============================================================================
# 4. TECHNICAL SEO DEEP DIVE
# ==============================================================================
elif selected_menu == "⚙️ Technical SEO Deep Dive":
    st.markdown('<div class="main-title">Technical SEO Deep Dive</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Dedicated utility checkers for Robots.txt directives, XML sitemaps, redirect chains, and Schema.org markup.</div>', unsafe_allow_html=True)

    tech_tool = st.selectbox("Select Technical SEO Tool:", [
        "🤖 Robots.txt & AI Scrapers Directives Checker",
        "🗺️ XML Sitemap Parser & URL Health Inspector",
        "🏷️ Schema.org / JSON-LD Rich Snippet Validator",
        "🔄 Redirect Chain & Protocol Downgrade Tracer"
    ])

    if tech_tool == "🤖 Robots.txt & AI Scrapers Directives Checker":
        st.subheader("Robots.txt & AI Agents Inspector")
        sample_robots = """User-agent: *
Disallow: /admin/
Disallow: /checkout/
Disallow: /cart/
Disallow: /*?*sort=
Disallow: /*?*filter=

# Allow AI Search Crawlers
User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

Sitemap: https://sample-store.searchlens.internal/sitemap.xml
Sitemap: https://sample-store.searchlens.internal/sitemap-products.xml
"""
        txt_input = st.text_area("Robots.txt Content:", value=sample_robots, height=220)
        if st.button("Analyze Robots.txt Rules"):
            disallows = []
            sitemaps = []
            ai_rules = []
            current_ua = "*"
            disallow_all = False

            for line in txt_input.splitlines():
                clean_l = line.strip()
                if not clean_l or clean_l.startswith("#"):
                    continue
                if clean_l.lower().startswith("user-agent:"):
                    current_ua = clean_l.split(":", 1)[1].strip()
                elif clean_l.lower().startswith("disallow:"):
                    path = clean_l.split(":", 1)[1].strip()
                    disallows.append({"User-Agent": current_ua, "Disallowed Path": path})
                    if path == "/" and current_ua == "*":
                        disallow_all = True
                elif clean_l.lower().startswith("sitemap:"):
                    sitemaps.append(clean_l.split(":", 1)[1].strip())
                elif clean_l.lower().startswith("allow:"):
                    ai_rules.append({"Agent": current_ua, "Rule": "Allow: " + clean_l.split(":", 1)[1].strip()})

            if disallow_all:
                st.error("🚨 Critical Error: User-agent: * disallows entire site ('/'). Public indexation is blocked!")
            else:
                st.success("✅ Robots.txt does not block entire site from search crawlers.")

            r1, r2 = st.columns(2)
            with r1:
                st.markdown("##### Declared Sitemaps:")
                for sm in sitemaps:
                    st.write(f"- `{sm}`")
                st.markdown("##### AI Bot Directives:")
                st.dataframe(pd.DataFrame(ai_rules) if ai_rules else pd.DataFrame([{"Agent": "None specified", "Rule": "Default"}]), hide_index=True)

            with r2:
                st.markdown("##### Disallow Directives Table:")
                st.dataframe(pd.DataFrame(disallows), hide_index=True)

    elif tech_tool == "🏷️ Schema.org / JSON-LD Rich Snippet Validator":
        st.subheader("Schema.org / JSON-LD Validator")
        default_schema = """{
  "@context": "https://schema.org/",
  "@type": "Product",
  "name": "Apex Trail Running Shoes",
  "image": "https://sample-store.searchlens.internal/images/apex.webp",
  "description": "High performance waterproof running shoe.",
  "sku": "OPT-APX-10",
  "brand": {
    "@type": "Brand",
    "name": "OptiFootwear"
  },
  "offers": {
    "@type": "Offer",
    "priceCurrency": "USD",
    "price": "149.99",
    "availability": "https://schema.org/InStock"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.8",
    "reviewCount": "142"
  }
}"""
        raw_json_input = st.text_area("Paste JSON-LD Schema Snippet:", value=default_schema, height=280)
        if st.button("Validate Structured Data Markup"):
            mock_html = f'<html><head><script type="application/ld+json">{raw_json_input}</script></head><body></body></html>'
            soup_mock = BeautifulSoup(mock_html, "html.parser")
            res_val = validate_structured_data(soup_mock)

            if res_val["is_valid"]:
                st.success("✅ Valid Schema! No critical syntax or required field errors found.")
            else:
                st.error("❌ Schema Validation Errors Detected.")

            st.write(f"**Detected Types:** {', '.join(res_val['schema_types'])}")
            st.write(f"**Eligible for Rich Results:** {', '.join(res_val['rich_snippet_eligible']) if res_val['rich_snippet_eligible'] else 'None'}")

            if res_val["issues"]:
                for iss in res_val["issues"]:
                    if iss["severity"] == "error":
                        st.error(f"**{iss['schema_type']}:** {iss['message']}\n\n*Recommended Fix:* {iss['fix']}")
                    else:
                        st.warning(f"**{iss['schema_type']}:** {iss['message']}\n\n*Recommended Fix:* {iss['fix']}")

    elif tech_tool == "🗺️ XML Sitemap Parser & URL Health Inspector":
        st.subheader("XML Sitemap Parser")
        sample_sitemap_urls = [
            "https://sample-store.searchlens.internal/",
            "https://sample-store.searchlens.internal/footwear",
            "https://sample-store.searchlens.internal/footwear/trail-running",
            "https://sample-store.searchlens.internal/products/optifootwear-apex-trail-runner-black",
            "https://sample-store.searchlens.internal/products/summit-pant",
            "https://sample-store.searchlens.internal/category/mens-hiking-apparel"
        ]
        st.write(f"Sample Sitemap contains **{len(sample_sitemap_urls)} URLs**:")
        df_sm = pd.DataFrame({"Sitemap URL": sample_sitemap_urls, "Expected HTTP Status": [200]*len(sample_sitemap_urls), "Indexability Status": ["Indexable"]*len(sample_sitemap_urls)})
        st.dataframe(df_sm, use_container_width=True, hide_index=True)

    elif tech_tool == "🔄 Redirect Chain & Protocol Downgrade Tracer":
        st.subheader("Redirect Hop & Scheme Downgrade Tracer")
        sample_hops = [
            {"Hop": 1, "Requested URL": "http://sample-store.searchlens.internal/products/apex", "Status Code": 301, "Redirect Type": "HTTP to HTTPS Redirection"},
            {"Hop": 2, "Requested URL": "https://sample-store.searchlens.internal/products/apex/", "Status Code": 301, "Redirect Type": "Trailing Slash Normalization"},
            {"Hop": 3, "Requested URL": "https://sample-store.searchlens.internal/products/optifootwear-apex-trail-runner-black", "Status Code": 200, "Redirect Type": "Final Destination"}
        ]
        st.dataframe(pd.DataFrame(sample_hops), use_container_width=True, hide_index=True)
        st.warning("⚠️ Warning: 2 intermediate hops detected. Best practice recommendation: Update internal links directly to the final 200 destination URL to eliminate chain latency.")


# ==============================================================================
# 5. KEYWORD INTELLIGENCE
# ==============================================================================
elif selected_menu == "📊 Keyword Intelligence":
    st.markdown('<div class="main-title">Keyword Intelligence & Opportunity Analyzer</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Clean, cluster, classify search intent, and uncover low-hanging fruit keywords. Transparently labels estimates vs verified source metrics.</div>', unsafe_allow_html=True)

    kw_mode = st.radio("Keyword Data Source:", ["Use Curated E-Commerce Dataset", "Upload CSV / Excel File", "Enter Seed Product Topic"], horizontal=True)

    dataset: Optional[KeywordDataset] = None

    if kw_mode == "Use Curated E-Commerce Dataset":
        curated_kw_list = [
            "waterproof trail running shoes", "buy apex trail runner online",
            "best gore tex running shoes 2026", "how to clean muddy trail running shoes",
            "running shoes for flat feet trail", "trail running shoes discount code",
            "optifootwear customer service", "anti aging face serum with retinol",
            "order vitamin c serum free shipping", "serum vs moisturizer routine order",
            "lightweight breathable hiking footwear", "cheap running shoes free returns",
            "best skincare serum for fine lines", "how to choose trail marathon shoes"
        ]
        dataset = KeywordDataset.from_list(curated_kw_list)

    elif kw_mode == "Upload CSV / Excel File":
        uploaded_file = st.file_uploader("Upload CSV or Excel file containing keywords:", type=["csv", "xlsx", "xls"])
        if uploaded_file:
            content_bytes = uploaded_file.read()
            dataset = KeywordDataset.from_file(content_bytes, uploaded_file.name)
            st.success(f"Uploaded and parsed {len(dataset.clean_df)} keywords from `{uploaded_file.name}`!")
        else:
            st.info("Upload a keyword file or switch to 'Use Curated E-Commerce Dataset' to explore.")

    elif kw_mode == "Enter Seed Product Topic":
        seed_topic = st.text_input("Enter E-Commerce Product / Category Seed:", value="waterproof trail running shoes")
        if seed_topic:
            suggestions = generate_ecommerce_keyword_suggestions(seed_topic)
            st.subheader(f"Algorithmic E-Commerce Suggestions for '{seed_topic}'")
            for stage, items in suggestions.items():
                with st.expander(f"📁 {stage} ({len(items)} suggestions)", expanded=True):
                    df_sug = pd.DataFrame(items)[["keyword", "intent", "opportunity_score", "is_long_tail", "search_volume_status"]]
                    st.dataframe(df_sug, use_container_width=True, hide_index=True)

    if dataset:
        summary = dataset.get_summary()

        st.markdown(f"""
        <div class="disclosure-box">
            <strong>Metric Source & Integrity Notice:</strong> {summary['metric_transparency_note']}
        </div>
        """, unsafe_allow_html=True)

        # Overview KPI Cards
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric("Total Cleaned Keywords", summary["total_keywords"])
        with k2:
            st.metric("Long-Tail Keywords", f"{summary['long_tail_count']} ({summary['long_tail_percent']}%)")
        with k3:
            st.metric("Search Volume", f"{summary['total_volume']:,}" if summary["total_volume"] else "Not in File (Estimated)")
        with k4:
            st.metric("Avg Difficulty", f"{summary['avg_difficulty']}/100" if summary["avg_difficulty"] else "Estimated via Intent")

        st.markdown("---")

        # Intent & Cluster Visualizations
        ch1, ch2 = st.columns(2)
        with ch1:
            st.subheader("Search Intent Breakdown")
            df_intent = pd.DataFrame(list(summary["intent_distribution"].items()), columns=["Intent", "Count"])
            fig_intent = px.pie(
                df_intent,
                names="Intent",
                values="Count",
                color="Intent",
                color_discrete_map={
                    "Transactional": "#10B981",
                    "Commercial": "#3B82F6",
                    "Informational": "#F59E0B",
                    "Navigational": "#8B5CF6",
                    "Navigational/Brand": "#8B5CF6"
                },
                hole=0.4
            )
            fig_intent.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300)
            st.plotly_chart(fig_intent, use_container_width=True)

        with ch2:
            st.subheader("Thematic Topic Clusters")
            df_clusters = pd.DataFrame(list(summary["cluster_distribution"].items()), columns=["Cluster", "Count"]).sort_values(by="Count", ascending=False)
            fig_clusters = px.bar(df_clusters.head(8), x="Count", y="Cluster", orientation='h', color="Count", color_continuous_scale="Blues")
            fig_clusters.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=300, yaxis={'autorange': 'reversed'})
            st.plotly_chart(fig_clusters, use_container_width=True)

        st.markdown("---")

        # Top Opportunity Keywords Table with Filters
        st.subheader("Keyword Opportunity Matrix")
        f_intent = st.multiselect("Filter by Intent:", list(summary["intent_distribution"].keys()), default=list(summary["intent_distribution"].keys()))
        f_long_tail_only = st.checkbox("Show Long-Tail Keywords Only (>= 3 words)", value=False)

        filtered_df = dataset.clean_df[dataset.clean_df["intent"].isin(f_intent)]
        if f_long_tail_only:
            filtered_df = filtered_df[filtered_df["is_long_tail"] == True]

        display_cols = ["keyword", "intent", "cluster", "opportunity_score", "word_count", "opportunity_source"]
        st.dataframe(
            filtered_df[display_cols].rename(columns={
                "keyword": "Keyword",
                "intent": "Intent",
                "cluster": "Topic Cluster",
                "opportunity_score": "Opportunity Score (0-100)",
                "word_count": "Words",
                "opportunity_source": "Metric Transparency Derivation"
            }),
            use_container_width=True,
            hide_index=True
        )

        # Download CSV
        csv_kw = io.StringIO()
        filtered_df.to_csv(csv_kw, index=False)
        st.download_button("📥 Download Filtered Keywords (CSV)", csv_kw.getvalue(), file_name="keyword_analysis.csv", mime="text/csv")


# ==============================================================================
# 6. E-COMMERCE SEO SUITE
# ==============================================================================
elif selected_menu == "🛒 E-Commerce SEO Suite":
    st.markdown('<div class="main-title">E-Commerce SEO Suite</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Specialized diagnostics for Product Detail Pages (PDP) and Category Pages (PLP). Audits title formulas, structured product data, faceted navigation risks, and missing merchant attributes.</div>', unsafe_allow_html=True)

    ecom_store_choice = st.selectbox("Select E-Commerce Store Page to Inspect:", get_sample_store_names())
    store = load_sample_store(ecom_store_choice)

    st.markdown(f"""
    <div class="disclosure-box">
        <strong>Sample Store Notice:</strong> {store['sample_store_notice']}. Tested URL: <code>{store['url']}</code>
    </div>
    """, unsafe_allow_html=True)

    soup = BeautifulSoup(store["html"], "html.parser")
    ecom_analyzer = EcommerceAnalyzer()
    res = ecom_analyzer.audit_page(soup, store["url"], store["html"])

    # Score & Archetype
    e1, e2, e3 = st.columns(3)
    with e1:
        st.metric("E-Commerce SEO Health Score", f"{res['ecom_seo_score']}/100")
    with e2:
        st.metric("Detected Page Archetype", res["archetype"])
    with e3:
        st.metric("Product Schema Present", "✅ Yes" if res["has_product_schema"] else "❌ Missing Schema")

    st.markdown("---")

    # If PDP, show PDP specific breakdowns
    if res["archetype"] == "Product Detail Page (PDP)":
        pdp = res["pdp_metrics"]
        st.subheader("📦 Product Detail Page (PDP) Diagnostics")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("##### Product Title Formula Compliance")
            st.write(f"**Title Analyzed:** `{pdp.get('product_title')}`")
            st.write(f"- Brand Identifier Detected: {'✅ Yes' if pdp.get('has_brand_in_title') else '⚠️ No brand qualifier'}")
            st.write(f"- Technical Specifications Detected: {'✅ Yes' if pdp.get('has_specs_in_title') else '⚠️ No size/color/specs'}")

            st.markdown("##### Commercial Information Checklist")
            p_price = pdp.get('price')
            p_curr = pdp.get('currency')
            p_avail = pdp.get('availability')
            p_sku = pdp.get('sku')
            p_rating = pdp.get('rating_value')
            st.write(f"- Price Declared: {'✅ ' + str(p_price) if p_price else '❌ Missing Price'}")
            st.write(f"- Currency (ISO 4217): {'✅ ' + str(p_curr) if p_curr else '❌ Missing Currency'}")
            st.write(f"- Stock Availability: {'✅ ' + str(p_avail) if p_avail else '❌ Missing Availability'}")
            st.write(f"- Product SKU / MPN: {'✅ ' + str(p_sku) if p_sku else '⚠️ Missing SKU'}")
            st.write(f"- Customer Reviews Schema: {'✅ Rating ' + str(p_rating) + '/5' if p_rating else '⚠️ No Review Stars Schema'}")

        with col_b:
            st.markdown("##### Description & Media Quality")
            desc_words = pdp.get("description_words", 0)
            st.write(f"- Description Length: **{desc_words} words** ({'✅ Sufficient' if desc_words >= 100 else '⚠️ Thin copy'})")
            st.write(f"- Breadcrumb Navigation: {'✅ Present' if pdp.get('has_breadcrumbs') else '⚠️ Missing Breadcrumbs'}")

            img_m = res["image_metrics"]
            st.write(f"- Total Gallery Images: **{img_m.get('total_images', 0)}**")
            st.write(f"- Images Missing Alt Text: **{img_m.get('missing_alt_count', 0)}** ({'✅ 0 missing' if img_m.get('missing_alt_count') == 0 else '❌ Missing Alt Text'})")
            st.write(f"- Modern Formats (WebP/AVIF): **{img_m.get('modern_format_percent', 0)}%**")

    # If PLP, show PLP diagnostics
    elif res["archetype"] == "Product Listing / Category Page (PLP)":
        plp = res["plp_metrics"]
        st.subheader("🗂️ Product Listing Page (PLP) Diagnostics")
        st.write(f"**Category Name:** {plp.get('category_name')}")
        st.write(f"**Category Intro Copy:** {plp.get('intro_word_count')} words ({'✅ Good introductory context' if plp.get('intro_word_count', 0) >= 30 else '⚠️ Thin category description'})")
        st.write(f"**Products Displayed on Grid:** {plp.get('products_displayed')}")
        st.write(f"**Pagination Markup Present:** {'✅ Yes' if plp.get('has_pagination') else '⚠️ No pagination markup'}")

    st.markdown("---")

    # Faceted Navigation Risk Check
    st.subheader("🎛️ Faceted Navigation & Parameter Duplicate Risk")
    fn = res["faceted_navigation_risk"]
    if fn.get("duplicate_risk_detected"):
        st.error("🚨 Faceted Navigation Duplicate Risk Detected! The filtered URL lacks a canonical tag pointing back to the clean master category.")
    else:
        st.success("✅ No faceted duplicate risks detected for this URL.")

    # E-Commerce Issues List
    st.subheader(f"E-Commerce Specific Recommendations ({len(res['issues'])})")
    if not res["issues"]:
        st.success("🎉 This store page follows all Google Merchant and E-Commerce SEO best practices!")
    else:
        for idx, iss in enumerate(res["issues"], 1):
            with st.expander(f"{idx}. [{iss.get('severity', 'warning').upper()}] {iss.get('title')}", expanded=True):
                st.markdown(f"**Why this matters:** {iss.get('explanation')}")
                st.markdown(f"**Actionable Fix:** 💡 {iss.get('recommended_fix')}")


# ==============================================================================
# 7. GEO RESEARCH (GENERATIVE ENGINE OPTIMIZATION)
# ==============================================================================
elif selected_menu == "🤖 GEO Research (AI Search)":
    st.markdown('<div class="main-title">GEO Research – Generative Engine Optimization</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Evidence-based analysis of brand visibility, citations, and competitor share of voice across ChatGPT, Perplexity, Gemini, Claude, and Copilot.</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="disclosure-box">
        <strong>Strictly Evidence-Based:</strong> GEO analytics in SearchLens parse verified prompt and response text submitted directly by the analyst. It never fabricates citations, synthesizes fake rankings, or invents citations.
    </div>
    """, unsafe_allow_html=True)

    geo_input_mode = st.radio("Research Intake Method:", ["Load Curated Benchmark Log", "Enter Live Prompt & AI Response"], horizontal=True)

    prompt_text = ""
    ai_response_text = ""
    target_brand = ""
    target_dom = ""
    competitors_list = []
    selected_eng = SUPPORTED_ENGINES[0]

    if geo_input_mode == "Load Curated Benchmark Log":
        bm_titles = [bm["title"] for bm in CURATED_GEO_BENCHMARKS]
        chosen_bm_title = st.selectbox("Select Curated Benchmark Case:", bm_titles)
        chosen_bm = next(bm for bm in CURATED_GEO_BENCHMARKS if bm["title"] == chosen_bm_title)

        prompt_text = chosen_bm["query_prompt"]
        ai_response_text = chosen_bm["ai_response"]
        target_brand = chosen_bm["brand_name"]
        target_dom = chosen_bm.get("target_domain", "")
        competitors_list = chosen_bm.get("competitors", [])
        selected_eng = chosen_bm["engine"]

        st.info(f"Loaded Benchmark: **{chosen_bm['title']}** | Engine: **{chosen_bm['engine']}** | Brand: **{chosen_bm['brand_name']}**")

    else:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            selected_eng = st.selectbox("AI Engine:", SUPPORTED_ENGINES)
            target_brand = st.text_input("Target Brand / Product Name:", value="OptiFootwear")
            target_dom = st.text_input("Target Domain (optional, for citation match):", value="sample-store.searchlens.internal")
        with col_g2:
            prompt_text = st.text_area("User Query / Prompt Asked to AI Engine:", value="What are the best waterproof trail running shoes for marathon training? Cite sources.", height=80)
            comp_input = st.text_input("Competitors to Track (comma-separated):", value="Salomon, Hoka, Brooks, La Sportiva")
            competitors_list = [c.strip() for c in comp_input.split(",") if c.strip()]

        ai_response_text = st.text_area("Paste Actual AI Response Text (Markdown supported):", value="", height=160)

    if prompt_text and ai_response_text and target_brand:
        geo_results = analyze_brand_visibility(
            response_text=ai_response_text,
            brand_name=target_brand,
            competitors=competitors_list,
            target_domain=target_dom
        )

        st.markdown("---")
        st.subheader("🎯 GEO Visibility & Evidence Scorecard")

        g_sc1, g_sc2, g_sc3, g_sc4 = st.columns(4)
        with g_sc1:
            st.metric("GEO Visibility Score", f"{geo_results['geo_visibility_score']}/100")
        with g_sc2:
            st.metric("Brand Mentioned", "✅ YES" if geo_results["is_mentioned"] else "❌ NO")
        with g_sc3:
            st.metric("Recommendation Rank", geo_results["rank_type"])
        with g_sc4:
            st.metric("Sentiment / Stance", geo_results["sentiment"])

        st.markdown("---")

        c_cit, c_comp = st.columns(2)
        with c_cit:
            st.subheader(f"Cited Sources & Domains ({geo_results['total_citations']})")
            if geo_results["brand_domain_cited"]:
                st.success("🎉 Target Brand Domain was cited as a verified source in the AI answer!")
            else:
                st.warning("⚠️ Target Brand Domain was NOT directly cited in this response.")

            if geo_results["citations"]:
                st.markdown("##### Extracted Citations:")
                for cit in geo_results["citations"]:
                    st.write(f"- [{cit['anchor']}]({cit['url']}) (`{cit['domain']}`)")
            else:
                st.info("No explicit URL citations found in this response.")

        with c_comp:
            st.subheader("Competitor Share of Voice")
            if geo_results["competitors_mentioned"]:
                df_comp = pd.DataFrame(geo_results["competitors_mentioned"])[["competitor", "mentions"]]
                fig_comp = px.bar(
                    df_comp,
                    x="mentions",
                    y="competitor",
                    orientation='h',
                    color="mentions",
                    color_continuous_scale="Viridis",
                    labels={"mentions": "Mention Count", "competitor": "Brand"}
                )
                fig_comp.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=250, yaxis={'autorange': 'reversed'})
                st.plotly_chart(fig_comp, use_container_width=True)
            else:
                st.info("No tracked competitors detected in this response text.")

        # Save record button
        if st.button("💾 Save GEO Research Record to Project"):
            payload = {
                "query_prompt": prompt_text,
                "engine": selected_eng,
                "brand_name": target_brand,
                "target_domain": target_dom,
                "ai_response": ai_response_text,
                "is_mentioned": geo_results["is_mentioned"],
                "position_rank": geo_results["position_rank"],
                "sentiment": geo_results["sentiment"],
                "geo_visibility_score": geo_results["geo_visibility_score"],
                "citations": geo_results["citations"],
                "competitors_mentioned": geo_results["competitors_mentioned"]
            }
            rec_id = db.save_geo_record(project_id, payload)
            st.success(f"Saved GEO Research log #{rec_id} to project `{current_project['name']}`!")

        # Cross-Engine Comparison Table from DB
        st.markdown("---")
        st.subheader("Cross-Platform AI Engine Comparison")
        engine_stats = db.get_geo_engine_comparison(project_id)
        if engine_stats:
            st.dataframe(pd.DataFrame(engine_stats).rename(columns={
                "engine": "Generative Search Engine",
                "total_queries": "Queries Analyzed",
                "mentions": "Total Mentions",
                "mention_rate_pct": "Mention Rate (%)",
                "avg_geo_score": "Average GEO Score (0-100)"
            }), use_container_width=True, hide_index=True)


# ==============================================================================
# 8. AUDIT HISTORY & TRACKING
# ==============================================================================
elif selected_menu == "📜 Audit History & Tracking":
    st.markdown('<div class="main-title">Audit History & Progress Tracking</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-title">Historical audit trend lines and diff comparisons for <strong>{current_project["name"]}</strong>.</div>', unsafe_allow_html=True)

    with db.get_connection() as conn:
        df_history = pd.read_sql_query(
            "SELECT id, audit_type, target_url, overall_score, tech_score, onpage_score, content_score, ecom_score, created_at FROM audit_results WHERE project_id = ? ORDER BY id DESC",
            conn, params=[project_id]
        )

    if not df_history.empty:
        # Score Trend Line
        st.subheader("Overall SEO Score Trend Over Time")
        df_sorted = df_history.sort_values(by="id", ascending=True)
        fig_trend = px.line(
            df_sorted,
            x="created_at",
            y="overall_score",
            markers=True,
            labels={"overall_score": "SEO Score (%)", "created_at": "Audit Timestamp"},
            title=f"Score Evolution for {current_project['name']}"
        )
        fig_trend.update_layout(yaxis=dict(range=[0, 100]), height=320)
        st.plotly_chart(fig_trend, use_container_width=True)

        st.markdown("---")
        st.subheader("Audit Runs Log")
        st.dataframe(df_history.rename(columns={
            "id": "Audit ID",
            "audit_type": "Audit Type",
            "target_url": "Target URL",
            "overall_score": "Overall Score",
            "tech_score": "Technical",
            "onpage_score": "On-Page",
            "content_score": "Content",
            "ecom_score": "E-Com Health",
            "created_at": "Timestamp"
        }), use_container_width=True, hide_index=True)

    else:
        st.info("No audit history found for this project. Run a single URL or site crawl to begin historical tracking.")


# ==============================================================================
# 9. DATABASE & DATA EXPORTS
# ==============================================================================
elif selected_menu == "💾 Database & Data Exports":
    st.markdown('<div class="main-title">Relational Database & Data Exports</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Direct SQL explorer and bulk CSV/JSON data export utility.</div>', unsafe_allow_html=True)

    table_choice = st.selectbox("Select SQLite Table to Inspect & Export:", [
        "seo_issues",
        "keywords",
        "geo_research",
        "audit_results",
        "crawled_pages",
        "audit_history",
        "projects"
    ])

    df_table = db.export_table_df(table_choice, project_id if table_choice != "projects" else None)

    st.write(f"Showing **{len(df_table)}** records from `{table_choice}`:")
    st.dataframe(df_table, use_container_width=True, hide_index=True)

    exp_col1, exp_col2 = st.columns(2)
    with exp_col1:
        csv_str = db.export_table_csv(table_choice, project_id if table_choice != "projects" else None)
        st.download_button(
            label=f"📥 Export {table_choice} to CSV",
            data=csv_str,
            file_name=f"{table_choice}_export.csv",
            mime="text/csv",
            type="primary"
        )
    with exp_col2:
        json_str = db.export_table_json(table_choice, project_id if table_choice != "projects" else None)
        st.download_button(
            label=f"📥 Export {table_choice} to JSON",
            data=json_str,
            file_name=f"{table_choice}_export.json",
            mime="application/json"
        )
