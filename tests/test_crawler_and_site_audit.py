"""
Unit tests for Crawler, URL Discovery, and Issue derivation.
"""
import pytest
from modules.site_audit.crawler import _normalize_url, CrawlConfig
from modules.site_audit.duplication import _norm_text, duplicate_text_by_hash
from modules.site_audit.issues import derive_issues, Issue


def test_url_normalization():
    base = "https://example.com/products/shoes"
    assert _normalize_url(base, "/contact") == "https://example.com/contact"
    assert _normalize_url(base, "details.html") == "https://example.com/products/details.html"
    assert _normalize_url(base, "#reviews") is None
    assert _normalize_url(base, "javascript:void(0)") is None
    assert _normalize_url(base, "mailto:support@example.com") is None


def test_duplicate_text_detection():
    pages = [
        {"url": "https://example.com/p1", "seo_attributes": {"OnPageAnalyzer": {"visibleTextHash": "abc123hash"}}},
        {"url": "https://example.com/p2", "seo_attributes": {"OnPageAnalyzer": {"visibleTextHash": "abc123hash"}}},
        {"url": "https://example.com/p3", "seo_attributes": {"OnPageAnalyzer": {"visibleTextHash": "uniquehash"}}}
    ]
    dupes = duplicate_text_by_hash(pages)
    assert "abc123hash" in dupes
    assert len(dupes["abc123hash"]) == 2


def test_issue_derivation_structure():
    # Page with multiple severe issues
    mock_attrs = {
        "TechnicalSEOAnalyzer": {
            "httpStatusCode": 404,
            "hasCanonicalTag": False,
            "hasHttps": False,
            "viewport": False
        },
        "OnPageAnalyzer": {
            "isTitle": False,
            "isMetaDescription": False,
            "h1Count": 0,
            "notOptimizedImagesCount": 5
        }
    }
    issues = derive_issues("https://example.com/404-page", mock_attrs)
    assert len(issues) > 0

    codes = [i.code for i in issues]
    assert "HTTP_404" in codes
    assert "NO_CANONICAL" in codes
    assert "NO_VIEWPORT" in codes
    assert "MISSING_TITLE" in codes
    assert "MISSING_H1" in codes
    assert "IMAGES_MISSING_ALT" in codes

    # Ensure every single issue adheres to Phase 2 requirements:
    for iss in issues:
        assert iss.url == "https://example.com/404-page"
        assert iss.severity in ("error", "warning", "notice")
        assert len(iss.explanation) > 10, f"Issue {iss.code} missing explanation"
        assert len(iss.recommended_fix) > 10, f"Issue {iss.code} missing recommended fix"
