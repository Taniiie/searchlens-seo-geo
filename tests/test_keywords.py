"""
Unit tests for Keyword Intelligence: Intent classification, Long-tail, Opportunity scoring, and Suggestions.
"""
import pytest
import pandas as pd
from modules.keywords import (
    classify_intent,
    is_long_tail,
    calculate_opportunity_score,
    KeywordDataset,
    generate_ecommerce_keyword_suggestions
)


def test_intent_classification():
    assert classify_intent("buy waterproof trail running shoes online")[0] == "Transactional"
    assert classify_intent("trail shoes discount code coupon")[0] == "Transactional"
    assert classify_intent("best trail running shoes 2026 vs alternatives")[0] == "Commercial"
    assert classify_intent("how to clean mud off running shoes")[0] == "Informational"
    assert classify_intent("what is heel to toe drop in trail shoes")[0] == "Informational"
    assert classify_intent("optifootwear customer login portal")[0] == "Navigational"


def test_long_tail_identification():
    assert is_long_tail("shoes") is False
    assert is_long_tail("running shoes") is False
    assert is_long_tail("trail running shoes") is True
    assert is_long_tail("best waterproof trail shoes for men") is True


def test_opportunity_score_with_real_metrics():
    # High volume, low difficulty = high score
    score, src = calculate_opportunity_score(volume=12000, difficulty=25.0, intent="Transactional", word_count=4)
    assert score >= 75.0
    assert "uploaded Search Volume" in src

    # High volume, high difficulty = moderate score
    score_hard, _ = calculate_opportunity_score(volume=12000, difficulty=85.0, intent="Informational", word_count=2)
    assert score_hard < score


def test_opportunity_score_with_missing_metrics():
    # Must transparently flag that metrics were estimated via query specificity & intent
    score, src = calculate_opportunity_score(volume=None, difficulty=None, intent="Transactional", word_count=4)
    assert "Estimated via Query Specificity & Intent" in src
    assert score > 0


def test_keyword_dataset_processing():
    raw_keywords = [
        "waterproof trail running shoes",
        "buy running shoes",
        "best running shoes 2026",
        "shoes",
        "how to clean sneakers",
        "waterproof trail running shoes"  # Duplicate
    ]
    ds = KeywordDataset.from_list(raw_keywords)
    # Deduplication
    assert len(ds.clean_df) == 5

    summary = ds.get_summary()
    assert summary["total_keywords"] == 5
    assert summary["long_tail_count"] >= 3
    assert "Shoes" in summary["cluster_distribution"]


def test_ecommerce_suggestions():
    sugs = generate_ecommerce_keyword_suggestions("trail running shoes")
    assert "Category & Attribute Keywords" in sugs
    assert "Buyer Intent & Transactional" in sugs
    assert any("buy trail running shoes" in item["keyword"] for item in sugs["Buyer Intent & Transactional"])
