"""
Seeds realistic demo project data, GEO benchmarks, and keywords for SearchLens portfolio showcase.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from .db import SearchLensDB
from ..geo import CURATED_GEO_BENCHMARKS, analyze_brand_visibility
from ..ecommerce import load_sample_store, EcommerceAnalyzer
from bs4 import BeautifulSoup


def seed_portfolio_data(db: SearchLensDB):
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM audit_results")
        if cur.fetchone()[0] > 0:
            return  # Already seeded

    project_id = 1  # Demo E-Commerce Store

    # 1. Seed Audits: A previous audit from 7 days ago and a current audit
    opti_store = load_sample_store("OptiFootwear - Elite Trail Running Shoes (Optimized PDP)")
    soup_opti = BeautifulSoup(opti_store["html"], "html.parser")
    res_opti = EcommerceAnalyzer().audit_page(soup_opti, opti_store["url"])

    # Previous baseline audit
    prev_time = (datetime.now() - timedelta(days=7)).isoformat()
    baseline_issues = [
        {"code": "ECOM_MISSING_SKU", "title": "Missing Product SKU / Identifier", "severity": "notice", "category": "ecommerce", "details": "Add sku to Product schema"},
        {"code": "NO_LLM_TXT", "title": "No llms.txt Directive Found", "severity": "notice", "category": "ai", "details": "Create /llms.txt for AI agents"},
        {"code": "SHORT_META_DESC", "title": "Meta Description Too Short", "severity": "notice", "category": "on_page", "details": "Expand to 140 chars"}
    ]
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO audit_results (project_id, audit_type, target_url, overall_score, tech_score, onpage_score, content_score, ecom_score, summary_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (project_id, "ecommerce", opti_store["url"], 78.5, 82.0, 75.0, 78.0, 80.0, json.dumps({"note": "Initial baseline crawl"}), prev_time))
        prev_audit_id = cur.lastrowid
        for iss in baseline_issues:
            cur.execute("""
            INSERT INTO seo_issues (audit_id, project_id, url, code, title, severity, category, explanation, recommended_fix, details, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (prev_audit_id, project_id, opti_store["url"], iss["code"], iss["title"], iss["severity"], iss["category"], iss["title"], iss["details"], iss["details"], prev_time))
        cur.execute("INSERT INTO audit_history (project_id, metric_name, metric_value, notes, recorded_at) VALUES (?, ?, ?, ?, ?)",
                    (project_id, "overall_score", 78.5, "Baseline audit", prev_time))
        conn.commit()

    # Current optimized audit
    current_time = datetime.now().isoformat()
    db.save_audit(
        project_id=project_id,
        target_url=opti_store["url"],
        audit_type="ecommerce",
        scores={
            "overall_score": 96.0,
            "tech_score": 98.0,
            "onpage_score": 95.0,
            "content_score": 95.0,
            "ecom_score": 100.0
        },
        issues=[
            {
                "url": opti_store["url"],
                "code": "NO_LLM_TXT",
                "title": "No llms.txt Directive Found",
                "severity": "notice",
                "category": "ai",
                "explanation": "No llms.txt file detected on domain. AI search engines benefit from clean markdown index.",
                "recommended_fix": "Add /llms.txt declaring core brand products and documentation.",
                "details": "Consider adding /llms.txt"
            }
        ],
        summary={"status": "Optimized trail running shoes PDP"}
    )

    # 2. Seed GEO Benchmarks
    for bm in CURATED_GEO_BENCHMARKS:
        analysis = analyze_brand_visibility(
            response_text=bm["ai_response"],
            brand_name=bm["brand_name"],
            competitors=bm["competitors"],
            target_domain=bm["target_domain"]
        )
        geo_payload = {
            "query_prompt": bm["query_prompt"],
            "engine": bm["engine"],
            "brand_name": bm["brand_name"],
            "target_domain": bm["target_domain"],
            "ai_response": bm["ai_response"],
            "is_mentioned": analysis["is_mentioned"],
            "position_rank": analysis["position_rank"],
            "sentiment": analysis["sentiment"],
            "geo_visibility_score": analysis["geo_visibility_score"],
            "citations": analysis["citations"],
            "competitors_mentioned": analysis["competitors_mentioned"]
        }
        db.save_geo_record(project_id, geo_payload)

    # 3. Seed E-commerce Keywords
    seed_kw_data = [
        {"keyword": "waterproof trail running shoes", "search_volume": 14800, "difficulty": 42.0, "cpc": 1.85, "intent": "Commercial", "cluster": "Shoes", "is_long_tail": True, "opportunity_score": 88.5, "source": "Semrush CSV Export"},
        {"keyword": "buy apex trail runner online", "search_volume": 3200, "difficulty": 28.0, "cpc": 2.40, "intent": "Transactional", "cluster": "Shoes", "is_long_tail": True, "opportunity_score": 92.0, "source": "Semrush CSV Export"},
        {"keyword": "best gore tex running shoes 2026", "search_volume": 8900, "difficulty": 48.0, "cpc": 1.60, "intent": "Commercial", "cluster": "Shoes", "is_long_tail": True, "opportunity_score": 82.0, "source": "Semrush CSV Export"},
        {"keyword": "how to clean muddy trail running shoes", "search_volume": 4100, "difficulty": 18.0, "cpc": 0.45, "intent": "Informational", "cluster": "Shoes", "is_long_tail": True, "opportunity_score": 85.0, "source": "Ahrefs Export"},
        {"keyword": "running shoes for flat feet trail", "search_volume": 6600, "difficulty": 35.0, "cpc": 1.95, "intent": "Commercial", "cluster": "Shoes", "is_long_tail": True, "opportunity_score": 86.0, "source": "Ahrefs Export"},
        {"keyword": "trail running shoes discount code", "search_volume": 2100, "difficulty": 22.0, "cpc": 1.30, "intent": "Transactional", "cluster": "Shoes", "is_long_tail": True, "opportunity_score": 89.0, "source": "Google Keyword Planner"},
        {"keyword": "optifootwear customer service", "search_volume": 850, "difficulty": 12.0, "cpc": 0.80, "intent": "Navigational", "cluster": "Optifootwear", "is_long_tail": True, "opportunity_score": 64.0, "source": "Internal Search Console"},
        {"keyword": "anti aging face serum with retinol", "search_volume": 22000, "difficulty": 64.0, "cpc": 3.10, "intent": "Commercial", "cluster": "Serum", "is_long_tail": True, "opportunity_score": 75.0, "source": "Semrush CSV Export"},
        {"keyword": "order vitamin c serum free shipping", "search_volume": 4800, "difficulty": 32.0, "cpc": 2.75, "intent": "Transactional", "cluster": "Serum", "is_long_tail": True, "opportunity_score": 90.5, "source": "Semrush CSV Export"},
        {"keyword": "serum vs moisturizer routine order", "search_volume": 9400, "difficulty": 24.0, "cpc": 0.90, "intent": "Informational", "cluster": "Serum", "is_long_tail": True, "opportunity_score": 84.0, "source": "Ahrefs Export"}
    ]
    import pandas as pd
    df_kw = pd.DataFrame(seed_kw_data)
    db.save_keywords(project_id, df_kw, source_label="Curated Seed Dataset")
