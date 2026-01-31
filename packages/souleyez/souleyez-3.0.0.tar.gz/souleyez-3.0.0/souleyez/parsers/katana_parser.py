#!/usr/bin/env python3
"""
souleyez.parsers.katana_parser - Parse Katana JSONL output

Katana is a web crawler from ProjectDiscovery that discovers endpoints,
parameters, and JavaScript-rendered routes.
"""
import json
from typing import Dict, Any, List, Set
from urllib.parse import urlparse, parse_qs

# LFI-suspicious parameter names - these typically include files, not query databases
LFI_PARAM_NAMES = {
    # Direct file inclusion params
    "page",
    "file",
    "include",
    "inc",
    "path",
    "filepath",
    "filename",
    "template",
    "tmpl",
    "tpl",
    "view",
    "layout",
    "content",
    # Document/resource params
    "doc",
    "document",
    "pdf",
    "folder",
    "root",
    "directory",
    "dir",
    # Language/locale (often load language files)
    "lang",
    "language",
    "locale",
    "loc",
    # Style/theme (often load CSS/template files)
    "style",
    "stylesheet",
    "css",
    "theme",
    "skin",
    # Config/module loading
    "config",
    "conf",
    "cfg",
    "module",
    "mod",
    "plugin",
    # Read/load operations
    "read",
    "load",
    "fetch",
    "get",
    "show",
    "display",
    "render",
    # PHP-specific
    "pg",
    "p",
    "cont",
    "controller",
    "action",
    "act",
    # Common variations
    "pagename",
    "page_name",
    "pageid",
    "site",
    "section",
}


def parse_katana_output(log_path: str) -> Dict[str, Any]:
    """
    Parse Katana JSONL output (one JSON object per line).

    Args:
        log_path: Path to katana output file

    Returns:
        Dict containing:
            - urls: List of all discovered URLs
            - urls_with_params: List of URLs containing query parameters
            - lfi_candidate_urls: URLs with LFI-suspicious params (page, file, include, etc.)
            - sqli_candidate_urls: URLs with non-LFI params (id, q, search, etc.)
            - forms_found: List of POST endpoint URLs
            - js_endpoints: List of JavaScript-discovered endpoints
            - unique_parameters: Set of unique parameter names found
            - lfi_params_found: Set of LFI parameter names found
            - methods: Dict of method counts (GET, POST, etc.)
    """
    urls: List[str] = []
    urls_with_params: List[str] = []
    lfi_candidate_urls: List[str] = []  # URLs with LFI-suspicious params only
    sqli_candidate_urls: List[str] = []  # URLs with non-LFI params
    forms_found: List[str] = []
    js_endpoints: List[str] = []
    unique_parameters: Set[str] = set()
    lfi_params_found: Set[str] = set()  # Track which LFI params we found
    methods: Dict[str, int] = {"GET": 0, "POST": 0, "PUT": 0, "DELETE": 0, "OTHER": 0}
    status_codes: Dict[int, int] = {}
    sources: Dict[str, int] = {}

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                # Skip comment lines and metadata
                if line.startswith("#") or line.startswith("==="):
                    continue

                line = line.strip()
                if not line:
                    continue

                try:
                    result = json.loads(line)

                    # Katana output format can vary by version
                    # Try multiple field locations
                    url = None
                    method = "GET"
                    status_code = None
                    source = None

                    # Format 1: request.endpoint structure
                    if "request" in result:
                        req = result["request"]
                        url = req.get("endpoint") or req.get("url")
                        method = req.get("method", "GET").upper()
                        if "response" in result:
                            status_code = result["response"].get("status_code")

                    # Format 2: Direct fields
                    if not url:
                        url = result.get("endpoint") or result.get("url")
                        method = result.get("method", "GET").upper()
                        status_code = result.get("status_code") or result.get("status")

                    # Get source (how endpoint was discovered)
                    source = result.get("source") or result.get("tag") or "unknown"

                    if not url:
                        continue

                    # Track all URLs
                    if url not in urls:
                        urls.append(url)

                    # Track methods
                    if method in methods:
                        methods[method] += 1
                    else:
                        methods["OTHER"] += 1

                    # Track status codes
                    if status_code:
                        status_codes[status_code] = status_codes.get(status_code, 0) + 1

                    # Track sources
                    sources[source] = sources.get(source, 0) + 1

                    # Check for query parameters
                    parsed = urlparse(url)
                    if parsed.query:
                        if url not in urls_with_params:
                            urls_with_params.append(url)

                        # Extract parameter names and categorize
                        # Use keep_blank_values=True to detect params like ?q= (empty value)
                        params = parse_qs(parsed.query, keep_blank_values=True)
                        param_names = set(params.keys())
                        unique_parameters.update(param_names)

                        # Check if params are LFI-suspicious
                        lfi_params_in_url = param_names & LFI_PARAM_NAMES
                        non_lfi_params = param_names - LFI_PARAM_NAMES

                        if lfi_params_in_url:
                            lfi_params_found.update(lfi_params_in_url)

                        # Categorize URL based on params
                        if lfi_params_in_url and not non_lfi_params:
                            # ALL params are LFI-suspicious → LFI candidate only
                            if url not in lfi_candidate_urls:
                                lfi_candidate_urls.append(url)
                        elif non_lfi_params:
                            # Has non-LFI params → SQLi candidate
                            if url not in sqli_candidate_urls:
                                sqli_candidate_urls.append(url)
                            # Also add to LFI if it has LFI params (mixed)
                            if lfi_params_in_url and url not in lfi_candidate_urls:
                                lfi_candidate_urls.append(url)

                    # Track POST endpoints as forms
                    if method == "POST":
                        if url not in forms_found:
                            forms_found.append(url)

                    # Track JavaScript-discovered endpoints
                    if source in ("js", "script", "javascript", "jscrawl"):
                        if url not in js_endpoints:
                            js_endpoints.append(url)

                except json.JSONDecodeError:
                    # Skip non-JSON lines (like metadata headers)
                    continue

    except FileNotFoundError:
        return {
            "urls": [],
            "urls_with_params": [],
            "lfi_candidate_urls": [],
            "sqli_candidate_urls": [],
            "forms_found": [],
            "js_endpoints": [],
            "unique_parameters": [],
            "lfi_params_found": [],
            "methods": methods,
            "status_codes": {},
            "sources": {},
            "error": f"Log file not found: {log_path}",
        }
    except Exception as e:
        return {
            "urls": [],
            "urls_with_params": [],
            "lfi_candidate_urls": [],
            "sqli_candidate_urls": [],
            "forms_found": [],
            "js_endpoints": [],
            "unique_parameters": [],
            "lfi_params_found": [],
            "methods": methods,
            "status_codes": {},
            "sources": {},
            "error": str(e),
        }

    return {
        "urls": urls,
        "urls_with_params": urls_with_params,
        "lfi_candidate_urls": lfi_candidate_urls,
        "sqli_candidate_urls": sqli_candidate_urls,
        "forms_found": forms_found,
        "js_endpoints": js_endpoints,
        "unique_parameters": sorted(list(unique_parameters)),
        "lfi_params_found": sorted(list(lfi_params_found)),
        "methods": methods,
        "status_codes": status_codes,
        "sources": sources,
    }


