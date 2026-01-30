import json
import os
import sys
from typing import Any, Optional

import click

from .api import DEFAULT_BASE_URL, SecurityTrailsError, _parse_json, request
from .cache import load_cached, save_cached
from .config import CACHE_DIR, load_config, save_config


class Context:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout: int,
        output: str,
        fail: bool,
        cache: bool,
        cache_ttl: int,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.output = output
        self.fail = fail
        self.cache = cache
        self.cache_ttl = cache_ttl


V2_BASE_URL = "https://api.securitytrails.com/v2"


def _resolve_key(cli_key: Optional[str]) -> Optional[str]:
    if cli_key:
        return cli_key
    env_key = os.getenv("SECURITYTRAILS")
    if env_key:
        return env_key
    cfg = load_config()
    return cfg.get("api_key")


def _print_response(resp, output: str) -> None:
    if output == "raw":
        sys.stdout.write(resp.text)
        if not resp.text.endswith("\n"):
            sys.stdout.write("\n")
        return
    try:
        data = resp.json()
    except ValueError:
        sys.stdout.write(resp.text)
        if not resp.text.endswith("\n"):
            sys.stdout.write("\n")
        return
    if output == "json":
        sys.stdout.write(json.dumps(data))
        sys.stdout.write("\n")
        return
    sys.stdout.write(json.dumps(data, indent=2, sort_keys=True))
    sys.stdout.write("\n")


@click.group()
@click.option("--key", "api_key", help="SecurityTrails API key (overrides env/config)")
@click.option("--base-url", default=DEFAULT_BASE_URL, show_default=True)
@click.option("--timeout", default=30, show_default=True, type=int)
@click.option("--output", type=click.Choice(["pretty", "json", "raw"]), default="pretty")
@click.option("--fail", is_flag=True, help="Exit non-zero on non-2xx responses")
@click.option("--cache/--no-cache", default=True, show_default=True, help="Enable response caching")
@click.option("--cache-ttl", default=3600, show_default=True, type=int, help="Cache TTL in seconds")
@click.pass_context
def cli(ctx, api_key, base_url, timeout, output, fail, cache, cache_ttl):
    """Shodan-style CLI for the SecurityTrails API."""
    resolved = _resolve_key(api_key)
    if not resolved:
        click.echo("Missing API key. Set SECURITYTRAILS or run 'sectra init --key ...'", err=True)
        ctx.exit(2)
    ctx.obj = Context(resolved, base_url, timeout, output, fail, cache, cache_ttl)


@cli.command()
@click.option("--key", "api_key", required=True, help="SecurityTrails API key")
def init(api_key):
    """Persist API key to config file."""
    save_config({"api_key": api_key})
    click.echo("Saved API key to config.")


def _fetch(ctx: Context, method: str, path: str, params: Optional[str], data: Optional[str]):
    try:
        params_obj = _parse_json(params)
        data_obj = _parse_json(data)
        if ctx.cache and method.upper() == "GET":
            url = path if path.startswith("http://") or path.startswith("https://") else ctx.base_url.rstrip("/") + (path if path.startswith("/") else f"/{path}")
            cached = load_cached(method, url, params_obj, data_obj, ctx.cache_ttl)
            if cached is not None:
                return _CachedResponse(cached), cached
        resp = request(
            method=method,
            path=path,
            api_key=ctx.api_key,
            base_url=ctx.base_url,
            params=params_obj,
            data=data_obj,
            timeout=ctx.timeout,
        )
        data_json = None
        try:
            data_json = resp.json()
        except ValueError:
            data_json = None
    except SecurityTrailsError as exc:
        click.echo(str(exc), err=True)
        sys.exit(2)
    if ctx.cache and method.upper() == "GET" and resp.ok:
        if isinstance(data_json, dict):
            url = path if path.startswith("http://") or path.startswith("https://") else ctx.base_url.rstrip("/") + (path if path.startswith("/") else f"/{path}")
            save_cached(method, url, params_obj, data_obj, data_json)
    return resp, data_json


def _do_request(ctx: Context, method: str, path: str, params: Optional[str], data: Optional[str]):
    resp, _ = _fetch(ctx, method, path, params, data)
    _print_response(resp, ctx.output)
    if ctx.fail and not resp.ok:
        sys.exit(1)


def _extract_scroll_id(data: Any) -> Optional[str]:
    if isinstance(data, dict):
        scroll_id = data.get("scroll_id") or data.get("id")
        if isinstance(scroll_id, str):
            return scroll_id
    return None


