"""
Unit tests for E-Commerce SEO Suite and Sample Store Audits.
"""
import pytest
from bs4 import BeautifulSoup
from modules.ecommerce import (
    EcommerceAnalyzer,
    SAMPLE_STORES,
    load_sample_store
)


def test_optimized_pdp_sample_store():
    store = load_sample_store("OptiFootwear - Elite Trail Running Shoes (Optimized PDP)")
    soup = BeautifulSoup(store["html"], "html.parser")
    res = EcommerceAnalyzer().audit_page(soup, store["url"], store["html"])

    assert res["archetype"] == "Product Detail Page (PDP)"
    assert res["has_product_schema"] is True
    assert res["has_breadcrumb_schema"] is True
    assert res["ecom_seo_score"] >= 90

    pdp = res["pdp_metrics"]
    assert pdp["price"] == "149.99"
    assert pdp["currency"] == "USD"
    assert pdp["has_brand_in_title"] is True
    assert pdp["has_specs_in_title"] is True
    assert pdp["description_words"] >= 100
    assert pdp["has_breadcrumbs"] is True

    # Zero critical errors
    critical_errors = [i for i in res["issues"] if i["severity"] == "error"]
    assert len(critical_errors) == 0


def test_flawed_pdp_sample_store():
    store = load_sample_store("LuxeGlow Skincare - Anti-Aging Serum (Flawed PDP with SEO Errors)")
    soup = BeautifulSoup(store["html"], "html.parser")
    res = EcommerceAnalyzer().audit_page(soup, store["url"], store["html"])

    assert res["archetype"] == "Product Detail Page (PDP)"
    assert res["ecom_seo_score"] < 70

    issue_codes = [i["code"] for i in res["issues"]]
    # Should catch thin description, missing availability, missing SKU, faceted self-canonical, missing alt
    assert "ECOM_THIN_PRODUCT_DESC" in issue_codes
    assert "ECOM_MISSING_AVAILABILITY" in issue_codes
    assert "ECOM_MISSING_SKU" in issue_codes
    assert "ECOM_FACET_SELF_CANONICAL" in issue_codes
    assert "ECOM_IMAGES_NO_ALT" in issue_codes


def test_category_plp_sample_store():
    store = load_sample_store("PeakGear Outdoor Store - Men's Hiking Apparel (PLP Category Page)")
    soup = BeautifulSoup(store["html"], "html.parser")
    res = EcommerceAnalyzer().audit_page(soup, store["url"], store["html"])

    assert res["archetype"] == "Product Listing / Category Page (PLP)"
    plp = res["plp_metrics"]
    assert plp["intro_word_count"] > 30
    assert plp["products_displayed"] == 3
    assert plp["has_pagination"] is True
