"""
SearchLens Database Module (SQLite)
Manages persistent relational storage for projects, crawled pages, audit runs,
SEO issues, keywords, GEO research logs, and historical performance tracking.
Includes specialized analytical SQL queries and export functions.
"""
from __future__ import annotations

import os
import json
import sqlite3
import csv
import io
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import pandas as pd


DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "searchlens.db")


class SearchLensDB:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        self._init_tables()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        with self.get_connection() as conn:
            cur = conn.cursor()

            # 1. Projects Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                domain TEXT NOT NULL,
                created_at TEXT NOT NULL,
                notes TEXT
            );
            """)

            # 2. Crawled Pages Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS crawled_pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                status_code INTEGER,
                title TEXT,
                meta_description TEXT,
                h1 TEXT,
                word_count INTEGER,
                response_time REAL,
                canonical TEXT,
                robots_meta TEXT,
                is_indexable INTEGER DEFAULT 1,
                schema_types TEXT,
                crawled_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            """)

            # 3. Audit Results Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                audit_type TEXT NOT NULL,
                target_url TEXT NOT NULL,
                overall_score REAL,
                tech_score REAL,
                onpage_score REAL,
                content_score REAL,
                ecom_score REAL,
                summary_json TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            """)

            # 4. SEO Issues Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS seo_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audit_id INTEGER,
                project_id INTEGER NOT NULL,
                url TEXT NOT NULL,
                code TEXT NOT NULL,
                title TEXT NOT NULL,
                severity TEXT NOT NULL,
                category TEXT NOT NULL,
                explanation TEXT NOT NULL,
                recommended_fix TEXT NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (audit_id) REFERENCES audit_results(id) ON DELETE CASCADE,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            """)

            # 5. Keywords Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                search_volume REAL,
                difficulty REAL,
                cpc REAL,
                intent TEXT NOT NULL,
                cluster TEXT,
                is_long_tail INTEGER NOT NULL,
                opportunity_score REAL NOT NULL,
                source TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            """)

            # 6. GEO Research Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS geo_research (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                query_prompt TEXT NOT NULL,
                engine TEXT NOT NULL,
                brand_name TEXT NOT NULL,
                target_domain TEXT,
                ai_response TEXT NOT NULL,
                brand_mentioned INTEGER NOT NULL,
                mention_rank INTEGER,
                sentiment TEXT NOT NULL,
                geo_score REAL NOT NULL,
                cited_urls_json TEXT,
                competitors_json TEXT,
                researched_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            """)

            # 7. Audit History Metrics Table
            cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                notes TEXT,
                recorded_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            """)

            conn.commit()

            # Seed default project if empty
            cur.execute("SELECT COUNT(*) FROM projects")
            if cur.fetchone()[0] == 0:
                now_str = datetime.now().isoformat()
                cur.execute(
                    "INSERT INTO projects (name, domain, created_at, notes) VALUES (?, ?, ?, ?)",
                    ("Demo E-Commerce Store", "sample-store.searchlens.internal", now_str, "Default portfolio sample project.")
                )
                conn.commit()

    # --- Project Management ---
    def get_or_create_project(self, name: str, domain: str, notes: str = "") -> int:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM projects WHERE name = ?", (name.strip(),))
            row = cur.fetchone()
            if row:
                return row["id"]
            now_str = datetime.now().isoformat()
            cur.execute(
                "INSERT INTO projects (name, domain, created_at, notes) VALUES (?, ?, ?, ?)",
                (name.strip(), domain.strip(), now_str, notes)
            )
            conn.commit()
            return cur.lastrowid

    def list_projects(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, name, domain, created_at, notes FROM projects ORDER BY id ASC")
            return [dict(r) for r in cur.fetchall()]

    # --- Save Audit Operations ---
    def save_audit(
        self,
        project_id: int,
        target_url: str,
        audit_type: str,
        scores: Dict[str, float],
        issues: List[Dict[str, Any]],
        summary: Optional[Dict[str, Any]] = None
    ) -> int:
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO audit_results (
                project_id, audit_type, target_url, overall_score,
                tech_score, onpage_score, content_score, ecom_score,
                summary_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                audit_type,
                target_url,
                scores.get("overall_score"),
                scores.get("tech_score"),
                scores.get("onpage_score"),
                scores.get("content_score"),
                scores.get("ecom_score"),
                json.dumps(summary or {}, default=str),
                now_str
            ))
            audit_id = cur.lastrowid

            # Save issues
            for iss in issues:
                cur.execute("""
                INSERT INTO seo_issues (
                    audit_id, project_id, url, code, title, severity, category,
                    explanation, recommended_fix, details, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    audit_id,
                    project_id,
                    iss.get("url", target_url),
                    iss.get("code", "SEO_ISSUE"),
                    iss.get("title", "SEO Issue"),
                    iss.get("severity", "warning"),
                    iss.get("category", "technical"),
                    iss.get("explanation", iss.get("details", "")),
                    iss.get("recommended_fix", iss.get("details", "")),
                    iss.get("details", ""),
                    now_str
                ))

            # Record in audit history
            if scores.get("overall_score") is not None:
                cur.execute("""
                INSERT INTO audit_history (project_id, metric_name, metric_value, notes, recorded_at)
                VALUES (?, ?, ?, ?, ?)
                """, (project_id, "overall_score", scores.get("overall_score"), f"Audit run for {target_url}", now_str))

            conn.commit()
            return audit_id

    # --- Save Crawled Pages ---
    def save_crawled_page(self, project_id: int, page_data: Dict[str, Any]):
        now_str = datetime.now().isoformat()
        attrs = page_data.get("seo_attributes", {})
        tech = attrs.get("TechnicalSEOAnalyzer", {})
        onp = attrs.get("OnPageAnalyzer", {})

        is_idx = 0 if tech.get("hasMetaNoindex") or "noindex" in (tech.get("xRobotsTag") or "").lower() else 1
        schemas = tech.get("structuredDataValidation", {}).get("schema_types", [])

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO crawled_pages (
                project_id, url, status_code, title, meta_description, h1,
                word_count, response_time, canonical, robots_meta, is_indexable,
                schema_types, crawled_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                page_data.get("url"),
                tech.get("httpStatusCode"),
                onp.get("title"),
                onp.get("metaDescription"),
                (onp.get("h1Tags") or [None])[0] if onp.get("h1Tags") else None,
                onp.get("wordsCount"),
                (tech.get("siteLoadingSpeedTest") or {}).get("ttfb_seconds"),
                tech.get("canonicalUrl"),
                tech.get("metaRobots"),
                is_idx,
                ", ".join(schemas) if schemas else None,
                now_str
            ))
            conn.commit()

    # --- Save Keywords ---
    def save_keywords(self, project_id: int, df: pd.DataFrame, source_label: str = "Upload"):
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cur = conn.cursor()
            for _, row in df.iterrows():
                cur.execute("""
                INSERT INTO keywords (
                    project_id, keyword, search_volume, difficulty, cpc,
                    intent, cluster, is_long_tail, opportunity_score, source, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    project_id,
                    str(row.get("keyword")),
                    row.get("search_volume") if pd.notna(row.get("search_volume")) else None,
                    row.get("difficulty") if pd.notna(row.get("difficulty")) else None,
                    row.get("cpc") if pd.notna(row.get("cpc")) else None,
                    str(row.get("intent", "Informational")),
                    str(row.get("cluster", "General")),
                    1 if row.get("is_long_tail") else 0,
                    float(row.get("opportunity_score", 50.0)),
                    source_label,
                    now_str
                ))
            conn.commit()

    # --- Save GEO Research ---
    def save_geo_record(self, project_id: int, geo_data: Dict[str, Any]) -> int:
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO geo_research (
                project_id, query_prompt, engine, brand_name, target_domain,
                ai_response, brand_mentioned, mention_rank, sentiment,
                geo_score, cited_urls_json, competitors_json, researched_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project_id,
                geo_data.get("query_prompt"),
                geo_data.get("engine"),
                geo_data.get("brand_name"),
                geo_data.get("target_domain"),
                geo_data.get("ai_response"),
                1 if geo_data.get("is_mentioned") else 0,
                geo_data.get("position_rank"),
                geo_data.get("sentiment"),
                geo_data.get("geo_visibility_score", 0),
                json.dumps(geo_data.get("citations", []), default=str),
                json.dumps(geo_data.get("competitors_mentioned", []), default=str),
                now_str
            ))
            conn.commit()
            return cur.lastrowid

    # --- Specialized SQL Analytics Queries ---
    def get_most_common_issues(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        sql = """
        SELECT code, title, severity, category, COUNT(*) as issue_count
        FROM seo_issues
        """
        params = []
        if project_id:
            sql += " WHERE project_id = ? "
            params.append(project_id)
        sql += " GROUP BY code, title, severity, category ORDER BY issue_count DESC LIMIT 15;"

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def get_most_affected_pages(self, project_id: Optional[int] = None, limit: int = 10) -> List[Dict[str, Any]]:
        sql = """
        SELECT url,
               COUNT(*) as total_issues,
               SUM(CASE WHEN severity = 'error' THEN 1 ELSE 0 END) as errors,
               SUM(CASE WHEN severity = 'warning' THEN 1 ELSE 0 END) as warnings,
               SUM(CASE WHEN severity = 'notice' THEN 1 ELSE 0 END) as notices
        FROM seo_issues
        """
        params = []
        if project_id:
            sql += " WHERE project_id = ? "
            params.append(project_id)
        sql += f" GROUP BY url ORDER BY errors DESC, total_issues DESC LIMIT {int(limit)};"

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def get_audit_comparison(self, project_id: int) -> Dict[str, Any]:
        """Compares the last two audits for the given project."""
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
            SELECT id, target_url, overall_score, tech_score, onpage_score, content_score, created_at
            FROM audit_results
            WHERE project_id = ?
            ORDER BY id DESC LIMIT 2;
            """, (project_id,))
            rows = [dict(r) for r in cur.fetchall()]

            if not rows:
                return {"has_comparison": False, "message": "No audit records found for this project."}
            if len(rows) == 1:
                return {
                    "has_comparison": True,
                    "latest": rows[0],
                    "previous": None,
                    "delta": 0,
                    "message": "Only 1 audit record on file; run another audit to see progress comparison."
                }

            latest = rows[0]
            prev = rows[1]
            delta = round((latest.get("overall_score") or 0) - (prev.get("overall_score") or 0), 1)

            return {
                "has_comparison": True,
                "latest": latest,
                "previous": prev,
                "overall_score_delta": delta,
                "score_improved": delta > 0,
                "score_regressed": delta < 0
            }

    def get_top_keyword_opportunities(self, project_id: Optional[int] = None, limit: int = 20) -> List[Dict[str, Any]]:
        sql = """
        SELECT keyword, search_volume, difficulty, intent, cluster, is_long_tail, opportunity_score, source
        FROM keywords
        """
        params = []
        if project_id:
            sql += " WHERE project_id = ? "
            params.append(project_id)
        sql += f" ORDER BY opportunity_score DESC LIMIT {int(limit)};"

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    def get_geo_engine_comparison(self, project_id: Optional[int] = None) -> List[Dict[str, Any]]:
        sql = """
        SELECT engine,
               COUNT(*) as total_queries,
               SUM(brand_mentioned) as mentions,
               ROUND(AVG(brand_mentioned) * 100.0, 1) as mention_rate_pct,
               ROUND(AVG(geo_score), 1) as avg_geo_score
        FROM geo_research
        """
        params = []
        if project_id:
            sql += " WHERE project_id = ? "
            params.append(project_id)
        sql += " GROUP BY engine ORDER BY avg_geo_score DESC;"

        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    # --- Generic Export to CSV & JSON ---
    def export_table_df(self, table_name: str, project_id: Optional[int] = None) -> pd.DataFrame:
        valid_tables = ["projects", "crawled_pages", "audit_results", "seo_issues", "keywords", "geo_research", "audit_history"]
        if table_name not in valid_tables:
            raise ValueError(f"Invalid table name {table_name}")

        sql = f"SELECT * FROM {table_name}"
        params = []
        if project_id and table_name != "projects":
            sql += " WHERE project_id = ?"
            params.append(project_id)

        with self.get_connection() as conn:
            return pd.read_sql_query(sql, conn, params=params)

    def export_table_csv(self, table_name: str, project_id: Optional[int] = None) -> str:
        df = self.export_table_df(table_name, project_id)
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        return buf.getvalue()

    def export_table_json(self, table_name: str, project_id: Optional[int] = None) -> str:
        df = self.export_table_df(table_name, project_id)
        return df.to_json(orient="records", indent=2)