def _paginate(ctx: Context, first_resp, first_data: Any, scroll_path_prefix: str, pages: Optional[int]):
    page = 1
    if ctx.fail and not first_resp.ok:
        sys.exit(1)
    while True:
        scroll_id = _extract_scroll_id(first_data)
        if not scroll_id:
            return
        if pages is not None and page >= pages:
            return
        resp, data = _fetch(ctx, "GET", f"{scroll_path_prefix}/{scroll_id}", None, None)
        _print_response(resp, ctx.output)
        if ctx.fail and not resp.ok:
            sys.exit(1)
        first_data = data
        page += 1


def _paginate_collect(
    ctx: Context, first_resp, first_data: Any, scroll_path_prefix: str, pages: Optional[int]
) -> list:
    collected = []
    if isinstance(first_data, dict):
        collected.append(first_data)
    page = 1
    if ctx.fail and not first_resp.ok:
        sys.exit(1)
    while True:
        scroll_id = _extract_scroll_id(first_data)
        if not scroll_id:
            return collected
        if pages is not None and page >= pages:
            return collected
        resp, data = _fetch(ctx, "GET", f"{scroll_path_prefix}/{scroll_id}", None, None)
        if ctx.fail and not resp.ok:
            sys.exit(1)
        if isinstance(data, dict):
            collected.append(data)
        first_data = data
        page += 1


class _CachedResponse:
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self.text = json.dumps(data)
        self.ok = True

    def json(self):
        return self._data


@cli.command("request")
@click.argument("method")
@click.argument("path")
@click.option("--params", help="Query params as JSON")
@click.option("--data", help="Request body as JSON")
@click.pass_obj
def request_cmd(ctx: Context, method, path, params, data):
    """Make an arbitrary API request."""
    _do_request(ctx, method, path, params, data)


@cli.command()
@click.pass_obj
def ping(ctx: Context):
    """Check API availability."""
    _do_request(ctx, "GET", "/ping", None, None)


@cli.command()
@click.pass_obj
def usage(ctx: Context):
    """Account usage and quota."""
    _do_request(ctx, "GET", "/account/usage", None, None)


@cli.command()
@click.argument("hostname")
@click.pass_obj
def domain(ctx: Context, hostname):
    """Domain details."""
    _do_request(ctx, "GET", f"/domain/{hostname}", None, None)


@cli.command()
@click.argument("hostname")
@click.option("--params", help="Query params as JSON")
@click.pass_obj
def subdomains(ctx: Context, hostname, params):
    """Domain subdomains."""
    _do_request(ctx, "GET", f"/domain/{hostname}/subdomains", params, None)


@cli.command()
@click.argument("hostname")
@click.pass_obj
def tags(ctx: Context, hostname):
    """Domain tags."""
    _do_request(ctx, "GET", f"/domain/{hostname}/tags", None, None)


@cli.command()
@click.argument("hostname")
@click.pass_obj
def whois(ctx: Context, hostname):
    """Domain WHOIS."""
    _do_request(ctx, "GET", f"/domain/{hostname}/whois", None, None)


@cli.command("history-whois")
@click.argument("hostname")
@click.pass_obj
def history_whois(ctx: Context, hostname):
    """Historical WHOIS."""
    _do_request(ctx, "GET", f"/history/{hostname}/whois", None, None)


@cli.command("history-dns")
@click.argument("hostname")
@click.argument("record_type")
@click.pass_obj
def history_dns(ctx: Context, hostname, record_type):
    """Historical DNS records by type (A, AAAA, MX, NS, TXT, SOA, CNAME, ...)."""
    _do_request(ctx, "GET", f"/history/{hostname}/dns/{record_type}", None, None)


@cli.command()
@click.argument("hostname")
@click.pass_obj
def associated(ctx: Context, hostname):
    """Associated domains."""
    _do_request(ctx, "GET", f"/domain/{hostname}/associated", None, None)


@cli.command()
@click.argument("hostname")
@click.pass_obj
def ssl(ctx: Context, hostname):
    """Domain SSL metadata."""
    _do_request(ctx, "GET", f"/domain/{hostname}/ssl", None, None)


@cli.command("ip-nearby")
@click.argument("ipaddress")
@click.pass_obj
def ip_nearby(ctx: Context, ipaddress):
    """Nearby IPs."""
    _do_request(ctx, "GET", f"/ips/nearby/{ipaddress}", None, None)


@cli.command("ip-whois")
@click.argument("ipaddress")
@click.pass_obj
def ip_whois(ctx: Context, ipaddress):
    """IP WHOIS."""
    _do_request(ctx, "GET", f"/ips/{ipaddress}/whois", None, None)


