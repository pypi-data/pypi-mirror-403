# sectra

Shodan-style CLI for the SecurityTrails API.

`sectra` is a lightweight, command-line client for SecurityTrails. It is built for quick lookups and scripting, with JSON output and optional response caching to save quota.

## Features

- Shodan-style CLI for common SecurityTrails endpoints
- JSON or pretty output
- Optional on-disk caching for GET requests
- Generic request passthrough for any endpoint

## Install

```bash
pip install sectra
```

## Authentication

Set your API key in the environment:

```bash
export SECURITYTRAILS=YOUR_KEY
```

Or persist it in a config file:

```bash
sectra init --key YOUR_KEY
```

## Usage

```bash
sectra --help
sectra ping
sectra usage
sectra domain example.com
sectra subdomains example.com
sectra whois example.com
sectra history-dns example.com A
sectra ip-whois 8.8.8.8
```

## Search

```bash
sectra domains-search --query "ns = 'ns1.yahoo.com'"
sectra domains-stats --query "ns = 'ns1.yahoo.com'"
sectra ips-search --query "ip:8.8.8.0/24"
sectra ips-stats --query "ip:8.8.8.0/24"
sectra sql-query --query "select * from domains where apex_domain = 'example.com' limit 5"
```

## ASI / V2 APIs

```bash
sectra projects
sectra assets-search PROJECT_ID --data '{"query":{"match_all":{}}}'
sectra assets-find PROJECT_ID --params '{"size":10}'
sectra asset PROJECT_ID ASSET_ID
sectra asset-exposures PROJECT_ID ASSET_ID
sectra asset-filters PROJECT_ID
sectra asset-tag-apply PROJECT_ID ASSET_ID critical
sectra asset-tag-remove PROJECT_ID ASSET_ID critical
sectra asset-tags-bulk PROJECT_ID ASSET_ID --data '{"tags":["critical","prod"]}'
sectra project-tags PROJECT_ID
sectra tag-task PROJECT_ID TASK_ID
sectra tags-bulk-assets PROJECT_ID --data '{"tags":["prod"],"asset_ids":["id1","id2"]}'
sectra exposures PROJECT_ID
sectra exposure-assets PROJECT_ID SIGNATURE_ID
sectra static-assets PROJECT_ID
sectra static-assets-bulk PROJECT_ID --data '{"assets":[{"asset_id":"id1","fields":{"note":"owned"}}]}'
sectra company-associated-ips example.com
sectra action-report PROJECT_ID report_type
sectra asi-risks PROJECT_ID
sectra asi-risks-history PROJECT_ID --params '{"page":1}'
```

## Caching

By default, GET responses are cached on disk to reduce repeated API usage.

```bash
sectra --cache-ttl 3600 domain example.com
sectra --no-cache domain example.com
```

Cache location: `~/.cache/sectra` (or `XDG_CACHE_HOME`).

## Output formats

```bash
sectra --output pretty domain example.com
sectra --output json domain example.com
sectra --output raw domain example.com
```

## Generic request

```bash
sectra request GET /domain/example.com
sectra request POST /domains/list --data '{"query":"ns = \'ns1.yahoo.com\'"}'
```

## Configuration

- Config: `~/.config/sectra/config.json` (or `XDG_CONFIG_HOME`)
- Cache: `~/.cache/sectra` (or `XDG_CACHE_HOME`)

## Development

```bash
pip install -e .
sectra --help
```

## License

MIT
