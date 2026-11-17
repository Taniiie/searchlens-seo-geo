"""
Unit tests for On-Page SEO elements and Content Analysis.
"""
import pytest
from bs4 import BeautifulSoup
from modules.on_page.title_meta import check_title, check_meta_description
from modules.on_page.headings_links_images import check_headings, check_images
from modules.content.readability import calculate_flesch_reading_ease
from modules.content.ratio import calculate_text_to_html_ratio


def test_title_tag_validation():
    # Good title
    html = "<html><head><title>Apex Trail Running Shoes - Waterproof Black | OptiFootwear</title></head></html>"
    soup = BeautifulSoup(html, "html.parser")
    res = check_title(soup, 20, 70, target_keywords=["trail running shoes"])
    assert res["isTitle"] is True
    assert res["titleLength"] > 20
    assert res["isTitleEnoughLong"] is True
    assert res["titlePrimaryKeywordPresent"] is True

    # Missing title
    html_empty = "<html><head></head></html>"
    soup_empty = BeautifulSoup(html_empty, "html.parser")
    res_empty = check_title(soup_empty, 20, 70)
    assert res_empty["isTitle"] is False
    assert res_empty["titleLength"] == 0

    # Short title
    html_short = "<html><head><title>Shoes</title></head></html>"
    soup_short = BeautifulSoup(html_short, "html.parser")
    res_short = check_title(soup_short, 20, 70)
    assert res_short["isTitleEnoughLong"] is False


def test_meta_description():
    html = '<html><head><meta name="description" content="Explore high-performance waterproof running shoes engineered for extreme alpine terrain. Free domestic shipping."></head></html>'
    soup = BeautifulSoup(html, "html.parser")
    res = check_meta_description(soup, 50, 160, target_keywords=["waterproof running shoes"])
    assert res["isMetaDescription"] is True
    assert res["isMetaDescriptionEnoughLong"] is True
    assert res["metaContainsPrimaryKeyword"] is True


def test_headings_hierarchy():
    # Correct hierarchy: single H1
    html = "<html><body><h1>Main Product Title</h1><h2>Features</h2><h3>Details</h3></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    res = check_headings(soup, primary_keyword="Product")
    assert res["h1Count"] == 1
    assert res["h2Count"] == 1
    assert res["h3Count"] == 1
    assert res["isH1OnlyOne"] is True

    # Multiple H1s
    html_multi = "<html><body><h1>First Title</h1><h1>Second Title</h1></body></html>"
    soup_multi = BeautifulSoup(html_multi, "html.parser")
    res_multi = check_headings(soup_multi)
    assert res_multi["h1Count"] == 2
    assert res_multi["isH1OnlyOne"] is False


def test_images_alt_attributes():
    html = """
    <html><body>
        <img src="pic1.jpg" alt="Trail shoes front view">
        <img src="pic2.jpg">
        <img src="pic3.jpg" alt="">
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    res = check_images(soup, "https://example.com", headers={}, request_timeout=5, active_check_limit=0)
    assert res["total_images_on_page"] == 3
    # 2 images missing alt text
    assert res["notOptimizedImagesCount"] == 2


def test_readability_and_text_ratio():
    # Provide at least 100 words and 3 sentences
    text = (
        "Running along technical mountain trails requires durable and supportive footwear. "
        "Trail runners must protect feet against sharp stones, wet roots, and steep mud descents. "
        "Modern engineered trail running shoes feature dual density foam midsoles to absorb heavy impacts. "
        "Furthermore, breathable waterproof membranes keep socks dry while allowing internal moisture to escape easily. "
        "When choosing the right shoes for your ultra marathon training, always consider the heel to toe drop and lug depth. "
        "High quality vibram rubber lugs provide unmatched grip on slick limestone ridges during wet rainy seasons. "
        "Proper foot care and breaking in your footwear will prevent painful blisters on long distance hikes."
    )
    res = calculate_flesch_reading_ease(text)
    assert "flesch_reading_ease_score" in res
    assert res["flesch_reading_ease_score"] is not None
    assert res["flesch_reading_ease_score"] > 0

    ratio_res = calculate_text_to_html_ratio(text, "<html><body><p>" + text + "</p></body></html>")
    assert "textToHtmlRatioPercent" in ratio_res
    assert ratio_res["textToHtmlRatioPercent"] > 0
