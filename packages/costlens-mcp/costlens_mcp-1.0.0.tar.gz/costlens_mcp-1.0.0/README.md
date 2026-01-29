# CostLens MCP

**FinOps MCP Server for BigQuery** — Cost estimation, query optimization, and safe execution.

## Installation

```bash
# Via pip
pip install costlens-mcp

# Via uvx (recommended)
uvx costlens-mcp --project YOUR_PROJECT
```

## Quick Start

```bash
# If you've run `gcloud auth application-default login`
costlens-mcp --project my-project

# With service account
costlens-mcp --project my-project --key-file /path/to/key.json

# Enable query execution (with cost limit)
costlens-mcp --project my-project --allow-execute --max-cost 5.0
```

## Tools

| Tool | Description |
|------|-------------|
| `estimate_query_cost` | Precise cost via BigQuery dry-run |
| `list_tables` | Tables with sizes |
| `describe_table` | Schema + partitions |
| `execute_query` | Cost-gated execution |
| `get_optimizations` | Structured suggestions |

## MCP Configuration

```json
{
  "mcpServers": {
    "costlens": {
      "command": "uvx",
      "args": ["costlens-mcp", "--project", "YOUR_PROJECT"]
    }
  }
}
```

## License

MIT
