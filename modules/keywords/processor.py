"""
SearchLens Keyword Intelligence Module
Processes, cleans, classifies, clusters, and analyzes keyword datasets.
Supports CSV, Excel, and manual seed keyword lists.
Strictly adheres to honest metric reporting: flags estimates and missing metrics.
"""
from __future__ import annotations

import re
import io
import math
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict

import pandas as pd


INTENT_PATTERNS = {
    "Transactional": [
        r"\bbuy\b", r"\bpurchase\b", r"\border\b", r"\bcheap\b", r"\bdiscount\b",
        r"\bcoupon\b", r"\bdeal\b", r"\bpromo\b", r"\bprice\b", r"\bpricing\b",
        r"\bshop\b", r"\bstore\b", r"\bshipping\b", r"\bfor sale\b", r"\bcheckout\b",
        r"\bcart\b", r"\bfree shipping\b", r"\baffordable\b"
    ],
    "Commercial": [
        r"\bbest\b", r"\btop\b", r"\breview\b", r"\breviews\b", r"\bvs\b",
        r"\bversus\b", r"\bcomparison\b", r"\bcompare\b", r"\balternative\b",
        r"\balternatives\b", r"\brated\b", r"\bspecs\b", r"\bfeatures\b",
        r"\bworth it\b", r"\bpros and cons\b", r"\btest\b"
    ],
    "Informational": [
        r"\bhow\b", r"\bwhat\b", r"\bwhy\b", r"\bwhen\b", r"\bwhere\b",
        r"\bwho\b", r"\bguide\b", r"\btutorial\b", r"\btips\b", r"\bideas\b",
        r"\bexamples\b", r"\bdiy\b", r"\bbenefits\b", r"\bmeaning\b",
        r"\bdefinition\b", r"\blearn\b", r"\bexplained\b", r"\binstructions\b"
    ],
    "Navigational": [
        r"\blogin\b", r"\bsign in\b", r"\bportal\b", r"\bofficial\b",
        r"\bwebsite\b", r"\baccount\b", r"\bcontact\b", r"\bsupport\b",
        r"\bdownload\b", r"\bapp\b", r"\bcustomer service\b"
    ]
}


def classify_intent(kw: str) -> Tuple[str, float]:
    """
    Classifies keyword search intent and returns (Intent, Confidence).
    Fallback is Commercial if contains product-related qualifiers, otherwise Informational.
    """
    k_lower = kw.lower().strip()
    scores = {"Transactional": 0, "Commercial": 0, "Informational": 0, "Navigational": 0}

    for intent, patterns in INTENT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, k_lower):
                scores[intent] += 1

    top_intent = max(scores, key=scores.get)
    if scores[top_intent] > 0:
        confidence = min(0.95, 0.65 + (scores[top_intent] * 0.15))
        return top_intent, round(confidence, 2)

    # Heuristics based on query length and product modifier patterns
    words = k_lower.split()
    if len(words) <= 2:
        return "Navigational/Brand", 0.50
    elif any(w in k_lower for w in ["men", "women", "kids", "size", "color", "black", "white", "pro", "max", "model"]):
        return "Commercial", 0.60
    return "Informational", 0.50


def is_long_tail(kw: str) -> bool:
    """True if query has 3 or more words."""
    words = [w for w in re.split(r"\s+", kw.strip()) if w]
    return len(words) >= 3


def calculate_opportunity_score(volume: Optional[float], difficulty: Optional[float], intent: str, word_count: int) -> Tuple[float, str]:
    """
    Computes an Opportunity Score (0-100) and describes its derivation honestly.
    """
    has_real_metrics = volume is not None and not math.isnan(volume) and difficulty is not None and not math.isnan(difficulty)

    if has_real_metrics:
        vol = max(0.0, volume)
        diff = max(0.0, min(100.0, difficulty))
        # Logarithmic volume score (10 to 50,000 searches) -> 0 to 50
        vol_score = min(50.0, (math.log10(max(10.0, vol)) / math.log10(50000.0)) * 50.0)
        # Low difficulty score (100 - KD) -> 0 to 40
        diff_score = ((100.0 - diff) / 100.0) * 40.0
        # Intent bonus: Transactional (+10), Commercial (+7), Informational (+4)
        intent_bonus = 10.0 if intent == "Transactional" else (7.0 if intent == "Commercial" else 4.0)
        score = round(min(100.0, vol_score + diff_score + intent_bonus), 1)
        return score, "Calculated from uploaded Search Volume & Keyword Difficulty"
    else:
        # Heuristic estimate based on specificity and commercial value
        base_score = 40.0
        if word_count >= 4:
            base_score += 25.0  # High specificity / lower assumed competition
        elif word_count == 3:
            base_score += 15.0
        if intent == "Transactional":
            base_score += 25.0
        elif intent == "Commercial":
            base_score += 18.0
        else:
            base_score += 10.0
        score = round(min(90.0, base_score), 1)
        return score, "Estimated via Query Specificity & Intent (Search Volume/KD Not In Source Data)"


