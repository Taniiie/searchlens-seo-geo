"""
Unit tests for GEO Research (AI Search Optimization) and SQLite Storage operations.
"""
import pytest
import os
import tempfile
from modules.geo import extract_cited_urls, analyze_brand_visibility, CURATED_GEO_BENCHMARKS
from modules.storage import SearchLensDB


def test_extract_cited_urls():
    text = """
    Check out [Trail Runner Magazine](https://trailrunnermag.com/best-shoes) and
    [GearJunkie Review](https://gearjunkie.com/footwear/waterproof-runners) for more details.
    You can also visit https://example.com/running directly.
    """
    citations = extract_cited_urls(text)
    assert len(citations) == 3
    domains = [c["domain"] for c in citations]
    assert "trailrunnermag.com" in domains
    assert "gearjunkie.com" in domains
    assert "example.com" in domains


def test_geo_brand_visibility_analysis():
    bm = CURATED_GEO_BENCHMARKS[0]  # OptiFootwear benchmark
    res = analyze_brand_visibility(
        response_text=bm["ai_response"],
        brand_name=bm["brand_name"],
        competitors=bm["competitors"],
        target_domain=bm["target_domain"]
    )
    assert res["is_mentioned"] is True
    assert res["mentions_count"] >= 1
    assert res["position_rank"] == 1  # Top recommendation
    assert res["geo_visibility_score"] >= 80
    assert res["brand_domain_cited"] is True
    assert len(res["competitors_mentioned"]) >= 2


def test_geo_unmentioned_brand():
    response = "The top recommended trail shoes are Salomon Speedcross and Hoka Speedgoat."
    res = analyze_brand_visibility(
        response_text=response,
        brand_name="UnknownBrand",
        competitors=["Salomon", "Hoka"]
    )
    assert res["is_mentioned"] is False
    assert res["mentions_count"] == 0
    assert res["geo_visibility_score"] == 0
    assert len(res["competitors_mentioned"]) == 2


def test_sqlite_database_lifecycle():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db = SearchLensDB(db_path=db_path)
        pid = db.get_or_create_project("Test Ecom Store", "test-store.com", "Test notes")
        assert pid is not None

        # Save audit
        scores = {"overall_score": 88.0, "tech_score": 90.0, "onpage_score": 85.0}
        issues = [
            {"code": "MISSING_TITLE", "title": "Missing Title", "severity": "error", "category": "on_page", "details": "Add title tag"}
        ]
        aid = db.save_audit(pid, "https://test-store.com", "single_page", scores, issues)
        assert aid is not None

        # Check issues query
        common = db.get_most_common_issues(pid)
        assert len(common) == 1
        assert common[0]["code"] == "MISSING_TITLE"

        # Check comparison query
        comp = db.get_audit_comparison(pid)
        assert comp["has_comparison"] is True

        # CSV / JSON export
        csv_out = db.export_table_csv("seo_issues", pid)
        assert "MISSING_TITLE" in csv_out
        json_out = db.export_table_json("seo_issues", pid)
        assert "MISSING_TITLE" in json_out

    finally:
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except Exception:
            pass