@cli.command("ip-useragents")
@click.argument("ipaddress")
@click.pass_obj
def ip_useragents(ctx: Context, ipaddress):
    """IP user agents."""
    _do_request(ctx, "GET", f"/ips/{ipaddress}/useragents", None, None)


@cli.command("domains-search")
@click.option("--query", help="DSL query string")
@click.option("--data", "data_json", help="Raw JSON body (overrides --query)")
@click.option("--params", help="Query params as JSON")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages using scroll")
@click.option("--pages", type=int, help="Fetch N pages using scroll")
@click.option("--aggregate", is_flag=True, help="Combine pages into one JSON response")
@click.pass_obj
def domains_search(ctx: Context, query, data_json, params, fetch_all, pages, aggregate):
    """Search domains (POST /domains/list)."""
    if not data_json and not query:
        raise click.UsageError("Provide --query or --data")
    body = data_json or json.dumps({"query": query})
    resp, data = _fetch(ctx, "POST", "/domains/list", params, body)
    if aggregate and (fetch_all or (pages and pages > 1)):
        pages_data = _paginate_collect(ctx, resp, data, "/scroll", None if fetch_all else pages)
        _print_response(_CachedResponse({"pages": pages_data}), ctx.output)
        return
    _print_response(resp, ctx.output)
    if fetch_all:
        _paginate(ctx, resp, data, "/scroll", None)
    elif pages and pages > 1:
        _paginate(ctx, resp, data, "/scroll", pages)


@cli.command("domains-search-dsl")
@click.option("--query", required=True, help="DSL query string")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages using scroll")
@click.option("--pages", type=int, help="Fetch N pages using scroll")
@click.option("--aggregate", is_flag=True, help="Combine pages into one JSON response")
@click.pass_obj
def domains_search_dsl(ctx: Context, query, fetch_all, pages, aggregate):
    """Search domains (POST /domains/list-backup)."""
    resp, data = _fetch(ctx, "POST", "/domains/list-backup", None, json.dumps({"query": query}))
    if aggregate and (fetch_all or (pages and pages > 1)):
        pages_data = _paginate_collect(ctx, resp, data, "/scroll", None if fetch_all else pages)
        _print_response(_CachedResponse({"pages": pages_data}), ctx.output)
        return
    _print_response(resp, ctx.output)
    if fetch_all:
        _paginate(ctx, resp, data, "/scroll", None)
    elif pages and pages > 1:
        _paginate(ctx, resp, data, "/scroll", pages)


@cli.command("domains-stats")
@click.option("--query", help="DSL query string")
@click.option("--data", "data_json", help="Raw JSON body (overrides --query)")
@click.pass_obj
def domains_stats(ctx: Context, query, data_json):
    """Domain stats (POST /domains/stats)."""
    if not data_json and not query:
        raise click.UsageError("Provide --query or --data")
    body = data_json or json.dumps({"query": query})
    _do_request(ctx, "POST", "/domains/stats", None, body)


@cli.command("ips-search")
@click.option("--query", help="DSL query string")
@click.option("--data", "data_json", help="Raw JSON body (overrides --query)")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages using scroll")
@click.option("--pages", type=int, help="Fetch N pages using scroll")
@click.option("--aggregate", is_flag=True, help="Combine pages into one JSON response")
@click.pass_obj
def ips_search(ctx: Context, query, data_json, fetch_all, pages, aggregate):
    """Search IPs (POST /ips/list)."""
    if not data_json and not query:
        raise click.UsageError("Provide --query or --data")
    body = data_json or json.dumps({"query": query})
    resp, data = _fetch(ctx, "POST", "/ips/list", None, body)
    if aggregate and (fetch_all or (pages and pages > 1)):
        pages_data = _paginate_collect(ctx, resp, data, "/scroll", None if fetch_all else pages)
        _print_response(_CachedResponse({"pages": pages_data}), ctx.output)
        return
    _print_response(resp, ctx.output)
    if fetch_all:
        _paginate(ctx, resp, data, "/scroll", None)
    elif pages and pages > 1:
        _paginate(ctx, resp, data, "/scroll", pages)


@cli.command("ips-stats")
@click.option("--query", help="DSL query string")
@click.option("--data", "data_json", help="Raw JSON body (overrides --query)")
@click.pass_obj
def ips_stats(ctx: Context, query, data_json):
    """IP stats (POST /ips/stats)."""
    if not data_json and not query:
        raise click.UsageError("Provide --query or --data")
    body = data_json or json.dumps({"query": query})
    _do_request(ctx, "POST", "/ips/stats", None, body)