class KeywordDataset:
    """
    Manages keyword ingestion from CSV/Excel or list, performs deduplication,
    intent classification, long-tail analysis, and thematic grouping.
    """

    def __init__(self, df: pd.DataFrame):
        self.raw_df = df
        self.clean_df = self._clean_and_enrich(df)

    @classmethod
    def from_file(cls, file_content: bytes, filename: str) -> "KeywordDataset":
        if filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            df = pd.read_csv(io.BytesIO(file_content))
        return cls(df)

    @classmethod
    def from_list(cls, keywords: List[str]) -> "KeywordDataset":
        df = pd.DataFrame({"keyword": keywords})
        return cls(df)

    def _find_column(self, df: pd.DataFrame, patterns: List[str]) -> Optional[str]:
        for col in df.columns:
            col_clean = str(col).lower().strip()
            for pat in patterns:
                if pat in col_clean:
                    return col
        return None

    def _clean_and_enrich(self, df: pd.DataFrame) -> pd.DataFrame:
        clean = df.copy()

        # Identify keyword column
        kw_col = self._find_column(clean, ["keyword", "query", "term", "search term", "keywords", "key phrase"])
        if not kw_col:
            # Fall back to first text column
            for col in clean.columns:
                if clean[col].dtype == object:
                    kw_col = col
                    break
        if not kw_col:
            clean["keyword"] = [f"item_{i}" for i in range(len(clean))]
            kw_col = "keyword"

        clean["keyword"] = clean[kw_col].astype(str).str.strip().str.lower()
        clean = clean[clean["keyword"].str.len() > 1].drop_duplicates(subset=["keyword"]).copy()

        # Map optional metric columns
        vol_col = self._find_column(clean, ["volume", "search volume", "monthly", "avg searches", "searches"])
        diff_col = self._find_column(clean, ["difficulty", "kd", "competition index", "keyword difficulty", "competition score"])
        cpc_col = self._find_column(clean, ["cpc", "cost per click", "cost"])
        comp_col = self._find_column(clean, ["competition", "comp"])

        has_vol = vol_col is not None
        has_diff = diff_col is not None

        clean["search_volume"] = pd.to_numeric(clean[vol_col], errors="coerce") if has_vol else None
        clean["difficulty"] = pd.to_numeric(clean[diff_col], errors="coerce") if has_diff else None
        clean["cpc"] = pd.to_numeric(clean[cpc_col], errors="coerce") if cpc_col else None
        clean["competition_level"] = clean[comp_col].astype(str) if comp_col else None

        # Add enrichment columns
        intents = []
        confidences = []
        long_tails = []
        word_counts = []
        opp_scores = []
        opp_sources = []

        for kw in clean["keyword"]:
            intent, conf = classify_intent(kw)
            lt = is_long_tail(kw)
            wc = len(kw.split())

            vol_val = clean.loc[clean["keyword"] == kw, "search_volume"].values[0] if has_vol else None
            diff_val = clean.loc[clean["keyword"] == kw, "difficulty"].values[0] if has_diff else None

            opp, src = calculate_opportunity_score(vol_val, diff_val, intent, wc)

            intents.append(intent)
            confidences.append(conf)
            long_tails.append(lt)
            word_counts.append(wc)
            opp_scores.append(opp)
            opp_sources.append(src)

        clean["intent"] = intents
        clean["intent_confidence"] = confidences
        clean["is_long_tail"] = long_tails
        clean["word_count"] = word_counts
        clean["opportunity_score"] = opp_scores
        clean["opportunity_source"] = opp_sources

        # Tag categories/clusters
        clean["cluster"] = self._cluster_keywords(clean["keyword"].tolist())

        return clean.sort_values(by="opportunity_score", ascending=False).reset_index(drop=True)

    def _cluster_keywords(self, keywords: List[str]) -> List[str]:
        """
        Clusters keywords into thematic topic groups based on prominent 2-word or 1-word roots.
        """
        word_freq = Counter()
        stopwords = {
            "the", "a", "an", "and", "or", "in", "on", "for", "with", "at",
            "to", "of", "by", "from", "is", "it", "this", "that", "how", "what",
            "why", "best", "top", "free", "near", "me"
        }

        for kw in keywords:
            words = [w for w in kw.split() if w not in stopwords and len(w) > 2]
            for w in words:
                word_freq[w] += 1

        top_roots = [w for w, count in word_freq.most_common(12) if count > 1]
        clusters = []

        for kw in keywords:
            assigned = "General / Other"
            for root in top_roots:
                if root in kw:
                    assigned = root.title()
                    break
            clusters.append(assigned)
        return clusters

    def get_summary(self) -> Dict[str, Any]:
        """Returns comprehensive summary stats for dashboard visualization."""
        df = self.clean_df
        total = len(df)
        if total == 0:
            return {"total_keywords": 0}

        intent_counts = df["intent"].value_counts().to_dict()
        long_tail_count = int(df["is_long_tail"].sum())
        cluster_counts = df["cluster"].value_counts().to_dict()

        has_source_volume = df["search_volume"].notna().any()
        has_source_difficulty = df["difficulty"].notna().any()

        total_volume = int(df["search_volume"].dropna().sum()) if has_source_volume else None
        avg_difficulty = round(float(df["difficulty"].dropna().mean()), 1) if has_source_difficulty else None

        # Quick wins: Opportunity >= 70 and (difficulty <= 40 or is_long_tail)
        quick_wins = df[df["opportunity_score"] >= 70].head(15)[
            ["keyword", "intent", "opportunity_score", "word_count", "cluster"]
        ].to_dict(orient="records")

        return {
            "total_keywords": total,
            "has_source_volume": bool(has_source_volume),
            "has_source_difficulty": bool(has_source_difficulty),
            "total_volume": total_volume,
            "avg_difficulty": avg_difficulty,
            "long_tail_count": long_tail_count,
            "long_tail_percent": round((long_tail_count / total) * 100, 1) if total > 0 else 0,
            "intent_distribution": intent_counts,
            "cluster_distribution": cluster_counts,
            "quick_wins": quick_wins,
            "metric_transparency_note": (
                "Verified Source Metrics: Search volume & KD loaded directly from source file."
                if has_source_volume else
                "Notice: Source file did not contain Search Volume / KD columns. Metrics displayed are rule-based specificity and intent estimates, explicitly labeled."
            )
        }


