"""
Unit tests for Technical SEO signals and Schema.org structured data validation.
"""
import pytest
from bs4 import BeautifulSoup
from modules.technical.html_core import (
    check_doctype,
    check_character_encoding,
    check_viewport_meta,
    check_canonical_tag,
    check_meta_robots
)
from modules.technical.structured_data import validate_structured_data


def test_core_html_signals():
    html = """<!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="canonical" href="https://example.com/clean-path">
        <meta name="robots" content="index, follow">
    </head>
    <body>Hello World</body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    assert check_doctype(soup)["isDoctype"] is True
    assert check_character_encoding(soup)["isCharacterEncode"] is True
    assert check_viewport_meta(soup)["viewport"] is True

    can_res = check_canonical_tag(soup, "https://example.com/clean-path?utm_source=fb")
    assert can_res["hasCanonicalTag"] is True
    assert can_res["canonicalUrl"] == "https://example.com/clean-path"

    rob_res = check_meta_robots(soup)
    assert rob_res["hasMetaNoindex"] is False


def test_structured_data_product_valid():
    html = """
    <html><head>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": "Apex Trail Running Shoe",
        "description": "Trail running shoe with waterproof membrane.",
        "sku": "SKU-12345",
        "offers": {
            "@type": "Offer",
            "price": "129.99",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock"
        },
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.9",
            "reviewCount": "50"
        }
    }
    </script>
    </head></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    res = validate_structured_data(soup)
    assert res["has_schema"] is True
    assert "Product" in res["schema_types"]
    assert res["is_valid"] is True
    assert any("Product Rich Result" in r for r in res["rich_snippet_eligible"])


def test_structured_data_product_missing_offers_price():
    html = """
    <html><head>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": "Flawed Shoe Without Price"
    }
    </script>
    </head></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    res = validate_structured_data(soup)
    assert res["has_schema"] is True
    assert res["is_valid"] is False
    assert any(i["field"] == "offers" for i in res["issues"])


def test_structured_data_breadcrumbs():
    html = """
    <html><head>
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://example.com"},
            {"@type": "ListItem", "position": 2, "name": "Footwear", "item": "https://example.com/shoes"}
        ]
    }
    </script>
    </head></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    res = validate_structured_data(soup)
    assert "BreadcrumbList" in res["schema_types"]
    assert any("Breadcrumb Trail" in r for r in res["rich_snippet_eligible"])