@cli.command()
@click.argument("scroll_id")
@click.pass_obj
def scroll(ctx: Context, scroll_id):
    """Scroll results by ID."""
    _do_request(ctx, "GET", f"/scroll/{scroll_id}", None, None)


@cli.command("sql-query")
@click.option("--query", help="SQL query string")
@click.option("--data", "data_json", help="Raw JSON body (overrides --query)")
@click.option("--params", help="Query params as JSON")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages using scroll")
@click.option("--pages", type=int, help="Fetch N pages using scroll")
@click.option("--aggregate", is_flag=True, help="Combine pages into one JSON response")
@click.pass_obj
def sql_query(ctx: Context, query, data_json, params, fetch_all, pages, aggregate):
    """SQL API query (POST /query/scroll)."""
    if not data_json and not query:
        raise click.UsageError("Provide --query or --data")
    body = data_json or json.dumps({"query": query})
    resp, data = _fetch(ctx, "POST", "/query/scroll", params, body)
    if aggregate and (fetch_all or (pages and pages > 1)):
        pages_data = _paginate_collect(ctx, resp, data, "/query/scroll", None if fetch_all else pages)
        _print_response(_CachedResponse({"pages": pages_data}), ctx.output)
        return
    _print_response(resp, ctx.output)
    if fetch_all:
        _paginate(ctx, resp, data, "/query/scroll", None)
    elif pages and pages > 1:
        _paginate(ctx, resp, data, "/query/scroll", pages)


@cli.command("sql-scroll")
@click.argument("scroll_id")
@click.pass_obj
def sql_scroll(ctx: Context, scroll_id):
    """SQL API scroll results by ID."""
    _do_request(ctx, "GET", f"/query/scroll/{scroll_id}", None, None)


@cli.command("feed-domains")
@click.argument("feed_type")
@click.pass_obj
def feed_domains(ctx: Context, feed_type):
    """Domain feeds."""
    _do_request(ctx, "GET", f"/feeds/domains/{feed_type}", None, None)


@cli.command("feed-subdomains")
@click.argument("feed_type")
@click.pass_obj
def feed_subdomains(ctx: Context, feed_type):
    """Subdomain feeds."""
    _do_request(ctx, "GET", f"/feeds/subdomains/{feed_type}", None, None)


@cli.command("action-report")
@click.argument("project_id")
@click.argument("report_type")
@click.pass_obj
def action_report(ctx: Context, project_id, report_type):
    """Action Center report."""
    _do_request(
        ctx,
        "GET",
        f"{V2_BASE_URL}/action_center/reports/{project_id}/{report_type}",
        None,
        None,
    )


@cli.command("projects")
@click.pass_obj
def projects(ctx: Context):
    """List ASI projects."""
    _do_request(ctx, "GET", f"{V2_BASE_URL}/projects", None, None)


@cli.command("assets-search")
@click.argument("project_id")
@click.option("--data", "data_json", required=True, help="Search body JSON")
@click.pass_obj
def assets_search(ctx: Context, project_id, data_json):
    """Search assets in a project."""
    _do_request(ctx, "POST", f"{V2_BASE_URL}/projects/{project_id}/assets/_search", None, data_json)


@cli.command("assets-find")
@click.argument("project_id")
@click.option("--params", required=True, help="Query params as JSON")
@click.pass_obj
def assets_find(ctx: Context, project_id, params):
    """Find assets in a project."""
    _do_request(ctx, "GET", f"{V2_BASE_URL}/projects/{project_id}/assets", params, None)


@cli.command("asset")
@click.argument("project_id")
@click.argument("asset_id")
@click.pass_obj
def asset(ctx: Context, project_id, asset_id):
    """Get asset by ID."""
    _do_request(ctx, "GET", f"{V2_BASE_URL}/projects/{project_id}/assets/{asset_id}", None, None)


@cli.command("asset-exposures")
@click.argument("project_id")
@click.argument("asset_id")
@click.pass_obj
def asset_exposures(ctx: Context, project_id, asset_id):
    """Get asset exposures."""
    _do_request(
        ctx, "GET", f"{V2_BASE_URL}/projects/{project_id}/assets/{asset_id}/exposures", None, None
    )


@cli.command("asset-filters")
@click.argument("project_id")
@click.option("--params", help="Query params as JSON")
@click.pass_obj
def asset_filters(ctx: Context, project_id, params):
    """Get asset filter options."""
    _do_request(ctx, "GET", f"{V2_BASE_URL}/projects/{project_id}/filters", params, None)