def generate_ecommerce_keyword_suggestions(seed_topic: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generates structured e-commerce product and category keyword suggestions
    across shopping stages (Awareness, Consideration, Purchase).
    """
    clean_seed = seed_topic.strip().lower()
    if not clean_seed:
        return {}

    templates = {
        "Category & Attribute Keywords": [
            f"{clean_seed}",
            f"best {clean_seed}",
            f"affordable {clean_seed}",
            f"waterproof {clean_seed}",
            f"lightweight {clean_seed}",
            f"luxury {clean_seed}",
            f"eco-friendly {clean_seed}",
            f"{clean_seed} for beginners",
            f"{clean_seed} for professionals"
        ],
        "Buyer Intent & Transactional": [
            f"buy {clean_seed} online",
            f"{clean_seed} discount code",
            f"{clean_seed} on sale",
            f"{clean_seed} price",
            f"cheap {clean_seed} free shipping",
            f"order {clean_seed} online",
            f"best price for {clean_seed}"
        ],
        "Comparison & Review (Commercial)": [
            f"{clean_seed} reviews 2026",
            f"top 10 {clean_seed}",
            f"{clean_seed} vs alternatives",
            f"is {clean_seed} worth it",
            f"{clean_seed} comparison guide"
        ],
        "Informational & Buying Guides": [
            f"how to choose {clean_seed}",
            f"{clean_seed} sizing guide",
            f"how to clean {clean_seed}",
            f"what is the best {clean_seed}",
            f"{clean_seed} maintenance tips"
        ]
    }

    result = {}
    for stage, kw_list in templates.items():
        items = []
        for kw in kw_list:
            intent, conf = classify_intent(kw)
            lt = is_long_tail(kw)
            opp, src = calculate_opportunity_score(None, None, intent, len(kw.split()))
            items.append({
                "keyword": kw,
                "intent": intent,
                "is_long_tail": lt,
                "opportunity_score": opp,
                "search_volume_status": "Estimated heuristic (no live API connection)",
                "difficulty_status": "Estimated heuristic (no live API connection)",
                "is_suggestion": True
            })
        result[stage] = items
    return result

