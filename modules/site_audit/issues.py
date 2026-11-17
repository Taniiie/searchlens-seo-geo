from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional


@dataclass
class Issue:
    url: str
    code: str
    title: str
    severity: str  # error | warning | notice
    category: str  # technical | on_page | content | performance | international | security | links | ai | ecommerce
    details: str
    explanation: str = ""
    recommended_fix: str = ""

    def __post_init__(self):
        if not self.explanation:
            self.explanation = self.details
        if not self.recommended_fix:
            self.recommended_fix = self.details

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _sev(cond: bool, when_true: str, when_false: str = "") -> str:
    return when_true if cond else when_false


def _status_bucket(sc: Optional[int]) -> Optional[str]:
    if sc is None:
        return None
    if sc == 403:
        return '403'
    if 400 <= sc < 500:
        return '4xx'
    if 500 <= sc < 600:
        return '5xx'
    if 300 <= sc < 400:
        return '3xx'
    if sc == 200:
        return '200'
    return str(sc)


def derive_issues(url: str, page_attrs: Dict[str, Any]) -> List[Issue]:
    issues: List[Issue] = []

    onpage = page_attrs.get('OnPageAnalyzer', {})
    tech = page_attrs.get('TechnicalSEOAnalyzer', {})
    content = page_attrs.get('ContentAnalyzer', {})
    ecom = page_attrs.get('EcommerceAnalyzer', {})

    # 1. HTTP Status Codes
    sc = tech.get('httpStatusCode')
    bucket = _status_bucket(sc)
    if bucket == '404' or sc == 404:
        issues.append(Issue(
            url=url, code='HTTP_404', title='Page Not Found (404)',
            severity='error', category='technical',
            details='Return 200 OK or 301 redirect to relevant page',
            explanation='The requested URL returned an HTTP 404 Not Found error. Search engines will de-index this URL and users encounter a broken page experience.',
            recommended_fix='If the page was permanently moved, implement a 301 permanent redirect to the most relevant equivalent page. If deleted, return a 410 Gone or restore content.'
        ))
    elif bucket == '403' or sc == 403:
        issues.append(Issue(
            url=url, code='HTTP_403', title='Access Forbidden (403)',
            severity='error', category='technical',
            details='Check server auth and access control headers',
            explanation='Search engine crawlers were denied access with an HTTP 403 Forbidden response, preventing discovery and indexation.',
            recommended_fix='Verify server firewall rules (Cloudflare, AWS WAF) and user-agent allowlists to ensure search bot crawlers are not inadvertently blocked.'
        ))
    elif bucket == '5xx' or (sc and 500 <= sc < 600):
        issues.append(Issue(
            url=url, code='HTTP_5XX', title=f'Server Error ({sc})',
            severity='error', category='technical',
            details='Investigate backend server error and database stability',
            explanation=f'The web server responded with HTTP {sc} server error. Prolonged 5xx errors cause search engines to slow down crawl rate and drop rankings.',
            recommended_fix='Inspect server application error logs, database connections, and server resource limits (CPU/RAM). Resolve runtime exceptions.'
        ))
    elif bucket == '4xx' and sc not in (404, 403):
        issues.append(Issue(
            url=url, code='HTTP_4XX', title=f'Client Request Error ({sc})',
            severity='error', category='technical',
            details='Fix routing or URL syntax',
            explanation=f'The client request resulted in an HTTP {sc} error status code.',
            recommended_fix='Check routing configuration and verify request formatting.'
        ))

    # 2. Redirects
    if bucket == '3xx' or (sc and 300 <= sc < 400):
        rh = tech.get('redirectHistory') or []
        redirect_hops = [h for h in rh if (h.get('status_code') or 0) // 100 == 3]
        if len(redirect_hops) > 1:
            issues.append(Issue(
                url=url, code='REDIRECT_CHAIN', title=f'Redirect Chain Detected ({len(redirect_hops)} hops)',
                severity='warning', category='technical',
                details='Reduce to a single direct 301 redirect',
                explanation='The page undergoes multiple sequential redirect hops before reaching the destination. Chains waste crawl budget and increase latency.',
                recommended_fix='Update internal links and server rules to redirect directly from source URL to the final destination in a single 301 hop.'
            ))
        seen = set()
        for hop in rh:
            u2 = hop.get('url')
            if u2:
                if u2 in seen:
                    issues.append(Issue(
                        url=url, code='REDIRECT_LOOP', title='Redirect Loop Detected',
                        severity='error', category='technical',
                        details='Resolve circular redirection loop',
                        explanation='The URL points back to a URL already encountered in the redirect sequence, trapping users and bots in an infinite loop.',
                        recommended_fix='Break the circular redirect in your .htaccess, Nginx config, or CDN routing rules.'
                    ))
                    break
                seen.add(u2)
        if any(h.get('status_code') == 302 for h in rh) or sc == 302:
            issues.append(Issue(
                url=url, code='TEMP_REDIRECT_302', title='Temporary 302 Redirect Used',
                severity='notice', category='technical',
                details='Use 301 redirect if move is permanent',
                explanation='HTTP 302 indicates a temporary move. Search engines may take longer to pass link equity (PageRank) to the destination.',
                recommended_fix='Change HTTP 302 to HTTP 301 (Moved Permanently) unless this redirection is truly temporary (e.g. flash sales, maintenance).'
            ))

    if tech.get('hasMetaRefresh'):
        issues.append(Issue(
            url=url, code='META_REFRESH', title='Meta Refresh Redirect Present',
            severity='warning', category='technical',
            details='Replace meta refresh with server-side 301 redirect',
            explanation='Client-side meta refresh tags introduce visual delay, hurt Core Web Vitals, and are discouraged by Google Webmaster guidelines.',
            recommended_fix='Remove <meta http-equiv="refresh"> and configure an HTTP 301 redirect on the web server level.'
        ))

    # Scheme Downgrade
    rh = tech.get('redirectHistory') or []
    if rh:
        try:
            first = rh[0].get('url')
            last = rh[-1].get('url')
            if first and last and first.startswith('https://') and last.startswith('http://'):
                issues.append(Issue(
                    url=url, code='HTTPS_TO_HTTP', title='HTTPS Insecurely Redirects to HTTP',
                    severity='error', category='security',
                    details='Never downgrade HTTPS URLs to plain HTTP',
                    explanation='A secure HTTPS URL redirected to an insecure HTTP endpoint, risking user credential exposure and triggering browser security warnings.',
                    recommended_fix='Ensure all redirections terminate at secure HTTPS URLs and enforce HSTS.'
                ))
        except Exception:
            pass

    # 3. Robots.txt and Indexability
    if tech.get('robotsTxtDisallowsAllGeneral'):
        issues.append(Issue(
            url=url, code='ROBOTS_DISALLOW_ALL', title='Robots.txt Disallows All Crawlers',
            severity='error', category='technical',
            details='Remove Disallow: / from robots.txt for production site',
            explanation='Your robots.txt file contains "Disallow: /" under User-agent: *, preventing all compliant search engines from crawling the website.',
            recommended_fix='Update robots.txt to permit crawling of public pages. Keep staging disallow directives strictly isolated from production.'
        ))

    if not tech.get('hasSitemap'):
        issues.append(Issue(
            url=url, code='NO_SITEMAP', title='No XML Sitemap Detected',
            severity='warning', category='technical',
            details='Publish an XML sitemap and reference it in robots.txt',
            explanation='No XML sitemap was found at standard locations (/sitemap.xml) or referenced in robots.txt. Sitemaps accelerate new URL discovery.',
            recommended_fix='Generate an XML sitemap adhering to sitemaps.org standards and declare its location in robots.txt (e.g. Sitemap: https://domain.com/sitemap.xml).'
        ))

    # 4. Canonicalization
    if not tech.get('hasCanonicalTag'):
        issues.append(Issue(
            url=url, code='NO_CANONICAL', title='Missing Canonical Tag',
            severity='warning', category='technical',
            details='Add <link rel="canonical" href="..."> to the <head>',
            explanation='The page lacks a canonical link element. Without it, duplicate URL parameters, tracking UTM codes, or trailing slashes can split ranking signals.',
            recommended_fix='Add a self-referential canonical tag: <link rel="canonical" href="https://domain.com/path">'
        ))
    else:
        can_url = tech.get('canonicalUrl')
        if can_url and isinstance(can_url, str):
            try:
                from urllib.parse import urlparse
                cu = urlparse(can_url)
                pu = urlparse(url)
                if pu.scheme == 'http' and cu.scheme == 'https':
                    issues.append(Issue(
                        url=url, code='CANONICAL_HTTP_TO_HTTPS', title='Canonical Points from HTTP to HTTPS',
                        severity='notice', category='technical',
                        details='Migrate entire page to HTTPS directly',
                        explanation='The HTTP version points canonical to HTTPS, which is good practice, but the HTTP page should also 301 redirect to HTTPS.',
                        recommended_fix='Implement server-wide 301 redirection from HTTP to HTTPS.'
                    ))
                if pu.scheme == 'https' and cu.scheme == 'http':
                    issues.append(Issue(
                        url=url, code='CANONICAL_HTTPS_TO_HTTP', title='Secure Page Has Insecure HTTP Canonical',
                        severity='warning', category='technical',
                        details='Update canonical URL to secure HTTPS protocol',
                        explanation='An HTTPS page specifies an unencrypted HTTP canonical target. This confuses crawlers and can cause loss of SSL ranking boost.',
                        recommended_fix='Change the canonical URL href attribute to use https://.'
                    ))
            except Exception:
                pass

    # Canonical target probe
    cprobe = tech.get('canonicalTargetProbe') or {}
    csc = cprobe.get('status_code')
    if isinstance(csc, int):
        if 300 <= csc < 400:
            issues.append(Issue(
                url=url, code='CANONICAL_TO_REDIRECT', title='Canonical Target Is A Redirect',
                severity='warning', category='technical',
                details='Point canonical directly to final destination URL',
                explanation=f'The canonical URL href points to a URL that returns HTTP {csc} redirect instead of a 200 OK final destination.',
                recommended_fix='Update rel="canonical" to reference the final resolved URL directly, bypassing the intermediate redirect.'
            ))
        elif 400 <= csc < 500:
            issues.append(Issue(
                url=url, code='CANONICAL_TO_4XX', title=f'Canonical Target Returns 4xx Error ({csc})',
                severity='error', category='technical',
                details='Fix broken canonical URL target',
                explanation='The designated canonical page is returning a 4xx client error, leaving search engines with no valid canonical master page.',
                recommended_fix='Update the canonical href to point to an active, valid 200 OK URL.'
            ))
        elif 500 <= csc < 600:
            issues.append(Issue(
                url=url, code='CANONICAL_TO_5XX', title=f'Canonical Target Returns Server Error ({csc})',
                severity='error', category='technical',
                details='Investigate canonical target server failure',
                explanation='The canonical target page returned a 5xx server error during inspection.',
                recommended_fix='Fix the server error at the canonical target URL.'
            ))

    # 5. Meta Robots & Header Directives
    if tech.get('hasMetaNoindex'):
        issues.append(Issue(
            url=url, code='NOINDEX', title='Page Has Meta Noindex Directive',
            severity='warning', category='technical',
            details='Remove <meta name="robots" content="noindex"> if page should rank',
            explanation='A meta robots tag with "noindex" instructs search engines never to index this page in search results.',
            recommended_fix='If this page should generate organic search traffic, remove the "noindex" directive from the HTML <head>.'
        ))
    xrt = (tech.get('xRobotsTag') or '')
    if isinstance(xrt, str) and xrt:
        if 'noindex' in xrt.lower():
            issues.append(Issue(
                url=url, code='NOINDEX_HEADER', title='HTTP Header X-Robots-Tag Contains Noindex',
                severity='warning', category='technical',
                details='Remove X-Robots-Tag: noindex HTTP header if page should rank',
                explanation='The server returned an X-Robots-Tag response header containing "noindex", preventing search engine indexation.',
                recommended_fix='Modify your web server or CDN header settings to remove X-Robots-Tag: noindex for public indexable pages.'
            ))
        if 'nofollow' in xrt.lower():
            issues.append(Issue(
                url=url, code='NOFOLLOW_HEADER', title='HTTP Header X-Robots-Tag Contains Nofollow',
                severity='notice', category='technical',
                details='Review X-Robots-Tag header',
                explanation='The HTTP header specifies "nofollow", preventing search bots from discovering or passing PageRank to outbound links on this page.',
                recommended_fix='Remove "nofollow" from header directives unless intentionally confining bot link discovery.'
            ))
    if tech.get('hasMetaNofollowDirective'):
        issues.append(Issue(
            url=url, code='NOFOLLOW_PAGE', title='Page Meta Robots Contains Nofollow',
            severity='notice', category='technical',
            details='Ensure nofollow on entire page is intentional',
            explanation='The meta robots tag specifies "nofollow", preventing search engines from crawling links found on this page.',
            recommended_fix='Remove the "nofollow" directive from meta robots unless you want search bots to ignore all page links.'
        ))

    # 6. Viewport & Mobile Usability
    if not tech.get('viewport'):
        issues.append(Issue(
            url=url, code='NO_VIEWPORT', title='Missing Mobile Viewport Meta Tag',
            severity='warning', category='performance',
            details='Add <meta name="viewport" content="width=device-width, initial-scale=1">',
            explanation='The page lacks a mobile viewport meta tag, causing mobile devices to render the page at desktop width with tiny unreadable text.',
            recommended_fix='Insert <meta name="viewport" content="width=device-width, initial-scale=1.0"> in the HTML <head>.'
        ))

    # 7. Security & SSL
    if tech.get('hasMixedContent'):
        issues.append(Issue(
            url=url, code='MIXED_CONTENT', title='Mixed Content Detected (Insecure Assets on HTTPS)',
            severity='error', category='security',
            details='Serve all scripts, stylesheets, and images over HTTPS',
            explanation='The HTTPS page loads insecure resources (HTTP scripts, styles, or images). Modern browsers block passive/active mixed content.',
            recommended_fix='Update all resource URLs in HTML source and CSS to use relative protocols or explicit https:// schemes.'
        ))
    if tech.get('hasHttps') is False:
        issues.append(Issue(
            url=url, code='NO_HTTPS', title='Page Served Over Unencrypted HTTP',
            severity='warning', category='security',
            details='Install SSL/TLS certificate and force HTTPS',
            explanation='The page is served over unencrypted HTTP. Google uses HTTPS as a ranking signal, and browsers flag HTTP sites as "Not Secure".',
            recommended_fix='Provision a free TLS certificate (e.g. Let\'s Encrypt) and enforce automatic HTTP-to-HTTPS 301 redirection.'
        ))

    # 8. Performance (TTFB)
    ttfb = (tech.get('siteLoadingSpeedTest') or {}).get('ttfb_seconds')
    if isinstance(ttfb, (int, float)) and ttfb is not None:
        if ttfb >= 1.5:
            issues.append(Issue(
                url=url, code='SLOW_TTFB', title=f'Slow Time To First Byte ({ttfb}s)',
                severity='warning', category='performance',
                details='Optimize backend queries, enable edge caching, or upgrade hosting',
                explanation=f'TTFB was measured at {ttfb}s, which exceeds Google\'s recommended threshold (< 0.8s). Slow server response slows down indexing and hurts Core Web Vitals.',
                recommended_fix='Enable Redis/memcached query caching, optimize database queries, deploy a CDN (Cloudflare/Fastly), or upgrade server compute.'
            ))
        elif ttfb >= 1.0:
            issues.append(Issue(
                url=url, code='MODERATE_TTFB', title=f'Elevated Time To First Byte ({ttfb}s)',
                severity='notice', category='performance',
                details='Consider page caching to bring TTFB under 0.8s',
                explanation=f'TTFB was {ttfb}s, slightly above optimal performance standards.',
                recommended_fix='Implement edge caching on static/dynamic assets and optimize backend processing.'
            ))

    # 9. On-Page Titles & Descriptions
    if not onpage.get('isTitle'):
        issues.append(Issue(
            url=url, code='MISSING_TITLE', title='Missing Page Title Tag',
            severity='error', category='on_page',
            details='Add a unique, descriptive <title> tag (50-60 chars)',
            explanation='The HTML <head> lacks a <title> tag. Search engines rely on titles as the primary headline in search engine result pages (SERPs).',
            recommended_fix='Add a concise, keyword-optimized title tag: <title>Primary Keyword - Benefit | Brand</title>.'
        ))
    else:
        title_len = onpage.get('titleLength', 0)
        if title_len < 20:
            issues.append(Issue(
                url=url, code='SHORT_TITLE', title=f'Title Tag Too Short ({title_len} chars)',
                severity='notice', category='on_page',
                details='Expand title to between 40-60 characters',
                explanation='Short titles fail to communicate sufficient topical context and miss opportunities to capture secondary search queries.',
                recommended_fix='Expand the title with target secondary keywords, product specifications, or brand qualifiers.'
            ))
        elif title_len > 70:
            issues.append(Issue(
                url=url, code='LONG_TITLE', title=f'Title Tag Too Long ({title_len} chars)',
                severity='notice', category='on_page',
                details='Shorten title to avoid truncation in Google SERPs (< 600px / ~60 chars)',
                explanation='Titles exceeding 60 characters or ~600px are frequently truncated with an ellipsis (...) in Google desktop and mobile SERPs.',
                recommended_fix='Front-load primary target keywords and keep total title length within 50 to 60 characters.'
            ))

    if not onpage.get('isMetaDescription'):
        issues.append(Issue(
            url=url, code='MISSING_META_DESC', title='Missing Meta Description',
            severity='warning', category='on_page',
            details='Add a compelling meta description (120-155 characters)',
            explanation='No meta description is specified. Search engines will auto-generate snippets from page body copy, often resulting in unappealing SERP snippets.',
            recommended_fix='Add <meta name="description" content="..."> with a clear call-to-action and primary keyword.'
        ))
    else:
        desc_len = onpage.get('metaDescriptionLength', 0)
        if desc_len < 70:
            issues.append(Issue(
                url=url, code='SHORT_META_DESC', title=f'Meta Description Too Short ({desc_len} chars)',
                severity='notice', category='on_page',
                details='Expand meta description to 120-155 characters',
                explanation='Short descriptions do not fully utilize the available snippet space in SERPs to persuade searchers to click.',
                recommended_fix='Elaborate on key product/service benefits, warranty, or unique value propositions.'
            ))
        elif desc_len > 165:
            issues.append(Issue(
                url=url, code='LONG_META_DESC', title=f'Meta Description Too Long ({desc_len} chars)',
                severity='notice', category='on_page',
                details='Trim meta description to under 160 characters',
                explanation='Meta descriptions over 160 characters risk getting truncated on mobile and desktop search results.',
                recommended_fix='Keep descriptions between 130 and 155 characters.'
            ))

    if onpage.get('hasMultipleTitleTags'):
        issues.append(Issue(
            url=url, code='MULTIPLE_TITLE_TAGS', title='Multiple <title> Tags in HTML',
            severity='warning', category='on_page',
            details='Retain only one <title> element inside <head>',
            explanation='Multiple <title> tags create ambiguity for search crawlers regarding which title to display in SERPs.',
            recommended_fix='Remove duplicate <title> tags and verify template rendering.'
        ))
    if onpage.get('hasMultipleMetaDescriptionTags'):
        issues.append(Issue(
            url=url, code='MULTIPLE_META_DESC_TAGS', title='Multiple Meta Description Tags',
            severity='notice', category='on_page',
            details='Retain only one meta description tag',
            explanation='Multiple meta descriptions can result in search engines choosing an arbitrary tag or ignoring both.',
            recommended_fix='Consolidate into a single authoritative meta description.'
        ))

    # 10. Headings Hierarchy
    h1_count = onpage.get('h1Count', 0)
    h2_count = onpage.get('h2Count', 0)
    h3_count = onpage.get('h3Count', 0)
    if h1_count == 0:
        issues.append(Issue(
            url=url, code='MISSING_H1', title='Missing Primary H1 Heading',
            severity='warning', category='on_page',
            details='Add exactly one <h1> element denoting page topic',
            explanation='The H1 tag is one of the strongest on-page semantic signals informing search engines and screen readers of the page core subject.',
            recommended_fix='Add an <h1> heading reflecting the primary product or article title near the top of the body content.'
        ))
    elif h1_count > 1:
        issues.append(Issue(
            url=url, code='MULTIPLE_H1', title=f'Multiple H1 Headings ({h1_count} found)',
            severity='notice', category='on_page',
            details='Use a single H1 and structure subtopics with H2-H4',
            explanation='Having multiple H1 tags can dilute topic clarity and disrupt heading hierarchy for accessibility tools.',
            recommended_fix='Reserve <h1> for the main page title. Convert subsidiary headings to <h2> and <h3>.'
        ))

    if h2_count == 0 and h3_count > 0:
        issues.append(Issue(
            url=url, code='HEADING_HIERARCHY_SKIP', title='Heading Hierarchy Skipped (H3 without H2)',
            severity='notice', category='on_page',
            details='Organize headings in logical hierarchy (H1 -> H2 -> H3)',
            explanation='The page jumps directly from H1 to H3 without an intermediate H2, breaking semantic document outline.',
            recommended_fix='Nest sub-sections under appropriate <h2> headings before introducing <h3> elements.'
        ))

    # 11. Image Optimization & Alt Text
    missing_alt_count = onpage.get('notOptimizedImagesCount', 0)
    if missing_alt_count > 0:
        issues.append(Issue(
            url=url, code='IMAGES_MISSING_ALT', title=f'{missing_alt_count} Images Missing Alt Text',
            severity='warning' if missing_alt_count > 3 else 'notice', category='content',
            details='Provide descriptive alt text for informative images',
            explanation=f'{missing_alt_count} images lack an alt attribute. Search engines rely on alt text for Image Search indexing, and screen readers require it for accessibility (WCAG 2.1).',
            recommended_fix='Add descriptive, keyword-relevant alt attributes to images (e.g. alt="Men\'s Waterproof Hiking Boots - Dark Brown"). Use alt="" only for decorative images.'
        ))

    # 12. Links & Anchor Issues
    broken_links = onpage.get('brokenLinksCount', 0)
    if broken_links > 0:
        issues.append(Issue(
            url=url, code='BROKEN_OUTGOING_LINKS', title=f'Page Has {broken_links} Broken Outgoing Links',
            severity='warning', category='links',
            details='Repair or remove broken links returning 4xx/5xx status',
            explanation='Broken links degrade user trust, halt crawler journeys, and waste crawl equity.',
            recommended_fix='Update the href attributes to working destination URLs or remove decommissioned link targets.'
        ))

    # HTTPS linking to HTTP
    try:
        from urllib.parse import urlparse
        if urlparse(url).scheme == 'https':
            http_links = [l for l in (onpage.get('internalLinks') or []) if l.startswith('http://')]
            if http_links:
                issues.append(Issue(
                    url=url, code='HTTPS_LINKS_TO_HTTP', title=f'{len(http_links)} Internal Links Point to Insecure HTTP',
                    severity='warning', category='security',
                    details='Update internal links to use https:// scheme',
                    explanation='Internal links pointing to http:// force unnecessary redirects and trigger insecure link warnings.',
                    recommended_fix='Update hardcoded internal links in templates and CMS database to use https:// or relative paths (/path).'
                ))
    except Exception:
        pass

    # 13. URL Structure
    try:
        from urllib.parse import urlparse
        pu = urlparse(url)
        path = pu.path or '/'
        if '//' in path:
            issues.append(Issue(
                url=url, code='DOUBLE_SLASH_URL', title='Double Slash in URL Path',
                severity='notice', category='technical',
                details='Normalize URL path to remove double slashes (//)',
                explanation='Double slashes can cause URL duplication and parsing errors in some web server routing engines.',
                recommended_fix='Clean up CMS routing patterns and canonicalize paths with clean single slashes.'
            ))
        if '%' in path:
            issues.append(Issue(
                url=url, code='URL_ENCODING', title='URL Contains Percent-Encoded Characters',
                severity='notice', category='technical',
                details='Use clean hyphens instead of encoded spaces or special characters',
                explanation='Percent-encoded characters (like %20 for spaces) reduce URL readability in search snippets and social shares.',
                recommended_fix='Use lowercase letters, numbers, and hyphens (-) exclusively in URL slugs.'
            ))
        if len(url) > 100:
            issues.append(Issue(
                url=url, code='LONG_URL', title=f'Excessively Long URL ({len(url)} chars)',
                severity='notice', category='technical',
                details='Shorten URL slug to improve readability and click-through',
                explanation='Long, complex URLs are less likely to be clicked, copied, or shared, and can get truncated in SERPs.',
                recommended_fix='Shorten category or product slugs to focus on 3-5 core descriptive keywords.'
            ))
    except Exception:
        pass

    # 14. Structured Data / Schema.org Validation
    sd_val = tech.get('structuredDataValidation') or {}
    if not tech.get('hasSchema') and not sd_val.get('has_schema'):
        issues.append(Issue(
            url=url, code='NO_SCHEMA', title='No Structured Data (Schema.org) Detected',
            severity='notice', category='technical',
            details='Add JSON-LD structured data to earn Google Rich Results',
            explanation='No Schema.org markup was found on this page. Structured data helps search engines understand entity types and display rich snippets (prices, ratings, FAQs).',
            recommended_fix='Add JSON-LD markup suited to the page type (e.g. Product, BreadcrumbList, Organization, or Article).'
        ))
    else:
        for sd_issue in sd_val.get('issues', []):
            issues.append(Issue(
                url=url,
                code=f"SCHEMA_{sd_issue.get('schema_type', 'GENERAL').upper().replace('/', '_')}_{sd_issue.get('field', 'ERR').upper()}",
                title=f"Schema Issue: {sd_issue.get('message')}",
                severity=sd_issue.get('severity', 'warning'),
                category='technical',
                details=sd_issue.get('fix', 'Correct structured data markup.'),
                explanation=sd_issue.get('message', 'Structured data error prevents rich results in search engine results.'),
                recommended_fix=sd_issue.get('fix', 'Correct JSON-LD Schema markup according to Schema.org standards.')
            ))

    # 15. Content Word Count
    words = onpage.get('wordsCount')
    if isinstance(words, int) and words < 250:
        issues.append(Issue(
            url=url, code='THIN_CONTENT', title=f'Thin Content Detected ({words} words)',
            severity='warning' if words < 100 else 'notice', category='content',
            details='Expand substantive content to provide valuable information',
            explanation='Pages with very low word count risk being classified as "thin content" under Google Search Essentials guidelines, making them difficult to rank.',
            recommended_fix='Add detailed product descriptions, FAQs, customer use cases, or buying guides to satisfy user search intent.'
        ))

    # 16. E-Commerce Specific Issues
    if ecom:
        for ec_issue in ecom.get('issues', []):
            issues.append(Issue(
                url=url,
                code=ec_issue.get('code', 'ECOM_GENERIC'),
                title=ec_issue.get('title', 'E-commerce SEO Issue'),
                severity=ec_issue.get('severity', 'warning'),
                category='ecommerce',
                details=ec_issue.get('recommended_fix', ''),
                explanation=ec_issue.get('explanation', ''),
                recommended_fix=ec_issue.get('recommended_fix', '')
            ))

    # 17. AI Directives
    if tech.get('llmsTxtStatus') not in ('found', 'ok'):
        issues.append(Issue(
            url=url, code='NO_LLM_TXT', title='No llms.txt or ai.txt Directive Found',
            severity='notice', category='ai',
            details='Consider adding /llms.txt for AI agents and LLM scrapers',
            explanation='Neither /llms.txt nor /ai.txt were discovered. While optional, emerging AI search engines (like Perplexity and ChatGPT) use llms.txt to efficiently ingest clean markdown.',
            recommended_fix='Create a /llms.txt file on your root domain summarizing brand information and clean links for LLM ingest.'
        ))

    return issues


def derive_site_issues(pages: List[Dict[str, Any]], nodes: Dict[str, Dict[str, int]], edges: List[Dict[str, Any]], sitemap_report: Optional[Dict[str, Any]] = None) -> List[Issue]:
    issues: List[Issue] = []
    url_set = {p.get('url') for p in pages}

    # Orphan pages: no inbound internal links
    for u, deg in nodes.items():
        if deg.get('in', 0) == 0:
            issues.append(Issue(
                url=u, code='ORPHAN_PAGE', title='Orphan Page (Zero Inbound Internal Links)',
                severity='warning', category='links',
                details='Add contextual internal links from parent categories or relevant articles',
                explanation='Orphan pages cannot be reached through the internal site navigation. Crawlers discover them only through sitemaps or external links, and they receive zero PageRank equity.',
                recommended_fix='Link to this page from related category pages, top-level navigation, or relevant blog posts with descriptive anchor text.'
            ))

    # Nofollow-only inbound
    inbound_map: Dict[str, List[List[str]]] = {u: [] for u in url_set}
    for e in edges:
        tgt = e.get('target')
        rel = e.get('rel') or []
        if tgt in inbound_map:
            inbound_map[tgt].append(rel)
    for u, rel_lists in inbound_map.items():
        if not rel_lists:
            continue
        any_dofollow = any(('nofollow' not in (rl or [])) for rl in rel_lists)
        any_nofollow = any(('nofollow' in (rl or [])) for rl in rel_lists)
        if not any_dofollow and any_nofollow:
            issues.append(Issue(
                url=u, code='NOFOLLOW_ONLY_INBOUND', title='Internal Page Receives Only Nofollow Links',
                severity='notice', category='links',
                details='Remove rel="nofollow" on internal navigation links',
                explanation='Internal links should pass equity (PageRank) throughout your website. Nofollow on internal links unnecessarily blocks authority transfer.',
                recommended_fix='Remove rel="nofollow" from internal links pointing to this indexable page.'
            ))

    # Duplicate content without canonical
    text_hash_to_urls: Dict[str, List[str]] = {}
    canonical_map: Dict[str, Optional[str]] = {}
    for p in pages:
        u = p.get('url')
        ona = p.get('seo_attributes', {}).get('OnPageAnalyzer', {})
        tech = p.get('seo_attributes', {}).get('TechnicalSEOAnalyzer', {})
        canonical_map[u] = tech.get('canonicalUrl')
        h = ona.get('visibleTextHash')
        if h:
            text_hash_to_urls.setdefault(h, []).append(u)

    for h, group in text_hash_to_urls.items():
        if len(group) > 1:
            for u in group:
                can = canonical_map.get(u)
                if not can:
                    issues.append(Issue(
                        url=u, code='DUPLICATE_NO_CANONICAL', title=f'Identical Duplicate Content Across {len(group)} Pages (No Canonical)',
                        severity='warning', category='technical',
                        details='Add rel="canonical" pointing to the master version or differentiate content',
                        explanation=f'This page shares identical text content with {len(group)-1} other crawled URLs, but neither page designates a canonical tag.',
                        recommended_fix='Choose one master URL and add a canonical link tag to all duplicate variants pointing to the master URL.'
                    ))

    # Sitemap issues
    if sitemap_report and sitemap_report.get('sitemapUrls'):
        buckets = sitemap_report.get('statusBuckets', {})
        for key, lst in buckets.items():
            if not lst:
                continue
            sev = 'error' if any(x in key for x in ['4xx', '5xx', 'forbidden', 'timeout']) else 'warning'
            title = f"Sitemap Contains Non-200 URLs: {key.replace('_', ' ').title()}"
            for u in lst[:30]:
                issues.append(Issue(
                    url=u, code=f'SITEMAP_{key.upper()}', title=title,
                    severity=sev, category='technical',
                    details=f'Remove or fix URL {u} inside XML sitemap',
                    explanation=f'The XML sitemap lists this URL, but when requested it returned status {key}. Sitemaps should only include clean 200 OK indexable URLs.',
                    recommended_fix='Regenerate your XML sitemap to exclude non-200 or redirected URLs.'
                ))

    return issues