@cli.command("asset-tag-apply")
@click.argument("project_id")
@click.argument("asset_id")
@click.argument("tag_name")
@click.pass_obj
def asset_tag_apply(ctx: Context, project_id, asset_id, tag_name):
    """Apply tag to an asset."""
    _do_request(
        ctx,
        "PUT",
        f"{V2_BASE_URL}/projects/{project_id}/assets/{asset_id}/tags/{tag_name}",
        None,
        None,
    )


@cli.command("asset-tag-remove")
@click.argument("project_id")
@click.argument("asset_id")
@click.argument("tag_name")
@click.pass_obj
def asset_tag_remove(ctx: Context, project_id, asset_id, tag_name):
    """Remove tag from an asset."""
    _do_request(
        ctx,
        "DELETE",
        f"{V2_BASE_URL}/projects/{project_id}/assets/{asset_id}/tags/{tag_name}",
        None,
        None,
    )


@cli.command("asset-tags-bulk")
@click.argument("project_id")
@click.argument("asset_id")
@click.option("--data", "data_json", required=True, help="Bulk tags body JSON")
@click.pass_obj
def asset_tags_bulk(ctx: Context, project_id, asset_id, data_json):
    """Apply tags in bulk to an asset."""
    _do_request(
        ctx,
        "POST",
        f"{V2_BASE_URL}/projects/{project_id}/assets/{asset_id}/tags",
        None,
        data_json,
    )


@cli.command("project-tags")
@click.argument("project_id")
@click.pass_obj
def project_tags(ctx: Context, project_id):
    """Get tags for a project."""
    _do_request(ctx, "GET", f"{V2_BASE_URL}/projects/{project_id}/tags", None, None)


@cli.command("tag-task")
@click.argument("project_id")
@click.argument("task_id")
@click.pass_obj
def tag_task(ctx: Context, project_id, task_id):
    """Get bulk-tagging task status."""
    _do_request(
        ctx, "GET", f"{V2_BASE_URL}/projects/{project_id}/tags/_task_status/{task_id}", None, None
    )


@cli.command("tags-bulk-assets")
@click.argument("project_id")
@click.option("--data", "data_json", required=True, help="Bulk tag assets body JSON")
@click.pass_obj
def tags_bulk_assets(ctx: Context, project_id, data_json):
    """Bulk tag assets."""
    _do_request(ctx, "POST", f"{V2_BASE_URL}/projects/{project_id}/tags/_bulk_tag_assets", None, data_json)


@cli.command("exposures")
@click.argument("project_id")
@click.pass_obj
def exposures(ctx: Context, project_id):
    """Get exposures by project."""
    _do_request(ctx, "GET", f"{V2_BASE_URL}/projects/{project_id}/exposures", None, None)


@cli.command("exposure-assets")
@click.argument("project_id")
@click.argument("signature_id")
@click.pass_obj
def exposure_assets(ctx: Context, project_id, signature_id):
    """Get assets by exposure signature ID."""
    _do_request(ctx, "GET", f"{V2_BASE_URL}/projects/{project_id}/exposures/{signature_id}", None, None)


@cli.command("static-assets")
@click.argument("project_id")
@click.pass_obj
def static_assets(ctx: Context, project_id):
    """Get static assets."""
    _do_request(ctx, "GET", f"{V2_BASE_URL}/projects/{project_id}/rules/static_assets", None, None)


@cli.command("static-assets-bulk")
@click.argument("project_id")
@click.option("--data", "data_json", required=True, help="Bulk update body JSON")
@click.pass_obj
def static_assets_bulk(ctx: Context, project_id, data_json):
    """Bulk update static assets."""
    _do_request(ctx, "POST", f"{V2_BASE_URL}/projects/{project_id}/rules/_bulk_static_assets", None, data_json)


@cli.command("company-associated-ips")
@click.argument("domain")
@click.pass_obj
def company_associated_ips(ctx: Context, domain):
    """Get associated IPs for a company domain."""
    _do_request(ctx, "GET", f"{V2_BASE_URL}/company/{domain}/associated-ips", None, None)


@cli.command("asi-risks")
@click.argument("project_id")
@click.pass_obj
def asi_risks(ctx: Context, project_id):
    """Get most recent issues for a project."""
    _do_request(ctx, "GET", f"/asi/rules/{project_id}/recent/issues", None, None)


@cli.command("asi-risks-history")
@click.argument("project_id")
@click.option("--params", help="Query params as JSON")
@click.pass_obj
def asi_risks_history(ctx: Context, project_id, params):
    """Get historical issues for a project."""
    _do_request(ctx, "GET", f"/asi/rules/history/{project_id}/activity", params, None)


if __name__ == "__main__":
    cli()