def extract_injectable_urls(parsed_data: Dict[str, Any]) -> List[str]:
    """
    Extract URLs that are good candidates for SQL injection testing.

    Only returns URLs with non-LFI parameters. URLs with only LFI-suspicious
    params (page, file, include, etc.) are excluded since SQLMap won't find
    LFI vulnerabilities.

    Prioritizes:
    1. URLs with non-LFI query parameters (sqli_candidate_urls)
    2. POST form endpoints
    3. JavaScript-discovered API endpoints

    Args:
        parsed_data: Output from parse_katana_output()

    Returns:
        List of URLs suitable for SQLMap/SQL injection testing
    """
    injectable = []

    # SQLi candidate URLs (have non-LFI params)
    for url in parsed_data.get("sqli_candidate_urls", []):
        if url not in injectable:
            injectable.append(url)

    # POST forms are also injectable, but skip LFI-only forms
    lfi_candidates = parsed_data.get("lfi_candidate_urls", [])
    sqli_candidates = parsed_data.get("sqli_candidate_urls", [])
    for url in parsed_data.get("forms_found", []):
        if url not in injectable:
            # Skip forms that only have LFI params (no SQLi potential)
            if url in lfi_candidates and url not in sqli_candidates:
                continue
            injectable.append(url)

    # JS endpoints might have hidden params
    for url in parsed_data.get("js_endpoints", []):
        if url not in injectable:
            injectable.append(url)

    return injectable


def extract_lfi_urls(parsed_data: Dict[str, Any]) -> List[str]:
    """
    Extract URLs that are good candidates for LFI (Local File Inclusion) testing.

    Returns URLs with LFI-suspicious parameters like page, file, include, path,
    template, etc. These should be tested with LFI payloads, not SQLMap.

    Args:
        parsed_data: Output from parse_katana_output()

    Returns:
        List of URLs suitable for LFI testing
    """
    return parsed_data.get("lfi_candidate_urls", [])
