"""
SearchLens Structured Data (Schema.org / JSON-LD / Microdata) Validator
Validates common Schema.org types with deep e-commerce and technical checks.
"""
from __future__ import annotations

import json
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup


SCHEMA_RULES = {
    "Product": {
        "required": ["name"],
        "recommended": ["image", "description", "offers", "sku", "brand", "aggregateRating"],
        "ecom_critical": ["offers", "price", "priceCurrency", "availability"]
    },
    "Offer": {
        "required": ["price", "priceCurrency"],
        "recommended": ["availability", "itemCondition", "priceValidUntil", "url"],
    },
    "AggregateRating": {
        "required": ["ratingValue"],
        "recommended": ["reviewCount", "ratingCount", "bestRating", "worstRating"],
    },
    "BreadcrumbList": {
        "required": ["itemListElement"],
        "recommended": [],
    },
    "Organization": {
        "required": ["name"],
        "recommended": ["url", "logo", "sameAs", "contactPoint"],
    },
    "FAQPage": {
        "required": ["mainEntity"],
        "recommended": [],
    },
    "Article": {
        "required": ["headline"],
        "recommended": ["image", "datePublished", "author", "publisher"],
    },
    "WebSite": {
        "required": ["name", "url"],
        "recommended": ["potentialAction"],
    }
}


def _normalize_type(t: Any) -> str:
    if isinstance(t, list) and t:
        t = t[0]
    if isinstance(t, str):
        if "/" in t:
            t = t.split("/")[-1]
        return t
    return "Unknown"


def validate_structured_data(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Finds and validates all JSON-LD and Microdata blocks on the page.
    Returns detected types, validation warnings, missing fields, and rich snippet eligibility.
    """
    raw_blocks: List[Any] = []
    parsed_items: List[Dict[str, Any]] = []
    validation_issues: List[Dict[str, Any]] = []
    types_found: List[str] = []
    rich_snippet_eligible: List[str] = []

    # 1. Parse JSON-LD scripts
    for script in soup.find_all("script", type="application/ld+json"):
        content = script.string
        if not content:
            continue
        try:
            data = json.loads(content.strip())
            if isinstance(data, list):
                raw_blocks.extend(data)
            elif isinstance(data, dict):
                if "@graph" in data and isinstance(data["@graph"], list):
                    raw_blocks.extend(data["@graph"])
                else:
                    raw_blocks.append(data)
        except Exception as e:
            validation_issues.append({
                "severity": "error",
                "schema_type": "JSON-LD Syntax",
                "message": f"Malformed JSON-LD script: {str(e)[:120]}",
                "fix": "Ensure JSON-LD script contains valid JSON syntax without trailing commas or unescaped characters."
            })

    # 2. Extract Microdata
    for item_scope in soup.find_all(attrs={"itemscope": True}):
        item_type = item_scope.get("itemtype", "")
        if item_type:
            clean_type = _normalize_type(item_type)
            types_found.append(clean_type)

    # 3. Analyze parsed items
    for item in raw_blocks:
        if not isinstance(item, dict):
            continue
        schema_type = _normalize_type(item.get("@type", "Unknown"))
        types_found.append(schema_type)

        item_summary = {
            "type": schema_type,
            "raw": item,
            "valid": True,
            "errors": [],
            "warnings": [],
            "recommendations": []
        }

        # Check Schema Rules
        rule = SCHEMA_RULES.get(schema_type)
        if rule:
            # Check required
            for req in rule.get("required", []):
                val = item.get(req)
                if val is None or (isinstance(val, str) and not val.strip()):
                    msg = f"{schema_type} is missing required field: '{req}'."
                    item_summary["errors"].append(msg)
                    item_summary["valid"] = False
                    validation_issues.append({
                        "severity": "error",
                        "schema_type": schema_type,
                        "field": req,
                        "message": msg,
                        "fix": f"Add the '{req}' property to the {schema_type} structured data markup."
                    })

            # Check recommended
            for rec in rule.get("recommended", []):
                val = item.get(rec)
                if val is None:
                    msg = f"{schema_type} is missing recommended field: '{rec}'."
                    item_summary["warnings"].append(msg)
                    validation_issues.append({
                        "severity": "warning",
                        "schema_type": schema_type,
                        "field": rec,
                        "message": msg,
                        "fix": f"Provide the '{rec}' property in {schema_type} to qualify for enhanced Google search rich results."
                    })

            # Special checks for Product
            if schema_type == "Product":
                offers = item.get("offers")
                if not offers:
                    msg = "Product schema has no 'offers' defined (price and availability will not display in Google Shopping/Search)."
                    validation_issues.append({
                        "severity": "error",
                        "schema_type": "Product",
                        "field": "offers",
                        "message": msg,
                        "fix": "Embed an Offer schema inside Product.offers including price, priceCurrency, and availability."
                    })
                else:
                    offer_dict = offers[0] if isinstance(offers, list) and offers else offers
                    if isinstance(offer_dict, dict):
                        if not offer_dict.get("price"):
                            validation_issues.append({
                                "severity": "error",
                                "schema_type": "Product/Offer",
                                "field": "price",
                                "message": "Product offer is missing 'price'. Rich product snippets will be rejected by search engines.",
                                "fix": "Set a valid numeric string for offer price (e.g., '29.99')."
                            })
                        if not offer_dict.get("priceCurrency"):
                            validation_issues.append({
                                "severity": "error",
                                "schema_type": "Product/Offer",
                                "field": "priceCurrency",
                                "message": "Product offer is missing ISO 4217 currency code (e.g. 'USD', 'EUR').",
                                "fix": "Add 'priceCurrency': 'USD' to the Offer markup."
                            })
                        if not offer_dict.get("availability"):
                            validation_issues.append({
                                "severity": "warning",
                                "schema_type": "Product/Offer",
                                "field": "availability",
                                "message": "Offer is missing availability status (e.g., InStock, OutOfStock).",
                                "fix": "Add 'availability': 'https://schema.org/InStock'."
                            })

                if item.get("aggregateRating"):
                    agg = item.get("aggregateRating")
                    if isinstance(agg, dict) and not agg.get("ratingValue"):
                        validation_issues.append({
                            "severity": "warning",
                            "schema_type": "AggregateRating",
                            "field": "ratingValue",
                            "message": "AggregateRating missing 'ratingValue'.",
                            "fix": "Provide numerical ratingValue (e.g. 4.5)."
                        })
                else:
                    item_summary["recommendations"].append("Add AggregateRating schema to earn review stars in SERPs.")

                # Rich snippet evaluation
                if item_summary["valid"] and item.get("offers"):
                    rich_snippet_eligible.append("Product Rich Result (Price & Availability)")
                if item.get("aggregateRating"):
                    rich_snippet_eligible.append("Review Stars Rich Snippet")

            if schema_type == "BreadcrumbList":
                items = item.get("itemListElement", [])
                if isinstance(items, list) and len(items) > 0:
                    rich_snippet_eligible.append("Breadcrumb Trail SERP Feature")

            if schema_type == "FAQPage":
                rich_snippet_eligible.append("FAQ Accordion SERP Feature")

        parsed_items.append(item_summary)

    unique_types = sorted(list(set(types_found)))
    return {
        "has_schema": len(unique_types) > 0,
        "schema_types": unique_types,
        "items_count": len(parsed_items),
        "parsed_items": parsed_items,
        "issues": validation_issues,
        "rich_snippet_eligible": list(set(rich_snippet_eligible)),
        "is_valid": len([i for i in validation_issues if i["severity"] == "error"]) == 0
    }

